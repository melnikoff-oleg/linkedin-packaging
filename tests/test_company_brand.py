"""Brand-specific font use and immutable, portable source bundles."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from linkedin_pack.company_brand import (
    load_brand, copy_brand_bundle, brand_record, audit_brand_typography, brand_styles, block_brand_network,
)
from linkedin_pack.core import ROOT, write_json, export_shareable
from linkedin_pack.reference_layout import reference_banner_html, registry
from linkedin_pack.render import measure_design_details
from scripts.build_example_pack import sha, current_brand_matches
from tests.test_example_export import released_examples, hashes


def brand_fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'fonts').mkdir(exist_ok=True)
    font = root / 'fonts/brand.ttf'
    font.write_bytes((ROOT / 'assets/fonts/Inter.ttf').read_bytes())
    write_json(root / 'brand.json', {
        'schema_version': 1, 'id': 'example-company', 'name': 'Example Company',
        'website': 'https://example.com/', 'palette': {'ink': '#123456', 'paper': '#ffffff'},
        'fonts': [{'family': 'Example Brand', 'path': 'fonts/brand.ttf', 'sha256': sha(font),
                   'weight': '100 900', 'style': 'normal', 'source_url': 'https://example.com/brand.ttf'}],
        'typography': {'display_family': 'Example Brand', 'body_family': 'Example Brand'},
        'stylesheet': 'brand.css', 'provenance': 'provenance.json',
    })
    (root / 'brand.css').write_text('.banner{color:#123456!important}')
    write_json(root / 'provenance.json', {'website': 'https://example.com/'})
    return root / 'brand.json'


class CompanyBrandTests(unittest.TestCase):
    def test_offline_browser_blocks_remote_assets_before_network_access(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            blocked, failed = [], []
            block_brand_network(page.context, blocked)
            page.on('requestfailed', lambda request: failed.append(request.failure))
            page.set_content('<div class="banner"><img src="https://example.invalid/unbound.png"></div>')
            self.assertEqual(blocked, ['https://example.invalid/unbound.png'])
            self.assertEqual(len(failed), 1)
            self.assertTrue(failed[0].startswith('net::ERR_BLOCKED_BY_CLIENT'), failed)
            browser.close()

    def test_all_unbound_css_asset_syntax_is_rejected(self):
        declarations = (
            r'background-image:u\72l(https://example.com/a.png)',
            r'background-image:\75 rl(../outside.png)',
            'background-image:u/**/rl(../outside.png)',
            'background-image:image-set("relative.png" 1x)',
            'background-image:-webkit-image-set("https://example.com/a.png" 1x)',
            'background-image:image("https://example.com/a.png")',
            'background-image:src("relative.png")',
            'background-image:IMAGE-SET("relative.png" 1x)',
            r'@im\70ort "https://example.com/outside.css";',
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest = brand_fixture(root / 'brand')
            stylesheet = manifest.parent / 'brand.css'
            for declaration in declarations:
                with self.subTest(declaration=declaration):
                    stylesheet.write_text('.banner{' + declaration + '}')
                    with self.assertRaisesRegex(ValueError, 'stylesheet'):
                        load_brand(root, {'manifest': 'brand/brand.json'})
            stylesheet.write_text('.banner{background:linear-gradient(90deg,#fff,#000);color:var(--ink);filter:grayscale(1) contrast(.9)}')
            load_brand(root, {'manifest': 'brand/brand.json'})

    def test_loaded_regular_face_cannot_mask_failed_bold_or_italic_face(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as temp, sync_playwright() as playwright:
            root = Path(temp); manifest = brand_fixture(root / 'brand')
            browser = playwright.chromium.launch()
            try:
                for weight, style in (('700', 'normal'), ('400', 'italic')):
                    with self.subTest(weight=weight, style=style):
                        data = json.loads(manifest.read_text())
                        data['fonts'] = [data['fonts'][0]]
                        data['fonts'][0]['weight'] = '400'
                        damaged = manifest.parent / 'fonts/damaged.ttf'
                        damaged.write_bytes(b'\x00\x01\x00\x00invalid font but matching declared hash')
                        data['fonts'].append({'family': 'Example Brand', 'path': 'fonts/damaged.ttf',
                            'sha256': sha(damaged), 'weight': weight, 'style': style,
                            'source_url': 'https://example.com/damaged.ttf'})
                        write_json(manifest, data)
                        # The file hash and font signature alone cannot prove
                        # the browser can decode the particular requested face.
                        data, _ = load_brand(root, {'manifest': 'brand/brand.json'})
                        fonts, css = brand_styles(root, {'manifest': 'brand/brand.json'})
                        page = browser.new_page()
                        page.set_content(f'<style>{fonts}{css}</style><div class="banner"><p style="font-weight:400;font-style:normal">Regular</p><p style="font-weight:{weight};font-style:{style}">Damaged face</p></div>')
                        page.evaluate('document.fonts.ready')
                        audit = audit_brand_typography(page, data, measure_design_details(page))
                        self.assertEqual(audit['status'], 'failed', audit)
                        self.assertTrue(any(face['weight'] == '400' and face['style'] == 'normal' and face['loaded'] for face in audit['font_faces']))
                        failed = next(face for face in audit['used_faces'] if face['weight'] == weight and face['style'] == style)
                        self.assertFalse(failed['loaded'])
                        self.assertTrue(any(f'weight {weight} style {style}' in failure for failure in audit['failures']))
                        page.close()
            finally:
                browser.close()

    def test_bundle_rejects_changed_fonts_traversal_and_network_css(self):
        for mutation in ('font', 'traversal', 'network_css'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); manifest = brand_fixture(root / 'brand')
                data = json.loads(manifest.read_text())
                if mutation == 'font':
                    (manifest.parent / 'fonts/brand.ttf').write_bytes(b'\x00\x01\x00\x00changed font')
                elif mutation == 'traversal':
                    data['fonts'][0]['path'] = '../outside.ttf'
                    write_json(manifest, data)
                else:
                    (manifest.parent / 'brand.css').write_text('@import "https://example.com/tracking.css";')
                with self.assertRaises(ValueError):
                    load_brand(root, {'manifest': 'brand/brand.json'})

    def test_copied_bundle_changes_revoke_source_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            account = Path(temp)
            source = brand_fixture(account / 'source/company-brand')
            output = account / 'results/style'
            copy_brand_bundle(source, output / 'company-brand')
            spec = {'company_brand': {'manifest': 'source/company-brand/brand.json'}}
            qa = {'company_brand': brand_record(output, {'manifest': 'company-brand/brand.json'}),
                  'company_brand_typography': {'status': 'passed'}}
            self.assertTrue(current_brand_matches(account, spec, output, qa))
            (output / 'company-brand/brand.css').write_text('.banner{color:#f00!important}')
            qa['company_brand'] = brand_record(output, {'manifest': 'company-brand/brand.json'})
            self.assertFalse(current_brand_matches(account, spec, output, qa))

    def test_every_reference_text_uses_real_brand_font_without_legacy_faces(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as temp, sync_playwright() as playwright:
            root = Path(temp); brand_fixture(root / 'company-brand')
            data, _ = load_brand(root, {'manifest': 'company-brand/brand.json'})
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={'width': 1584, 'height': 396})
            try:
                for style, (_, reference, _) in registry().items():
                    content = copy.deepcopy(reference)
                    # Layout slots remain present; the renderer supports explicit
                    # empty logos without needing unrelated company fixtures.
                    from linkedin_pack.evidence import _reference_logo_slots
                    for container, index in _reference_logo_slots(content):
                        container[index] = ''
                    brief = {'selected_style': style, 'layout_mode': 'reference-faithful',
                             'reference_content': content, 'company_brand': {'manifest': 'company-brand/brand.json'}}
                    source = reference_banner_html(brief, style, asset_root=root)
                    self.assertNotIn("@font-face{font-family:'Inter'", source)
                    page.set_content(source)
                    page.evaluate('document.fonts.ready')
                    audit = audit_brand_typography(page, data, measure_design_details(page))
                    self.assertEqual(audit['status'], 'passed', (style, audit))
                    self.assertEqual(audit['families_used'], ['Example Brand'])
            finally:
                browser.close()

    def test_portable_export_rechecks_brand_sources_and_rendered_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); folder = released_examples(root)
            source = brand_fixture(folder / 'source/company-brand')
            account = json.loads((folder / 'account.json').read_text())
            account['company_brand'] = {'manifest': 'source/company-brand/brand.json'}
            write_json(folder / 'account.json', account)
            manifest = json.loads((folder / 'manifest.json').read_text())
            manifest['company_brand'] = brand_record(folder, account['company_brand'])
            _, source_files = load_brand(folder, account['company_brand'])
            for row in manifest['packages']:
                output = folder / 'results' / row['style']
                copy_brand_bundle(source, output / 'company-brand')
                brief = json.loads((output / 'brief.json').read_text())
                brief['company_brand'] = {'manifest': 'company-brand/brand.json'}
                write_json(output / 'brief.json', brief)
                record = brand_record(output, brief['company_brand'])
                qa = json.loads((output / 'qa.json').read_text())
                qa['company_brand'] = row['company_brand'] = record
                qa['company_brand_typography'] = {'status': 'passed'}
                qa['account_source_sha256'].update({path.relative_to(root).as_posix(): sha(path) for path in source_files})
                qa['account_source_sha256'][(folder / 'account.json').relative_to(root).as_posix()] = sha(folder / 'account.json')
                row['source_sha256'] = qa['account_source_sha256']
                qa['input_sha256'] = hashes(output, ('brief.json', 'banner.html'))
                write_json(output / 'qa.json', qa)
                row['sha256'] = hashes(output, set(row['sha256']) | set(record['files_sha256']))
            write_json(folder / 'manifest.json', manifest)
            export_shareable(root, root / 'dist/current.zip')
            first = folder / 'results' / manifest['packages'][0]['style'] / 'company-brand/brand.css'
            first.write_text('.banner{color:#f00!important}')
            with self.assertRaisesRegex(ValueError, 'Export blocked'):
                export_shareable(root, root / 'dist/changed.zip')


if __name__ == '__main__':
    unittest.main()
