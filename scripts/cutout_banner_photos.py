"""Preserve the distinct shoot while extracting a true-alpha banner insert."""
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from linkedin_pack.core import ROOT,load_keys
from linkedin_pack.providers.kie import KieClient
from linkedin_pack.visual_assets import BANNER_PHOTO_STYLES
from PIL import Image
PROMPT='''Remove only the background from the supplied photograph and output the exact same subject as a clean transparent PNG cutout. Preserve the person, entire pose, camera angle, body proportions, facial details, glasses, hair, facial hair, clothes, hands, chair if present, and lighting EXACTLY. Do not redraw, restyle, beautify, change gaze, move hands or crop body. Background must be truly transparent alpha, not a checkerboard, white, black or any solid color. No added shadows, glow or outline. Keep the full subject silhouette and fine natural edges.'''
def run(slug):
 folder=ROOT/'test_account/results'/slug
 target=folder/'banner-photo-cutout.png'
 if not target.exists():
  client=KieClient(load_keys()['KIE_AI_API_KEY'],ROOT/'.cache/kie-cutout-v2')
  client.generate_headshot(folder/'banner-photo-master.png',PROMPT,target,resolution='1K',aspect_ratio='3:4',background='transparent',timeout=900)
 with Image.open(target) as img:
  assert img.mode=='RGBA' and img.getchannel('A').getextrema()[0]==0,'No true transparency'
 (folder/'banner-cutout-prompt.txt').write_text(PROMPT+'\n')
 print('ALPHA CUTOUT READY',slug,flush=True)
if __name__=='__main__':
 failed=False
 with ThreadPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,s):s for s in sorted(BANNER_PHOTO_STYLES)}
  for f in as_completed(jobs):
   try:f.result()
   except Exception as e:failed=True;print('FAILED',jobs[f],str(e),flush=True)
 raise SystemExit(int(failed))
