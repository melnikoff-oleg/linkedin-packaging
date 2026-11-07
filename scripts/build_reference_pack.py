"""Rebuild the ten examples with fixed original-reference compositions."""
import argparse
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT,write_json
from linkedin_pack.reference_layout import registry
from linkedin_pack.render import render_package,preview_html
from linkedin_pack.styles import STYLES
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES

REFERENCE_HEADLINES={
    'clarekitching':'Fractional CTO · Part-time technology leadership | Vehicle protection: quotes from >5 minutes to <5 seconds, ~10× visitor-to-purchase conversion at ForeverCar',
    'diandraescobar':'Hands-on fractional CTO for growing businesses | At Factor: daily peak outages ended without a full rewrite | Former CTO, ForeverCar',
    'laraacostar':'Fractional CTO & hands-on builder | At Factor: ended daily peak outages with an incremental platform rebuild, avoiding a full rewrite | Former CTO, ForeverCar',
    'mattgray1':'From spreadsheet to acquired software at Digital H2O | Fractional CTO, W27 Collective',
    'adrian-kul':'Fractional CTO & co-founder, W27 Collective | At Factor: daily peak outages ended without a full rewrite | Former CTO, ForeverCar | Former VP, Double Good',
    'donnellychris':'Fractional CTO | At Factor: daily peak outages ended without a full rewrite | W27 co-founder',
    'rob-hoffman-ceo':'Fractional CTO | At Factor: daily peak outages ended with an incremental rebuild | Former CTO, ForeverCar; former VP, Double Good',
    'jakezward':'Fractional CTO | At Double Good: ~30% more software releases and ~25% less testing effort with AI-assisted workflows | W27 co-founder',
    'charlie-hills':'Fractional CTO | Digital H2O: spreadsheet to acquired business',
    'liamkarlsson':'Hands-on fractional CTO at W27 Collective | At Factor: daily peak outages ended without a full rewrite | Former VP, Double Good; former CTO, ForeverCar',
}


def make_source_brief(slug, *, root=None):
 root=Path(root) if root is not None else ROOT
 cases=json.loads((root/'test_account/case-directions.json').read_text())
 case=cases[slug]
 ledger=json.loads((root/'test_account/source/evidence-ledger.json').read_text())
 evidence=[{'claim':row['statement'],'source':row['source'].get('profile_url','')+' · '+row['source']['file']+' '+row['source'].get('json_path','')} for row in ledger['claims']]
 evidence.extend({'claim':'; '.join(row.get('supports',[])),'source':row['url']} for row in ledger['external_sources'])
 return dict(name='Kal Walkden',audience='Business owners, founders and referral partners unfamiliar with these employers, considering part-time technology leadership for a growing business',positioning='Part-time technology leadership with results in meal delivery, vehicle-protection sales, online fundraising and energy software; company names and logos attribute the proof.',evidence=evidence,selected_style=slug,headline=case['headline'],banner_title=case['banner_title'],banner_subtitle=case['banner_subtitle'],proof_points=[],proof_cards=case['proof_cards'],logo_assets=case.get('logo_assets',{}),cta='',portrait_prompt=STYLES[slug]['portrait'],rationale='Reference-led composition leading with understandable business context and exact scoped outcomes; company names and logos are supporting attribution. Approximations and former-role labels are retained. Original company logos indicate documented roles, not client endorsement. Source performance figures are self-reported, not independently audited. Audience is inferred from current fractional CTO work; the complete profile must pass the substitution test.')

def prepare(slug, *, root=None):
    root=Path(root) if root is not None else ROOT
    destination=root/'test_account/results'/slug
    brief=make_source_brief(slug,root=root)
    brief['layout_mode']='reference-faithful'
    brief['headline']=REFERENCE_HEADLINES[slug]
    brief['reference_content']=copy.deepcopy(registry()[slug][1])
    brief['proof_cards']=[]
    brief['rationale']='The original reference fixes layout, typography scale, line count, logo positions and whitespace. Only supported subject copy, identity and truthful affiliations replace reference content. Secondary text follows original display sizes.'
    curated=root/'test_account/source/company-logos/curated'
    provenance={};assets={}
    (destination/'logos').mkdir(parents=True,exist_ok=True)
    for key in ('2839269','1167899','2454643','forevercar','digitalh2o','1009'):
        shutil.copyfile(curated/f'{key}.png',destination/'logos'/f'{key}.png')
        provenance[key]=json.loads((curated/f'{key}.json').read_text())
        assets[key]=f'logos/{key}.png'
    write_json(destination/'logos/provenance.json',provenance)
    brief['logo_assets']=assets
    return brief


def comparisons(slug, *, root=None):
    from playwright.sync_api import sync_playwright
    root=Path(root) if root is not None else ROOT
    folder=root/'test_account/results'/slug;ref=root/'references'/slug
    profile=json.loads((ref/'profile.json').read_text())
    portrait=next(ref.glob('portrait.*'))
    name=profile.get('name') or ' '.join([profile.get('firstName',''),profile.get('lastName','')]) or slug
    original=preview_html({'name':name,'headline':(ref/'headline.txt').read_text().strip()},f'../../../references/{slug}/banner.jpg',f'../../../references/{slug}/{portrait.name}')
    (folder/'reference-preview.html').write_text(original)
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(viewport={'width':848,'height':680},device_scale_factor=1)
        page.goto((folder/'reference-preview.html').resolve().as_uri());page.locator('img').evaluate_all('els=>Promise.all(els.map(e=>e.decode()))')
        page.locator('.card').screenshot(path=str(folder/'reference-desktop.png'))
        html=f'''<!doctype html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box}}body{{margin:0;padding:20px;width:1644px;background:#e9e9e7;font:16px Arial;color:#222}}.grid{{display:grid;grid-template-columns:792px 792px;gap:20px}}.label{{padding:0 0 12px;font-weight:600}}img{{display:block;width:792px;height:auto}}.banner{{height:198px;object-fit:cover}}.space{{height:24px}}</style></head><body><div class="grid"><div><div class="label">ORIGINAL REFERENCE</div><img class="banner" src="../../../references/{slug}/banner.jpg"></div><div><div class="label">KAL — SAME COMPOSITION</div><img class="banner" src="banner.png"></div></div><div class="space"></div><div class="grid"><img src="reference-desktop.png"><img src="review-desktop.png"></div></body></html>'''
        (folder/'comparison.html').write_text(html)
        page.set_viewport_size({'width':1644,'height':900});page.goto((folder/'comparison.html').resolve().as_uri());page.locator('img').evaluate_all('els=>Promise.all(els.map(e=>e.decode()))')
        page.locator('body').screenshot(path=str(folder/'reference-comparison.png'))
        browser.close()



def render_reference(slug, *, root=None):
    """Render one fixture through the current reference mode and comparisons."""
    root=Path(root) if root is not None else ROOT
    if slug not in STYLES:raise ValueError('Unknown reference style')
    folder=root/'test_account/results'/slug
    brief=prepare(slug,root=root)
    background={'mattgray1':'mountain-background-reference.png','liamkarlsson':'liam-background-reference.png'}.get(slug)
    qa=render_package(brief,folder/'portrait-reference.png' if (folder/'portrait-reference.png').exists() else folder/'portrait-master.png',folder,location='Chicago, Illinois, United States',
                      banner_photo_path=(folder/'banner-photo-reference.png' if (folder/'banner-photo-reference.png').exists() else folder/'banner-photo-cutout.png') if slug in BANNER_PHOTO_STYLES else None,
                      background_path=root/'test_account/source'/background if background else None)
    comparisons(slug,root=root)
    print(slug,'PASS' if qa['passed'] else qa['failures'],flush=True)
    return qa['passed']


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--style',choices=STYLES);args=parser.parse_args(argv)
    archive=ROOT/'tmp/before-reference-fidelity'
    if not archive.exists():shutil.copytree(ROOT/'test_account/results',archive)
    failed=[]
    for slug in ([args.style] if args.style else STYLES):
        if not render_reference(slug):failed.append(slug)
    return bool(failed)

if __name__=='__main__':raise SystemExit(main())
