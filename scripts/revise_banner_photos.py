"""Generate distinct banner photographs for the corrected sample packages."""
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT,load_keys
from linkedin_pack.providers.kie import KieClient
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES,banner_photo_prompt,validate_photo_pair

def build(slug):
 target=ROOT/'test_account/results'/slug
 prompt=banner_photo_prompt(slug)
 path=target/'banner-photo-master.png'
 (target/'banner-photo-prompt.txt').write_text(prompt+'\n')
 client=KieClient(load_keys()['KIE_AI_API_KEY'],ROOT/'.cache/kie-banner-v2')
 client.generate_headshot(ROOT/'test_account/source/portrait.png',prompt,path,resolution='2K',aspect_ratio='3:4',timeout=900)
 validate_photo_pair(target/'portrait-master.png',path)
 print('DISTINCT BANNER PHOTO READY',slug,flush=True)

if __name__=='__main__':
 failed=False
 with ThreadPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(build,s):s for s in sorted(BANNER_PHOTO_STYLES)}
  for f in as_completed(jobs):
   try:f.result()
   except Exception as e:failed=True;print('FAILED',jobs[f],str(e),flush=True)
 raise SystemExit(1 if failed else 0)
