"""Finalize only exact currently reviewed reference-faithful deliverables."""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT,write_json
from linkedin_pack.styles import STYLES
from linkedin_pack.reference_gallery import build_reference_gallery
from linkedin_pack.reference_review import review_record,reference_review_passed,buyer_review_record,reference_buyer_review_passed,FILES
from linkedin_pack.reference_qa import audit_reference_design
from linkedin_pack.reference_layout import registry
from linkedin_pack.evidence import validate_specificity

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    results=ROOT/'test_account/results';packages=[]
    profile=json.loads((ROOT/'test_account/source/profile.json').read_text())
    supplements=json.loads((ROOT/'test_account/source/supplemental-evidence.json').read_text())
    for slug in STYLES:
        folder=results/slug
        if not reference_review_passed(folder):raise SystemExit(f'Current independent reference acceptance required: {slug}')
        if not reference_buyer_review_passed(folder):raise SystemExit(f'Current independent buyer acceptance required: {slug}')
        brief=json.loads((folder/'brief.json').read_text());qa=json.loads((folder/'qa.json').read_text())
        if brief.get('layout_mode')!='reference-faithful':raise SystemExit(f'Wrong layout mode: {slug}')
        if not qa.get('passed') or qa.get('failures'):raise SystemExit(f'Technical QA failed: {slug}')
        measured=qa.get('design_details',{})
        if measured.get('reference_regions')!=registry()[slug][2] or audit_reference_design(measured)['status']!='passed':raise SystemExit(f'Current source geometry QA required: {slug}')
        for name,digest in qa.get('render_sha256',{}).items():
            if sha(folder/name)!=digest:raise SystemExit(f'Stale rendered file: {slug}/{name}')
        if not qa.get('reference_source_sha256'):raise SystemExit(f'Reference source binding missing: {slug}')
        for name,digest in qa['reference_source_sha256'].items():
            if sha(ROOT/name)!=digest:raise SystemExit(f'Source reference changed: {name}')
        for name,width in (('review-desktop.png',792),('review-mobile.png',390)):
            with Image.open(folder/name) as image:
                if image.width!=width:raise SystemExit(f'Native review width must be {width}: {slug}')
        specificity=validate_specificity(brief,profile,supplemental_evidence=supplements)
        ref_length=len((ROOT/'references'/slug/'headline.txt').read_text().strip())
        files=(*FILES,'preview.png','preview-mobile.png','reference-desktop.png','brief.json','banner.html','qa.json','logos/provenance.json',*brief.get('logo_assets',{}).values())
        packages.append({'style':slug,'technical_qa':'passed','visual_review':review_record(folder),'buyer_review':buyer_review_record(folder),
                         'headline_characters':len(brief['headline']),'original_headline_characters':ref_length,
                         'reference_regions':measured['reference_regions'],'region_differences':measured['region_differences'],
                         'type_measurements':measured['text'],'specificity':specificity,
                         'photo_roles':qa['photo_roles'],'reference_source_sha256':qa['reference_source_sha256'],
                         'sha256':{name:sha(folder/name) for name in files}})
    build_reference_gallery(results)
    for row in packages:row['package_zip_sha256']=sha(results/row['style']/'package.zip')
    write_json(ROOT/'test_account/manifest.json',{'generated_at':datetime.now(timezone.utc).isoformat(),
        'revision':'reference-faithful-original-compositions','subject':'Kal Walkden','reference_count':10,
        'acceptance':'all-ten-current-reference-and-blind-buyer-reviews-accepted','packages':packages,
        'source_sha256':{name:sha(ROOT/'test_account/source'/name) for name in ('profile.json','evidence-ledger.json','supplemental-evidence.json','company-context.json','website/walkden-home.txt')},
        'review_scope':'Independent AI-simulated original/adapted visual comparisons plus a separate founder buyer simulation of neutral desktop and native 390 px profiles. Fine secondary type follows original scale. Actual identity, content and authentic affiliation logo shapes differ. Not human buyer interviews or verification of self-reported results.'})
    sheet=Image.new('RGB',(1644,10*232),'#e9e9e7');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype(str(ROOT/'assets/fonts/Inter.ttf'),18)
    for i,slug in enumerate(STYLES):
        draw.text((20,i*232+5),slug+' — original / adapted',font=font,fill='#222222')
        for x,path in ((20,ROOT/'references'/slug/'banner.jpg'),(832,results/slug/'banner.png')):
            with Image.open(path) as im:sheet.paste(im.convert('RGB').resize((792,198),Image.Resampling.LANCZOS),(x,i*232+29))
    sheet.save(ROOT/'test_account/comparison-sheet.jpg',quality=95)
    print('Finalized 10 reference-faithful packages; independent image hashes and technical gates are current.')

if __name__=='__main__':main()
