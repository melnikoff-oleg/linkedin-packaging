"""Reproducible, evidence-backed ten-style validation set for Kal Walkden."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT,load_keys,write_json
from linkedin_pack.styles import STYLES,IDENTITY_RULES
from linkedin_pack.providers.kie import KieClient
from linkedin_pack.render import render_package
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES,banner_photo_prompt,validate_photo_pair,banner_cutout_prompt,has_transparent_background

def make_brief(slug):
 from scripts.build_reference_pack import make_source_brief
 return make_source_brief(slug,root=ROOT)

def generate(slug):
 target=ROOT/'test_account/results'/slug;target.mkdir(parents=True,exist_ok=True)
 brief=make_brief(slug);write_json(target/'brief.json',brief)
 prompt=(target/'portrait-prompt.txt').read_text().strip() if (target/'portrait-prompt.txt').exists() else IDENTITY_RULES+'\n'+STYLES[slug]['portrait']
 (target/'portrait-prompt.txt').write_text(prompt+'\n')
 path=target/'portrait-master.png'
 if not path.exists():
  KieClient(load_keys()['KIE_AI_API_KEY'],ROOT/'.cache/kie').generate_headshot(ROOT/'test_account/source/portrait.png',prompt,path,timeout=900)
 if slug in BANNER_PHOTO_STYLES:
  banner=target/'banner-photo-master.png'
  bp=banner_photo_prompt(slug)
  (target/'banner-photo-prompt.txt').write_text(bp+'\n')
  if not banner.exists():
   KieClient(load_keys()['KIE_AI_API_KEY'],ROOT/'.cache/kie-banner-v2').generate_headshot(ROOT/'test_account/source/portrait.png',bp,banner,resolution='2K',aspect_ratio='3:4',timeout=900)
  validate_photo_pair(path,banner)
  cutout=target/'banner-photo-cutout.png'
  if not cutout.exists():
   KieClient(load_keys()['KIE_AI_API_KEY'],ROOT/'.cache/kie-cutout-v2').generate_headshot(banner,banner_cutout_prompt(),cutout,resolution='1K',aspect_ratio='3:4',background='transparent',timeout=900)
  if not has_transparent_background(cutout):raise ValueError('Banner insert needs genuine transparency')
 print('PORTRAIT READY',slug,flush=True)
 return path

def render(slug):
 # Compatibility entry point: never overwrite accepted reference fixtures with
 # the superseded evidence-card composition. No import back into this module.
 from scripts.build_reference_pack import render_reference
 return render_reference(slug,root=ROOT)


def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--render-only',action='store_true');p.add_argument('--style',choices=STYLES);p.add_argument('--workers',type=int,default=3);a=p.parse_args(argv)
 if a.workers<1:p.error('--workers must be positive')
 slugs=[a.style] if a.style else list(STYLES)
 failed=False
 if not a.render_only:
  with ThreadPoolExecutor(max_workers=a.workers) as pool:
   tasks={pool.submit(generate,slug):slug for slug in slugs}
   for future in as_completed(tasks):
    try:future.result()
    except Exception as exc:
     failed=True
     print('ERROR',tasks[future],type(exc).__name__,str(exc),flush=True)
 for slug in slugs:
  if not (ROOT/'test_account/results'/slug/'portrait-master.png').exists():
   print('MISSING PORTRAIT',slug,flush=True);failed=True
  else:
   try:
    if not render(slug):failed=True
   except Exception as exc:
    print('RENDER ERROR',slug,type(exc).__name__,str(exc),flush=True);failed=True
 return 1 if failed else 0

if __name__=='__main__':
 raise SystemExit(main())
