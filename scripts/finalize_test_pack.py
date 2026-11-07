"""Rebuild example downloads and their manifest only after current blind reviews pass."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT, write_json
from linkedin_pack.gallery import build_gallery
from linkedin_pack.evidence import validate_specificity
from linkedin_pack.review import review_passed
from linkedin_pack.render import audit_design_details
from linkedin_pack.styles import STYLES


DESIGN_EVIDENCE = (
    'docs/design-system.md', 'docs/logo-treatment.md', 'docs/brief-compatibility.md',
    'docs/design-measurements-current-48px.json',
    'test_account/reviews/design-inputs.json', 'test_account/reviews/design-final.md',
    'test_account/reviews/design-recheck.md',
)


def _current_design_qa(folder):
    """A legacy true flag cannot substitute for current measured design QA."""
    try:
        qa=json.loads((folder/'qa.json').read_text())
        design=qa.get('design_details')
        if (qa.get('passed') is not True or qa.get('failures')!=[] or not isinstance(design,dict)
                or design.get('status')!='passed' or design.get('failures')!=[] or not design.get('text')):
            return None
        checked=audit_design_details(design)
        if checked['status']!='passed' or checked['thresholds']!=design.get('thresholds'):
            return None
        return qa
    except (OSError,ValueError,TypeError,AttributeError,KeyError):
        return None


def main():
    results = ROOT/'test_account/results'
    briefs=[json.loads(p.read_text()) for p in results.glob('*/brief.json')]
    if len(briefs)==10 and all(b.get('layout_mode')=='reference-faithful' for b in briefs):
        from scripts.finalize_reference_pack import main as finalize_reference
        return finalize_reference()
    missing = [slug for slug in STYLES if not review_passed(results/slug)]
    if missing:
        raise SystemExit('Current independent review required: '+', '.join(missing))
    qa_records={slug:_current_design_qa(results/slug) for slug in STYLES}
    invalid=[slug for slug,qa in qa_records.items() if qa is None]
    if invalid:
        raise SystemExit('Current passing technical/design QA required: '+', '.join(invalid))
    review_dimensions={}
    for slug in STYLES:
        review_dimensions[slug]={}
        for name,width in (('review-desktop.png',792),('review-mobile.png',390)):
            with Image.open(results/slug/name) as image:
                if image.width!=width:
                    raise SystemExit(f'Native review image must be {width}px wide: {slug}/{name}')
                review_dimensions[slug][name]=list(image.size)
    design_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in DESIGN_EVIDENCE}
    source=ROOT/'test_account/source'
    profile=json.loads((source/'profile.json').read_text())
    supplements=json.loads((source/'supplemental-evidence.json').read_text())
    source_checks={slug:validate_specificity(
        json.loads((results/slug/'brief.json').read_text()),profile,
        supplemental_evidence=supplements) for slug in STYLES}
    build_gallery(results)
    files = ('banner.png', 'portrait.png', 'preview.png', 'preview-mobile.png',
             'headline.txt', 'review-desktop.png', 'review-mobile.png')
    packages = []
    sheet = Image.new('RGB', (1640, 2640), '#edf0ed')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(ROOT/'assets/fonts/Inter.ttf'), 24)
    for index, (slug, style) in enumerate(STYLES.items()):
        folder = results/slug
        report = json.loads((folder/'blind-review.json').read_text())
        brief = json.loads((folder/'brief.json').read_text())
        provenance = json.loads((folder/'logos/provenance.json').read_text())
        packages.append({
            'style': slug, 'automated_checks_passed': qa_records[slug]['passed'],
            'design_details': qa_records[slug]['design_details'],
            'review_display_dimensions': review_dimensions[slug],
            'visual_review': 'accepted', 'review_model': report['model'],
            'review_prompt_sha256': report['prompt_sha256'],
            'interchangeability': report['interchangeability'],
            'brand_independent_clarity': report['brand_independent_clarity'],
            'plain_language_takeaway': report['plain_language_takeaway'],
            'distinctive_details': report['distinctive_details'],
            'memorability': report['memorability'],
            'specificity_check': source_checks[slug],
            'proof_cards': brief['proof_cards'],
            'logo_provenance': provenance,
            'supporting_sha256': {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
                                 for name in ('brief.json','blind-review.json','qa.json','logos/provenance.json',*brief.get('logo_assets',{}).values())},
            'headline_characters': len((folder/'headline.txt').read_text().strip()),
            'sha256': {name: hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in files},
            'photo_roles': json.loads((folder/'visual-assets.json').read_text()),
        })
        x = 20+(index % 2)*810; y = 20+(index // 2)*520
        draw.text((x, y), style['name'], fill='#193023', font=font)
        with Image.open(folder/'review-desktop.png') as im:
            im = im.convert('RGB'); im.thumbnail((790, 474))
            sheet.paste(im, (x, y+36))
    sheet.save(ROOT/'test_account/comparison-sheet.jpg', quality=94)
    write_json(ROOT/'test_account/manifest.json', {
        'generated_at': datetime.now(timezone.utc).isoformat(), 'subject': 'Kal Walkden',
        'source': 'https://www.linkedin.com/in/kalwalkden/',
        'revision': 'native-size-typography-spacing-and-transparent-original-logos',
        'acceptance': 'all-ten-current-technical-design-and-native-size-reviews-passed',
        'design_evidence_sha256': design_hashes,
        'source_sha256': {name:hashlib.sha256((source/name).read_bytes()).hexdigest()
                          for name in ('profile.json','evidence-ledger.json','supplemental-evidence.json','company-context.json','website/walkden-home.txt')},
        'reference_count': 10, 'avatar_edits': 10, 'distinct_banner_shots': 5,
        'transparent_banner_extractions': 5, 'packages': packages,
        'review_scope': 'AI assessment of exact 792px desktop and 390px mobile headers, including typography, spacing, original-logo treatment, plain-language comprehension and individual substance. Readers are assumed unfamiliar with the brands. Not real buyer interviews or independent verification of profile claims.',
    })
    print('Finalized ten current reviewed packages, downloads, gallery and hash manifest.')


if __name__ == '__main__':
    main()
