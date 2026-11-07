"""Offline, account-scoped reference packages and a browsable example collection.

Render:   python scripts/build_example_pack.py render --account kayla-bautista
Finalize: python scripts/build_example_pack.py finalize --account kayla-bautista
Gallery:  python scripts/build_example_pack.py gallery

No provider calls or generated claims. Explicit briefs, source portraits, separate
banner photographs and original transparent logos must already exist locally.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT, safe_slug, validate_brief, write_json
from linkedin_pack.evidence import enrich_brief_assets, validate_specificity, _reference_logo_slots
from linkedin_pack.reference_layout import registry
from linkedin_pack.reference_qa import audit_reference_design
from linkedin_pack.reference_review import (
    FILES, review_record, buyer_review_record,
    reference_review_passed, reference_buyer_review_passed,
)
from linkedin_pack.render import preview_html, render_package
from linkedin_pack.styles import STYLES
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES
from linkedin_pack.company_brand import load_brand, brand_record, copy_brand_bundle

DOWNLOADS = ('banner.png', 'portrait.png', 'preview.png', 'headline.txt')
BUYER_FILES = ('review-desktop.png', 'review-mobile.png')
OUTPUT_FILES = tuple(dict.fromkeys((*FILES, *DOWNLOADS, 'preview-mobile.png', 'reference-desktop.png')))
BACKGROUNDS = {
    'mattgray1': 'mountain-background-reference.png',
    'liamkarlsson': 'liam-background-reference.png',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def account_path(slug):
    return ROOT / 'examples' / safe_slug(slug)


def load_account(slug):
    folder = account_path(slug)
    account = read_json(folder / 'account.json')
    if not isinstance(account.get('name'), str) or not account['name'].strip():
        raise ValueError('account.json requires the subject name')
    return folder, account


def local_asset(folder, relative):
    if not isinstance(relative, str) or not relative.startswith('source/'):
        raise ValueError('Account assets must be explicit source/ paths')
    path = (folder / relative).resolve()
    if not path.is_relative_to((folder / 'source').resolve()) or not path.is_file():
        raise ValueError(f'Missing account source asset: {relative}')
    return path


def inputs_for_style(folder, account, style):
    assets = account.get('assets', {})
    settings = {key: assets[key] for key in ('portrait', 'banner_photo') if key in assets}
    settings.update(assets.get('styles', {}).get(style, {}))
    # Conventional filenames keep the manifest short while every subject stays
    # inside its own source tree. Explicit account overrides take precedence.
    settings.setdefault('portrait', f'source/portraits/{style}.png')
    portrait = local_asset(folder, settings['portrait'])
    photo = None
    if style in BANNER_PHOTO_STYLES:
        settings.setdefault('banner_photo', f'source/banner-photos/{style}.png')
        photo = local_asset(folder, settings['banner_photo'])
    background = None
    if settings.get('background'):
        background = local_asset(folder, settings['background'])
    elif style in BACKGROUNDS:
        # Reuse only the established landscape/texture, never a fixture person.
        background = ROOT / 'test_account/source' / BACKGROUNDS[style]
        if not background.is_file():
            raise ValueError(f'Missing reference background: {background.name}')
    return portrait, photo, background


def source_brief(folder, account, style):
    raw = read_json(folder / 'source/briefs' / f'{style}.json')
    if 'reference_content' not in raw or 'headline' not in raw:
        raise ValueError('Each account brief requires explicit headline and reference_content')
    brief = {
        'name': account['name'], 'audience': account.get('audience', ''),
        'positioning': account.get('summary', ''), 'evidence': [],
        'selected_style': style, 'layout_mode': 'reference-faithful',
        'headline': '', 'banner_title': account['name'], 'banner_subtitle': '',
        'proof_points': [], 'proof_cards': [], 'cta': '',
        'portrait_prompt': 'Supplied local source portrait; no generation in this build.',
        'rationale': 'Source-backed identity and copy in the original reference composition.',
    }
    brief.update(copy.deepcopy(raw))
    if brief['name'] != account['name'] or brief['selected_style'] != style:
        raise ValueError('Brief identity/style must match its account and filename')
    if brief.get('layout_mode') != 'reference-faithful':
        raise ValueError('Example packages require the fixed reference composition')
    if account.get('company_brand'):
        if account['company_brand'].get('manifest') != 'source/company-brand/brand.json':
            raise ValueError('Company branding requires source/company-brand/brand.json inside its own account.')
        brief['company_brand'] = copy.deepcopy(account['company_brand'])
    elif brief.get('company_brand'):
        raise ValueError('Company brand overrides must be explicit in account.json.')
    validate_brief(brief)
    return brief


def prepare_brief(folder, account, style, destination):
    brief = source_brief(folder, account, style)
    # A complete local curated cache is mandatory. This preflight means the
    # existing provenance validator can never fall back to a network download.
    keys = {container[index] for container, index in _reference_logo_slots(brief['reference_content']) if container[index]}
    cache = folder / 'source/company-logos'
    for key in keys:
        if not isinstance(key, str) or '/' in key or '\\' in key:
            raise ValueError('Invalid reference logo key')
        for suffix in ('.png', '.json'):
            if not (cache / 'curated' / (key + suffix)).is_file():
                raise ValueError(f'Original local logo/provenance required: {key}{suffix}')
    profile = read_json(folder / 'source/profile.json')
    supplement_path = folder / 'source/supplemental-evidence.json'
    supplements = read_json(supplement_path) if supplement_path.exists() else []
    prepared = enrich_brief_assets(brief, profile, destination, cache_dir=cache, supplemental_evidence=supplements)
    if brief.get('company_brand'):
        copy_brand_bundle(folder / brief['company_brand']['manifest'], destination / 'company-brand')
        prepared['company_brand'] = {'manifest': 'company-brand/brand.json'}
    return prepared


def comparisons(folder, account, style):
    from playwright.sync_api import sync_playwright
    reference = ROOT / 'references' / style
    profile = read_json(reference / 'profile.json')
    portrait = next(reference.glob('portrait.*'))
    name = profile.get('name') or ' '.join([profile.get('firstName', ''), profile.get('lastName', '')]) or style
    relative = lambda path: Path(os.path.relpath(path, folder)).as_posix()
    original = preview_html(
        {'name': name, 'headline': (reference / 'headline.txt').read_text().strip()},
        relative(reference / 'banner.jpg'), relative(portrait),
    )
    (folder / 'reference-preview.html').write_text(original, encoding='utf-8')
    label = html.escape(account['name'].upper())
    treatment = html.escape(account.get('variant_label', 'SAME COMPOSITION').upper())
    source = f'''<!doctype html><html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box}}body{{margin:0;padding:20px;width:1644px;background:#e9e9e7;font:16px Arial;color:#222}}
    .grid{{display:grid;grid-template-columns:792px 792px;gap:20px}}.label{{padding:0 0 12px;font-weight:600}}
    img{{display:block;width:792px;height:auto}}.banner{{height:198px;object-fit:cover}}.space{{height:24px}}
    </style></head><body><div class="grid"><div><div class="label">ORIGINAL REFERENCE</div>
    <img class="banner" src="{relative(reference / 'banner.jpg')}"></div><div>
    <div class="label">{label} · {treatment}</div><img class="banner" src="banner.png"></div></div>
    <div class="space"></div><div class="grid"><img src="reference-desktop.png"><img src="review-desktop.png"></div></body></html>'''
    (folder / 'comparison.html').write_text(source, encoding='utf-8')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 848, 'height': 680}, device_scale_factor=1)
        page.goto((folder / 'reference-preview.html').resolve().as_uri())
        page.locator('img').evaluate_all('els=>Promise.all(els.map(e=>e.decode()))')
        page.locator('.card').screenshot(path=str(folder / 'reference-desktop.png'))
        page.set_viewport_size({'width': 1644, 'height': 900})
        page.goto((folder / 'comparison.html').resolve().as_uri())
        page.locator('img').evaluate_all('els=>Promise.all(els.map(e=>e.decode()))')
        page.locator('body').screenshot(path=str(folder / 'reference-comparison.png'))
        browser.close()


def current_source_hashes(folder, account, style):
    portrait, photo, background = inputs_for_style(folder, account, style)
    files = [folder / 'account.json', folder / 'source/profile.json', folder / 'source/briefs' / f'{style}.json', portrait]
    files.extend(path for path in (photo, background, folder / 'source/supplemental-evidence.json') if path and path.is_file())
    if account.get('company_brand'):
        _, brand_files = load_brand(folder, account['company_brand'])
        files.extend(brand_files)
    brief = source_brief(folder, account, style)
    for key in {container[index] for container, index in _reference_logo_slots(brief['reference_content']) if container[index]}:
        files.extend(folder / 'source/company-logos/curated' / (key + ext) for ext in ('.png', '.json'))
    return {str(path.relative_to(ROOT)): sha(path) for path in files}


def current_reference_hashes(style):
    reference = ROOT / 'references' / style
    files = (reference / 'banner.jpg', reference / 'headline.txt', *reference.glob('portrait.*'))
    return {str(path.relative_to(ROOT)): sha(path) for path in files}


def output_hashes_current(output, qa):
    """Require every delivered/reviewed image, not a caller-selected subset."""
    try:
        return qa.get('example_output_sha256') == {name: sha(output / name) for name in OUTPUT_FILES}
    except OSError:
        return False


def review_inputs(folder, account):
    rows = {}
    for style in STYLES:
        output = folder / 'results' / style
        if all((output / name).is_file() for name in FILES):
            rows[style] = {
                'sha256': {name: sha(output / name) for name in FILES},
                'files': {name: str(output / name) for name in FILES},
            }
    write_json(folder / 'reviews/review-inputs.json', {
        'subject': account['name'], 'account': folder.name,
        'reference_review_glob': 'reference-independent-*.json',
        'buyer_review_glob': 'reference-buyer-release*.json',
        'instruction': 'Independent reviewers must inspect current pixels. Do not infer approval from this hash inventory. Reference review uses all six hashes; buyer review uses only native desktop/mobile hashes.',
        'reviews': rows,
    })


def render_account(slug, style=None):
    folder, account = load_account(slug)
    failures = []
    for selected in ([style] if style else STYLES):
        output = folder / 'results' / selected
        try:
            # An old approved export must disappear before any source changes.
            (output / 'package.zip').unlink(missing_ok=True)
            (folder / 'manifest.json').unlink(missing_ok=True)
            portrait, photo, background = inputs_for_style(folder, account, selected)
            brief = prepare_brief(folder, account, selected, output)
            qa = render_package(brief, portrait, output, location=account.get('location', ''),
                                banner_photo_path=photo, background_path=background)
            comparisons(output, account, selected)
            qa['account_source_sha256'] = current_source_hashes(folder, account, selected)
            # Keep the generic buyer-review hash schema backward-compatible,
            # while this workflow also freezes the downloadable full preview.
            qa['example_output_sha256'] = {name: sha(output / name) for name in OUTPUT_FILES}
            write_json(output / 'qa.json', qa)
            if not qa['passed']:
                failures.append(selected)
            print(f'{slug}/{selected}: ' + ('PASS' if qa['passed'] else json.dumps(qa['failures'])), flush=True)
        except (OSError, ValueError, RuntimeError) as error:
            failures.append(selected)
            print(f'{slug}/{selected}: ERROR {error}', flush=True)
    review_inputs(folder, account)
    build_galleries()
    return not failures


def accepted(folder, style):
    output = folder / 'results' / style
    try:
        if not (reference_review_passed(output, reviews_dir=folder / 'reviews')
                and reference_buyer_review_passed(output, reviews_dir=folder / 'reviews')):
            return False
        qa = read_json(output / 'qa.json')
        account = read_json(folder / 'account.json')
        if qa.get('account_source_sha256') != current_source_hashes(folder, account, style):
            return False
        if account.get('company_brand') and not current_brand_matches(folder, account, output, qa):
            return False
        if not qa.get('render_sha256') or not qa.get('reference_source_sha256'):
            return False
        return output_hashes_current(output, qa) and all(
            sha(output / name) == digest for name, digest in qa['render_sha256'].items()) and (
            qa['reference_source_sha256'] == current_reference_hashes(style))
    except (OSError, ValueError, TypeError, KeyError):
        return False


def current_brand_matches(folder, account, output, qa):
    """Bind copied render dependencies to the corresponding account source."""
    source = brand_record(folder, account['company_brand'])
    rendered = brand_record(output, {'manifest': 'company-brand/brand.json'})
    return (qa.get('company_brand') == rendered
            and qa.get('company_brand_typography', {}).get('status') == 'passed'
            and {Path(name).relative_to('source').as_posix(): value for name, value in source['files_sha256'].items()} == rendered['files_sha256'])


def deterministic_zip(folder):
    with zipfile.ZipFile(folder / 'package.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in DOWNLOADS:
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (folder / name).read_bytes())


def finalize_account(slug):
    folder, account = load_account(slug)
    profile = read_json(folder / 'source/profile.json')
    supplemental = folder / 'source/supplemental-evidence.json'
    supplements = read_json(supplemental) if supplemental.exists() else []
    packages = []
    for style in STYLES:
        output = folder / 'results' / style
        if not accepted(folder, style):
            raise ValueError(f'Current independent reference and buyer acceptance required: {slug}/{style}')
        brief, qa = read_json(output / 'brief.json'), read_json(output / 'qa.json')
        if brief.get('name') != account['name'] or brief.get('selected_style') != style or brief.get('layout_mode') != 'reference-faithful':
            raise ValueError(f'Incorrect account identity/style: {style}')
        measured = qa.get('design_details', {})
        if qa.get('passed') is not True or qa.get('failures') != []:
            raise ValueError(f'Current technical QA required: {style}')
        if measured.get('reference_regions') != registry()[style][2] or audit_reference_design(measured)['status'] != 'passed':
            raise ValueError(f'Current reference geometry required: {style}')
        if not qa.get('render_sha256') or not qa.get('reference_source_sha256'):
            raise ValueError(f'Missing rendered/reference hash bindings: {style}')
        if not output_hashes_current(output, qa):
            raise ValueError(f'Deliverable changed after render or complete output hashes missing: {style}')
        for name, digest in qa['render_sha256'].items():
            if sha(output / name) != digest:
                raise ValueError(f'Stale rendered file: {style}/{name}')
        if qa['reference_source_sha256'] != current_reference_hashes(style):
            raise ValueError(f'Changed original reference or missing reference hashes: {style}')
        if qa.get('account_source_sha256') != current_source_hashes(folder, account, style):
            raise ValueError(f'Account source changed after render: {style}')
        for filename, width in (('review-desktop.png', 792), ('review-mobile.png', 390)):
            with Image.open(output / filename) as image:
                if image.width != width:
                    raise ValueError(f'Native {width}px review image required: {style}/{filename}')
        specificity = validate_specificity(brief, profile, supplemental_evidence=supplements)
        files = tuple(dict.fromkeys((*FILES, *DOWNLOADS, 'preview-mobile.png', 'reference-desktop.png',
            'brief.json', 'banner.html', 'qa.json', 'visual-assets.json', 'logos/provenance.json', *brief.get('logo_assets', {}).values())))
        if account.get('company_brand'):
            if not current_brand_matches(folder, account, output, qa):
                raise ValueError(f'Current company brand source and typography required: {style}')
            _, brand_files = load_brand(output, brief['company_brand'])
            files += tuple(path.relative_to(output).as_posix() for path in brand_files)
        packages.append({
            'style': style, 'technical_qa': 'passed', 'specificity': specificity,
            'visual_review': review_record(output, reviews_dir=folder / 'reviews'),
            'buyer_review': buyer_review_record(output, reviews_dir=folder / 'reviews'),
            'headline_characters': len(brief['headline']), 'reference_regions': measured['reference_regions'],
            'photo_roles': qa['photo_roles'], 'source_sha256': qa['account_source_sha256'],
            'reference_source_sha256': qa['reference_source_sha256'],
            **({'company_brand': qa['company_brand']} if account.get('company_brand') else {}),
            'sha256': {name: sha(output / name) for name in files},
        })
    # Nothing is exported until every style passes; no partially approved pack.
    for row in packages:
        output = folder / 'results' / row['style']
        deterministic_zip(output)
        row['package_zip_sha256'] = sha(output / 'package.zip')
    write_json(folder / 'manifest.json', {
        'generated_at': datetime.now(timezone.utc).isoformat(), 'account': slug, 'subject': account['name'],
        'profile_url': account.get('profile_url', ''), 'reference_count': len(packages),
        'revision': 'company-branded-reference-composition' if account.get('company_brand') else 'multi-account-reference-faithful',
        **({'company_brand': brand_record(folder, account['company_brand']),
            'original_account': account.get('original_account'),
            'variant_label': account.get('variant_label', '')} if account.get('company_brand') else {}),
        'acceptance': 'all-ten-current-reference-and-independent-buyer-reviews-accepted',
        'download_files': list(DOWNLOADS), 'packages': packages,
        'review_scope': 'Independent AI visual comparison and separate AI buyer simulation of native desktop/mobile profiles. Not human interviews, factual verification or a published LinkedIn profile.',
    })
    comparison_sheet(folder)
    build_galleries()
    print(f'Finalized {len(packages)} reviewed packages for {account["name"]}.')


def comparison_sheet(folder):
    sheet = Image.new('RGB', (1644, len(STYLES) * 232), '#e9e9e7')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(ROOT / 'assets/fonts/Inter.ttf'), 18)
    for i, style in enumerate(STYLES):
        draw.text((20, i * 232 + 5), style + ' · original / adapted', font=font, fill='#222222')
        for x, path in ((20, ROOT / 'references' / style / 'banner.jpg'), (832, folder / 'results' / style / 'banner.png')):
            with Image.open(path) as image:
                sheet.paste(image.convert('RGB').resize((792, 198), Image.Resampling.LANCZOS), (x, i * 232 + 29))
    sheet.save(folder / 'comparison-sheet.jpg', quality=95)


GALLERY_CSS = '''
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f5f4ef;color:#17251e;font:15px/1.5 Inter,Arial,sans-serif}a{color:inherit;text-decoration:none}button,select{font:inherit}button,a,select{-webkit-tap-highlight-color:transparent}button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid #9ebcaf;outline-offset:4px}
.shell{max-width:1480px;margin:auto;padding:0 32px}nav{padding:25px 0;border-bottom:1px solid #d7dcd4;display:flex;justify-content:space-between;gap:20px;font-size:12px;letter-spacing:.12em;text-transform:uppercase}nav a{letter-spacing:0;text-transform:none}.hero{padding:55px 0 35px;display:grid;grid-template-columns:1.3fr 1fr;gap:60px;align-items:end}.eyebrow{font-size:11px;letter-spacing:.17em;text-transform:uppercase;color:#65796a;font-weight:700}h1{font:400 clamp(40px,4.5vw,64px)/1.06 Georgia,serif;letter-spacing:-2px;margin:14px 0 0}h1 em{color:#5d7764;font-weight:400}.intro{margin:0;max-width:560px;color:#607064;font-size:16px;line-height:1.7}.toolbar{position:sticky;top:0;z-index:5;background:#f5f4eff5;backdrop-filter:blur(16px);border-top:1px solid #d7dcd4;border-bottom:1px solid #d7dcd4;padding:15px 0;margin-bottom:34px;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.controls{display:flex;gap:10px;flex-wrap:wrap}select{padding:10px 34px 10px 13px;border:1px solid #cdd5cb;border-radius:7px;background:#fff;color:#243c2b;max-width:100%}.tabs{display:flex;gap:4px;border:1px solid #d2dacf;border-radius:8px;padding:4px;background:#e9ede6}.tabs button{border:0;background:none;padding:7px 12px;border-radius:5px;color:#526b59;cursor:pointer}.tabs button[aria-pressed=true]{background:white;color:#1b3425;box-shadow:0 1px 4px #18392313}.account{margin:42px 0 28px}.account-head{display:flex;align-items:center;justify-content:space-between;gap:24px;margin:0 0 18px}.identity{display:flex;align-items:center;gap:15px}.identity img{width:58px;height:58px;border-radius:50%;object-fit:cover;background:#e6eae3}.identity h2{font:400 28px/1.1 Georgia,serif;letter-spacing:-.5px;margin:0 0 6px}.identity p{margin:0;font-size:13px;color:#607064}.source-links{display:flex;gap:16px;font-size:12px;color:#587160}.cards{display:grid;grid-template-columns:1fr 1fr;gap:24px}.card{min-width:0;background:#fff;border:1px solid #d8ded4;border-radius:12px;overflow:hidden;box-shadow:0 4px 18px #19352404}.card-header{padding:17px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}.card-header h3{margin:0;font-size:15px;font-weight:600}.index{font-size:10px;color:#849185;letter-spacing:.14em;margin-right:9px}.status{font-size:10px;white-space:nowrap;background:#eef3eb;color:#426047;border-radius:20px;padding:4px 8px}.status.pending{background:#f5f0e3;color:#8a713e}.stage{padding:16px;background:#e9ece6;min-height:240px;display:flex;align-items:flex-start;justify-content:center;border-top:1px solid #e2e7de;border-bottom:1px solid #e2e7de}.stage a{display:block;max-width:100%}.stage img{display:block;width:100%;height:auto;border-radius:6px;box-shadow:0 3px 12px #18281e12}.stage img.mobile{display:none;width:390px;max-width:100%;border-radius:0}.stage img.comparison{display:none}.download{padding:17px 20px 13px;display:flex;align-items:center;justify-content:space-between;gap:10px}.primary{background:#203f2d;color:#fff;border-radius:6px;padding:9px 12px;font-size:12px;font-weight:600}.pending-link{font-size:12px;color:#7d795f}.detail-links{font-size:11px;color:#63766a;display:flex;gap:12px;flex-wrap:wrap;padding:0 20px 18px}.detail-links a:hover,.source-links a:hover{text-decoration:underline}.quick{font-size:11px;color:#6c7d70}.empty{padding:40px;color:#607064}footer{margin:50px 0 0;padding:25px 0 40px;border-top:1px solid #d7dcd4;display:flex;justify-content:space-between;gap:36px;font-size:12px;color:#748075}footer p{margin:0;max-width:850px}body[data-view=mobile] .stage img.desktop,body[data-view=comparison] .stage img.desktop{display:none}body[data-view=mobile] .stage img.mobile{display:block}body[data-view=comparison] .stage img.comparison{display:block}body[data-view=comparison] .cards{grid-template-columns:1fr}body[data-view=comparison] .stage{padding:0}body[data-view=comparison] .stage img{border-radius:0;box-shadow:none}[hidden]{display:none!important}@media(max-width:850px){.shell{padding:0 18px}.hero{grid-template-columns:1fr;gap:24px;padding:36px 0 28px}.cards{grid-template-columns:1fr}.toolbar{position:static}.account-head{align-items:flex-start;flex-direction:column;gap:12px}.stage{padding:10px}footer{flex-direction:column;gap:15px}.card-header{padding:15px}.download{padding:15px}.detail-links{padding:0 15px 16px}}@media(max-width:430px){.shell{padding:0 12px}h1{font-size:40px;letter-spacing:-1.5px}.tabs button{padding:7px 9px}.card-header h3{font-size:14px}.status{font-size:9px}.controls{width:100%}.controls select{flex:1;min-width:0}}
'''


def gallery_html(accounts, destination):
    esc = html.escape
    link = lambda path: esc(Path(os.path.relpath(path, destination.parent)).as_posix(), quote=True)
    branded = bool(accounts) and all(account.get('collection') == 'company-branded' for _, account in accounts)
    collection = 'Company-branded variants' if branded else 'Original reference collection'
    other_gallery = ROOT / ('examples/index.html' if branded else 'examples/company-branded.html')
    other_label = 'Original reference collection' if branded else 'Company-branded variants'
    sections = []
    total = 0
    for folder, account in accounts:
        cards = []
        for index, (style, detail) in enumerate(STYLES.items(), 1):
            output = folder / 'results' / style
            if not all((output / name).exists() for name in (*FILES, 'reference-desktop.png', 'preview.png')):
                continue
            total += 1
            is_accepted = accepted(folder, style) and (folder / 'manifest.json').exists()
            manifest = read_json(folder / 'manifest.json') if is_accepted else {}
            final_record = next((row for row in manifest.get('packages', []) if row.get('style') == style), {})
            ready = is_accepted and (output / 'package.zip').exists() and final_record.get('package_zip_sha256') == sha(output / 'package.zip')
            status = '<span class="status">Reviewed</span>' if is_accepted else '<span class="status pending">In review</span>'
            download = f'<a class="primary" href="{link(output / "package.zip")}" download>Download 4-file pack ↓</a>' if ready else '<span class="pending-link">Independent review pending</span>'
            links = ''.join(f'<a href="{link(output / filename)}" download>{label}</a>' for filename, label in zip(DOWNLOADS, ('Banner', 'Portrait', 'Profile preview', 'Headline')))
            cards.append(f'''<article class="card" id="{esc(folder.name)}-{style}" data-style="{style}">
            <div class="card-header"><h3><span class="index">{index:02d}</span>{esc(detail['name'])}</h3>{status}</div>
            <div class="stage"><a href="{link(output / 'review-desktop.png')}" data-desktop="{link(output / 'review-desktop.png')}" data-mobile="{link(output / 'review-mobile.png')}" data-comparison="{link(output / 'reference-comparison.png')}">
            <img class="desktop" src="{link(output / 'review-desktop.png')}" alt="{esc(account['name'])} in the {esc(detail['name'])} style, desktop profile" loading="lazy">
            <img class="mobile" src="{link(output / 'review-mobile.png')}" alt="{esc(account['name'])}, native 390 pixel mobile profile" loading="lazy">
            <img class="comparison" src="{link(output / 'reference-comparison.png')}" alt="Original {esc(detail['name'])} reference beside the {esc(account['name'])} adaptation" loading="lazy"></a></div>
            <div class="download">{download}<a class="quick" href="{link(output / 'reference-comparison.png')}">Original + adapted ↗</a></div>
            <div class="detail-links">{links}<a href="{link(output / 'review-mobile.png')}">Mobile</a></div></article>''')
        if not cards:
            continue
        portrait = folder / 'results' / next(style for style in STYLES if (folder / 'results' / style / 'portrait.png').exists()) / 'portrait.png'
        source_links = f'<a href="{link(folder / "source/profile.json")}">Source profile ↗</a>'
        if (folder / 'manifest.json').exists():
            source_links += f'<a href="{link(folder / "manifest.json")}">Review manifest ↗</a>'
        variant = account.get('variant_label', 'Original reference treatment')
        if account.get('company_brand'):
            source_links += f'<a href="{link(folder / "source/company-brand/provenance.json")}">Brand sources ↗</a>'
            source_links += f'<a href="{link(ROOT / "examples" / account["original_account"] / "results/index.html")}">Original designs ↗</a>' if account.get('original_account') else ''
        sections.append(f'''<section class="account" data-account="{esc(folder.name)}"><div class="account-head"><div class="identity"><img src="{link(portrait)}" alt=""><div><h2>{esc(account['name'])}</h2><p><strong>{esc(variant)}</strong> · {esc(account.get('summary', 'Ten reference compositions, one identity.'))}</p></div></div><div class="source-links">{source_links}</div></div><div class="cards">{''.join(cards)}</div></section>''')
    options = ''.join(f'<option value="{esc(folder.name)}">{esc(account["name"])} · {esc(account.get("variant_label", "Original reference"))}</option>' for folder, account in accounts)
    styles = ''.join(f'<option value="{style}">{esc(detail["name"])}</option>' for style, detail in STYLES.items())
    kal = link(ROOT / 'test_account/results/index.html')
    title = 'The same composition.<br><em>Company colors and type.</em>' if branded else 'A different identity.<br><em>The same design language.</em>'
    intro = ('Explore company-branded adaptations of the ten reference compositions. Each retains its structure, with website-sourced colors and fonts plus coordinated profile portraits. Compare desktop, mobile and the source reference.' if branded else 'Explore ten reference styles through real professional backgrounds. Compare the original composition, inspect desktop and mobile profiles, and download each finished package.')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LinkedIn profile examples · {collection}</title><style>{GALLERY_CSS}</style></head>
    <body data-view="desktop"><main class="shell"><nav><span>LinkedIn packaging · {collection}</span><a href="{link(other_gallery)}">{other_label} ↗</a><a href="{kal}">Kal Walkden collection ↗</a></nav>
    <div class="hero"><div><div class="eyebrow">{len(sections)} people · {total} complete profiles</div><h1>{title}</h1></div><p class="intro">{intro}</p></div>
    <div class="toolbar"><div class="controls"><select id="account-filter" aria-label="Choose a person"><option value="all">All people</option>{options}</select><select id="style-filter" aria-label="Choose a reference style"><option value="all">All ten styles</option>{styles}</select></div><div class="tabs" role="group" aria-label="Preview view"><button data-view="desktop" aria-pressed="true">Desktop</button><button data-view="mobile" aria-pressed="false">Mobile</button><button data-view="comparison" aria-pressed="false">Compare original</button></div></div>
    {''.join(sections) or '<p class="empty">Examples are being prepared.</p>'}
    <footer><p>Local profile previews; nothing is published. Each package contains a banner, portrait, profile preview and headline. “Reviewed” requires current technical checks plus independent AI visual and buyer reviews of the exact images. Source claims and employment are attributed, not independently audited.</p><a href="{link(ROOT / 'README.md')}">Project guide ↗</a></footer></main>
    <script>const person=document.querySelector('#account-filter'),style=document.querySelector('#style-filter');function filter(){{document.querySelectorAll('.account').forEach(s=>{{s.hidden=person.value!=='all'&&s.dataset.account!==person.value;s.querySelectorAll('.card').forEach(c=>c.hidden=style.value!=='all'&&c.dataset.style!==style.value)}})}}person.addEventListener('change',filter);style.addEventListener('change',filter);document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{{document.body.dataset.view=b.dataset.view;document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('.stage a').forEach(a=>a.href=a.dataset[b.dataset.view])}}));</script></body></html>'''


def build_galleries():
    accounts = []
    for path in sorted((ROOT / 'examples').glob('*/account.json')):
        folder, account = path.parent, read_json(path)
        accounts.append((folder, account))
        output = folder / 'results/index.html'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(gallery_html([(folder, account)], output), encoding='utf-8')
    output = ROOT / 'examples/index.html'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(gallery_html([(folder, account) for folder, account in accounts if account.get('collection', 'reference') == 'reference'], output), encoding='utf-8')
    company_output = ROOT / 'examples/company-branded.html'
    company_output.write_text(gallery_html([(folder, account) for folder, account in accounts if account.get('collection') == 'company-branded'], company_output), encoding='utf-8')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('render', 'finalize', 'gallery', 'prepare-brand'))
    parser.add_argument('--account')
    parser.add_argument('--style', choices=STYLES)
    parser.add_argument('--brand', help='Verified local brand.json to copy into the account source tree')
    args = parser.parse_args(argv)
    if args.action != 'gallery' and not args.account:
        parser.error('--account is required for rendering/finalization')
    if args.style and args.action != 'render':
        parser.error('--style is only available for render')
    if (args.action == 'prepare-brand') != bool(args.brand):
        parser.error('--brand is required only for prepare-brand')
    try:
        if args.action == 'render':
            return 0 if render_account(args.account, args.style) else 1
        if args.action == 'prepare-brand':
            folder, account = load_account(args.account)
            copy_brand_bundle(Path(args.brand).resolve(), folder / 'source/company-brand')
            account['company_brand'] = {'manifest': 'source/company-brand/brand.json'}
            account['collection'] = 'company-branded'
            write_json(folder / 'account.json', account)
            print(f'Prepared verified offline company brand for {args.account}.')
        elif args.action == 'finalize':
            finalize_account(args.account)
        else:
            print(build_galleries())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
