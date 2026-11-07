"""Prepare the test subject's named-case copy and original company logos; no image generation."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT, write_json
from linkedin_pack.evidence import enrich_brief_assets
from linkedin_pack.styles import STYLES
from scripts.build_test_pack import make_brief


def main():
    source=ROOT/'test_account/source';profile=json.loads((source/'profile.json').read_text())
    cases_file=ROOT/'test_account/case-directions.json';cases=json.loads(cases_file.read_text())
    supplements=json.loads((source/'supplemental-evidence.json').read_text())
    for slug in STYLES:
        output=ROOT/'test_account/results'/slug
        plan=enrich_brief_assets(make_brief(slug),profile,output,cache_dir=source/'company-logos',supplemental_evidence=supplements)
        for company,key in [('ForeverCar','forevercar'),('Digital H2O','digitalh2o')]:
            if not any(card['company']==company for card in plan['proof_cards']):
                continue
            original=source/'company-logos'/f'{key}.png'
            (output/'logos').mkdir(exist_ok=True)
            shutil.copyfile(original,output/'logos'/f'{key}.png')
            plan['logo_assets'][key]=f'logos/{key}.png'
            metadata=json.loads((output/'logos/provenance.json').read_text())
            metadata[key]=json.loads((source/'company-logos'/f'{key}.provenance.json').read_text())
            write_json(output/'logos/provenance.json',metadata)
        cases[slug]['logo_assets']=plan['logo_assets']
        write_json(output/'brief.json',plan)
        print('CASE ASSETS',slug,'source-linked; logos',len(plan['logo_assets']),flush=True)
    write_json(cases_file,cases)


if __name__=='__main__':
    main()
