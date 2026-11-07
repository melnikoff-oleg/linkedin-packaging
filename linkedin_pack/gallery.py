"""Local browsing and download gallery; no service, tracking or remote assets."""
import html
import json
import zipfile
from pathlib import Path
from .styles import STYLES
from .core import ROOT
from .review import review_passed


def build_gallery(results):
    results=Path(results);cards=[]
    briefs=[json.loads(p.read_text()) for p in results.glob('*/brief.json')]
    if briefs and all(b.get('layout_mode')=='reference-faithful' for b in briefs):
        from .reference_gallery import build_reference_gallery
        return build_reference_gallery(results)
    for slug,style in STYLES.items():
        folder=results/slug
        if not (folder/'preview.png').exists():continue
        brief=json.loads((folder/'brief.json').read_text())
        with zipfile.ZipFile(folder/'package.zip','w',zipfile.ZIP_DEFLATED) as archive:
            for file in ['banner.png','portrait.png','preview.png','headline.txt']:
                archive.write(folder/file,arcname=file)
        title=html.escape(style['name']);headline=html.escape(brief['headline'])
        reference_portrait=next((p.name for p in (ROOT/'references'/slug).glob('portrait.*') if p.suffix in ('.png','.jpg','.jpeg')), 'portrait.jpg')
        status='Independent review: accepted' if review_passed(folder) else 'Review required'
        cards.append(f'''<article id="{slug}" data-style="{slug}"><div class="card-head"><span>{title}</span><span class="tag">{status}</span></div><a href="{slug}/preview.png"><img class="preview" loading="lazy" src="{slug}/preview.png" alt="{title} profile preview"></a><div class="detail"><p class="headline">{headline}</p><div class="links"><a class="primary" href="{slug}/package.zip" download>Download package ↗</a><a href="{slug}/banner.png" download>Banner</a><a href="{slug}/portrait.png" download>Portrait</a><a href="{slug}/headline.txt">Headline</a><a href="{slug}/review-mobile.png">Mobile view (390 px)</a><a href="{slug}/blind-review.json">Independent review</a></div><details><summary>Original reference & design analysis</summary><img loading="lazy" class="reference" src="../../references/{slug}/banner.jpg" alt="Original reference banner"><a href="../../references/{slug}/{reference_portrait}">Original profile portrait</a> · <a href="../../references/{slug}/analysis.md">Read the full breakdown ↗</a></details></div></article>''')
    source='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kal Walkden · LinkedIn packaging studio</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f4f5f1;color:#18251e;font-family:Arial,sans-serif}.wrap{max-width:1220px;padding:46px 32px 80px;margin:auto}nav{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #cdd6cb;padding-bottom:24px;font-size:12px;font-weight:700;letter-spacing:2px}.dot{display:inline-block;width:10px;height:10px;background:#446547;border-radius:50%;margin-right:9px}.label{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#6b786b;margin:47px 0 15px}h1{font-family:Georgia,serif;font-size:64px;line-height:1.05;font-weight:400;letter-spacing:-2px;margin:0;max-width:760px}.intro{max-width:680px;line-height:1.65;color:#5f6b61;font-size:17px;margin:22px 0 32px}.facts{display:flex;gap:25px;border-top:1px solid #d5dcd3;border-bottom:1px solid #d5dcd3;padding:18px 0;font-size:13px;margin-bottom:28px}.filter{display:flex;align-items:center;gap:15px;margin:25px 0;font-size:14px}select{border:1px solid #c7d2c7;border-radius:7px;background:white;padding:12px;color:#24392b;max-width:100%}article{background:white;border:1px solid #d7ded5;border-radius:14px;overflow:hidden;margin:0 0 34px}.card-head{display:flex;justify-content:space-between;gap:10px;padding:20px 24px;font-size:16px;font-weight:600}.tag{font-size:11px;font-weight:400;background:#f0f4eb;padding:5px 9px;border-radius:20px;color:#53654e}.preview{display:block;width:100%;height:auto;border-block:1px solid #e9ece6}.detail{padding:24px}.headline{max-width:850px;line-height:1.55;font-size:16px;margin:0 0 22px}.links{display:flex;align-items:center;gap:21px;flex-wrap:wrap}a{color:#2c5539;text-decoration:none;font-size:13px}a:hover{text-decoration:underline}.primary{display:inline-block;background:#233d2c;color:white;padding:12px 17px;border-radius:6px}details{margin-top:23px;border-top:1px solid #e5e9e1;padding-top:18px;font-size:13px;color:#6d776b}summary{cursor:pointer}.reference{display:block;width:100%;margin:18px 0 12px}footer{font-size:13px;line-height:1.7;color:#6d776b}button{font:inherit}@media(max-width:650px){.wrap{padding:24px 16px}h1{font-size:44px}.facts{flex-wrap:wrap;gap:10px 20px}.card-head{padding:16px;font-size:14px}.tag{display:none}.detail{padding:18px}.links{gap:16px}.intro{font-size:15px}}
    </style></head><body><main class="wrap"><nav><span><i class="dot"></i>LINKEDIN PACKAGING STUDIO</span><span>01 / KAL WALKDEN</span></nav><p class="label">Ten references. One recognizable person.</p><h1>A clearer first impression.</h1><p class="intro">Ten complete visual directions for Kal Walkden. Meal delivery, online fundraising, vehicle protection and energy software: each direction explains the business, the problem and the result. Original company logos and role labels show where the work happened.</p><div class="facts"><span>3168 × 792 banner</span><span>800 × 800 portrait</span><span>Clear business context + concrete results</span><span>Desktop + mobile previews</span></div><div class="filter"><label for="style">Explore a direction</label><select id="style"><option value="all">All ten directions</option>'''
    source+=''.join(f'<option value="{slug}">{html.escape(style["name"])}</option>' for slug,style in STYLES.items())
    source+='</select></div>'+''.join(cards)+'''<footer>Previews simulate the LinkedIn profile layout; nothing has been published. Banner text is rendered from editable HTML, portraits were edited with Kie using Kal’s source photograph, and reference images remain available for comparison.<br><a href="../visual-review.md">Visual quality review</a> · <a href="../../README.md">Setup and use this tool</a> · <a href="../../docs/reference-synthesis.md">What the references teach</a></footer></main><script>document.getElementById('style').addEventListener('change',function(){for(const card of document.querySelectorAll('article'))card.hidden=this.value!=='all'&&card.dataset.style!==this.value;});</script></body></html>'''
    (results/'index.html').write_text(source,encoding='utf-8')
    return results/'index.html'
