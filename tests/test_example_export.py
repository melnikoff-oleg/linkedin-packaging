"""Project exports retain drafts but cannot redistribute stale example releases."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from linkedin_pack.core import export_shareable, write_json
from linkedin_pack.reference_review import FILES
from linkedin_pack.review import PACKAGE_FILES
from linkedin_pack.styles import STYLES
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES


DOWNLOADS = ('banner.png', 'portrait.png', 'preview.png', 'headline.txt')
OUTPUTS = set(FILES) | set(DOWNLOADS) | {'preview-mobile.png', 'reference-desktop.png'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(base, names):
    return {name: digest(base / name) for name in names}


def released_examples(root):
    """A complete release in a foreign root; no checkout globals or mocks."""
    folder = root / 'examples/person'
    write_json(folder / 'account.json', {'name': 'Example Person', 'assets': {
        'portrait': 'source/portrait.png', 'banner_photo': 'source/banner-photo.png'}})
    write_json(folder / 'source/profile.json', {'name': 'Example Person'})
    for name in ('portrait.png', 'banner-photo.png'):
        (folder / 'source' / name).write_bytes(name.encode())
    for name in ('mountain-background-reference.png', 'liam-background-reference.png'):
        path = root / 'test_account/source' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    visual, buyer, rows = {}, [], []
    for style in STYLES:
        output = folder / 'results' / style
        output.mkdir(parents=True)
        source_brief = folder / 'source/briefs' / f'{style}.json'
        write_json(source_brief, {'reference_content': {}})
        reference = root / 'references' / style
        reference.mkdir(parents=True)
        for name in ('banner.jpg', 'portrait.png', 'headline.txt'):
            (reference / name).write_bytes(f'{style} original {name}'.encode())
        for name in OUTPUTS | {'banner.html'}:
            (output / name).write_bytes(f'{style} current {name}'.encode())
        write_json(output / 'brief.json', {'name': 'Example Person', 'selected_style': style,
                                         'layout_mode': 'reference-faithful', 'logo_assets': {}})
        write_json(output / 'visual-assets.json', {})
        write_json(output / 'logos/provenance.json', {})
        sources = [folder / 'account.json', folder / 'source/profile.json', source_brief,
                   folder / 'source/portrait.png']
        if style in BANNER_PHOTO_STYLES:
            sources.append(folder / 'source/banner-photo.png')
        if style in ('mattgray1', 'liamkarlsson'):
            name = 'mountain-background-reference.png' if style == 'mattgray1' else 'liam-background-reference.png'
            sources.append(root / 'test_account/source' / name)
        source_hashes = {str(path.relative_to(root)): digest(path) for path in sources}
        reference_hashes = {str(path.relative_to(root)): digest(path) for path in reference.iterdir()}
        write_json(output / 'qa.json', {'passed': True, 'failures': [],
            'input_sha256': hashes(output, ('brief.json', 'banner.html')),
            'render_sha256': hashes(output, PACKAGE_FILES),
            'example_output_sha256': hashes(output, OUTPUTS),
            'account_source_sha256': source_hashes, 'reference_source_sha256': reference_hashes})
        visual[style] = {'verdict': 'accept', 'findings': [], 'sha256': hashes(output, FILES)}
        buyer.append({'style': style, 'verdict': 'accept', 'required_findings': [],
                      'sha256': hashes(output, ('review-desktop.png', 'review-mobile.png'))})
        with zipfile.ZipFile(output / 'package.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in DOWNLOADS:
                archive.writestr(name, (output / name).read_bytes())
        rows.append({'style': style, 'technical_qa': 'passed', 'source_sha256': source_hashes,
            'reference_source_sha256': reference_hashes,
            'sha256': hashes(output, OUTPUTS | {'brief.json', 'banner.html', 'qa.json',
                                               'visual-assets.json', 'logos/provenance.json'}),
            'package_zip_sha256': digest(output / 'package.zip')})
    ref_report = folder / 'reviews/reference-independent-01.json'
    buyer_report = folder / 'reviews/reference-buyer-release-01.json'
    write_json(ref_report, {'reviews': visual})
    write_json(buyer_report, {'reviews': buyer})
    for row, item in zip(rows, buyer):
        row['visual_review'] = {**visual[row['style']], 'report': str(ref_report.relative_to(root)),
                                'report_sha256': digest(ref_report)}
        row['buyer_review'] = {**item, 'report': str(buyer_report.relative_to(root)),
                               'report_sha256': digest(buyer_report)}
    write_json(folder / 'manifest.json', {'account': 'person', 'subject': 'Example Person',
        'reference_count': len(STYLES), 'download_files': list(DOWNLOADS), 'packages': rows,
        'acceptance': 'all-ten-current-reference-and-independent-buyer-reviews-accepted'})
    (folder / 'results/index.html').write_text('<span>Reviewed</span>')
    return folder


class ExampleExportTests(unittest.TestCase):
    def test_complete_release_exports_from_supplied_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); released_examples(root)
            destination = export_shareable(root, root / 'dist/share.zip')
            with zipfile.ZipFile(destination) as archive:
                packages = [name for name in archive.namelist() if name.startswith('linkedin-package/examples/') and name.endswith('/package.zip')]
                self.assertEqual(len(packages), 10)

    def test_drafts_and_existing_kal_artifacts_remain_exportable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(root / 'examples/draft/account.json', {'name': 'Draft Person'})
            old = root / 'test_account/results/example/package.zip'
            old.parent.mkdir(parents=True); old.write_bytes(b'Existing Kal artifact')
            destination = export_shareable(root, root / 'dist/share.zip')
            with zipfile.ZipFile(destination) as archive:
                self.assertIn('linkedin-package/examples/draft/account.json', archive.namelist())
                self.assertIn('linkedin-package/test_account/results/example/package.zip', archive.namelist())

    def test_stale_release_is_blocked_before_archive_creation(self):
        cases = ('preview', 'source', 'new_supplement', 'reference', 'zip', 'missing_manifest',
                 'missing_style', 'missing_file_hash', 'later_rejection', 'missing_review', 'extra_zip')
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); folder = released_examples(root)
                style = next(iter(STYLES)); output = folder / 'results' / style
                manifest = json.loads((folder / 'manifest.json').read_text())
                if case == 'preview':
                    (output / 'preview.png').write_bytes(b'Other person')
                elif case == 'source':
                    write_json(folder / 'source/profile.json', {'name': 'Changed subject'})
                elif case == 'new_supplement':
                    write_json(folder / 'source/supplemental-evidence.json', [])
                elif case == 'reference':
                    (root / 'references' / style / 'banner.jpg').write_bytes(b'Changed original')
                elif case == 'zip':
                    # Updating only the archive checksum cannot bless unrelated ZIP contents.
                    with zipfile.ZipFile(output / 'package.zip', 'w') as archive:
                        for name in DOWNLOADS:
                            archive.writestr(name, b'Unreviewed replacement')
                    manifest['packages'][0]['package_zip_sha256'] = digest(output / 'package.zip')
                    write_json(folder / 'manifest.json', manifest)
                elif case == 'missing_manifest':
                    (folder / 'manifest.json').unlink()
                elif case == 'missing_style':
                    manifest['packages'].pop(); write_json(folder / 'manifest.json', manifest)
                elif case == 'missing_file_hash':
                    manifest['packages'][0]['sha256'].pop('preview.png')
                    write_json(folder / 'manifest.json', manifest)
                elif case == 'later_rejection':
                    item = {**manifest['packages'][0]['buyer_review'], 'verdict': 'revise',
                            'required_findings': ['Visible identity mismatch']}
                    write_json(folder / 'reviews/reference-buyer-release-02.json', {'reviews': [item]})
                elif case == 'missing_review':
                    (folder / 'reviews/reference-independent-01.json').unlink()
                elif case == 'extra_zip':
                    (folder / 'old-package').mkdir()
                    (folder / 'old-package/package.zip').write_bytes(b'Stale release')
                destination = root / 'dist/share.zip'
                with self.assertRaisesRegex(ValueError, 'Export blocked: finalized example person'):
                    export_shareable(root, destination)
                self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
