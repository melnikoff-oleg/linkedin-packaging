"""Show original and adapted profiles together as the primary browsing surface."""
import html
import json
import zipfile
from pathlib import Path
from .styles import STYLES
from .reference_review import reference_review_passed,review_record,buyer_review_record

def build_reference_gallery(results):
    results=Path(results);cards=[]
    for slug,style in STYLES.items():
        folder=results/slug
        if not (folder/'reference-desktop.png').is_file():continue
        with zipfile.ZipFile(folder/'package.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name in ('banner.png','portrait.png','preview.png','headline.txt'):z.write(folder/name,name)
        status='Visual comparison accepted' if reference_review_passed(folder) else 'Visual comparison in review'
        report=review_record(folder)
        report_link=f'<a href="../../{report["report"]}">AI review</a>' if report else ''
        buyer=buyer_review_record(folder)
        if buyer:report_link+=f'<a href="../../{buyer["report"]}">Buyer simulation</a>'
        cards.append(f'''<article id="{slug}" data-style="{slug}"><header><h2>{html.escape(style['name'])}</h2><span>{status}</span></header><div class="pair"><figure><figcaption>ORIGINAL REFERENCE</figcaption><a href="{slug}/reference-comparison.png"><img src="{slug}/reference-desktop.png" loading="lazy" alt="Original {html.escape(style['name'])} profile"></a></figure><figure><figcaption>KAL · ADAPTED</figcaption><a href="{slug}/reference-comparison.png"><img src="{slug}/review-desktop.png" loading="lazy" alt="Kal profile using the same reference composition"></a></figure></div><div class="links"><a class="button" href="{slug}/package.zip" download>Download package</a><a href="{slug}/reference-comparison.png">Full-size comparison ↗</a><a href="{slug}/banner.png">Banner</a><a href="{slug}/portrait.png">Portrait</a><a href="{slug}/headline.txt">Headline</a><a href="{slug}/review-mobile.png">Mobile · 390 px</a>{report_link}</div></article>''')
    source='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kal Walkden · Original and adapted</title><style>*{box-sizing:border-box}body{margin:0;background:#f1f1ee;color:#191c1a;font:16px/1.5 Arial,sans-serif}.wrap{max-width:1720px;margin:auto;padding:40px 28px 70px}nav{font-size:12px;letter-spacing:1.7px;border-bottom:1px solid #d2d7d0;padding-bottom:20px;margin-bottom:32px}h1{font:400 48px/1.1 Georgia,serif;letter-spacing:-1.2px;margin:0 0 16px}.intro{max-width:770px;color:#566058;margin-bottom:26px}.filter{display:flex;gap:14px;align-items:center;margin:24px 0}select{padding:11px;border:1px solid #bfc8bf;background:white;border-radius:6px;max-width:100%}article{background:#fff;border:1px solid #d2d8cf;border-radius:10px;overflow:hidden;margin-bottom:28px}header{padding:18px 22px;display:flex;justify-content:space-between;align-items:center;gap:16px}h2{font-size:17px;margin:0;font-weight:600}header span{font-size:12px;color:#57674f}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;padding:18px;background:#e9e9e7}figure{margin:0;min-width:0}figcaption{font-size:11px;font-weight:700;letter-spacing:1.2px;margin-bottom:10px;color:#586158}img{width:100%;height:auto;display:block}a{color:#264e36;text-decoration:none}a:hover{text-decoration:underline}.links{padding:20px;display:flex;align-items:center;flex-wrap:wrap;gap:20px;font-size:13px}.button{padding:10px 15px;border-radius:6px;background:#233d2c;color:white}footer{color:#667067;font-size:13px;max-width:1000px}@media(max-width:760px){.wrap{padding:24px 14px}h1{font-size:36px}.pair{grid-template-columns:1fr;padding:12px;gap:24px}header{align-items:flex-start;flex-direction:column;gap:4px}.links{gap:15px}.filter{align-items:flex-start;flex-direction:column}}</style></head><body><main class="wrap"><nav>LINKEDIN PACKAGING · KAL WALKDEN</nav><h1>Original → adapted.</h1><p class="intro">Ten reference compositions, kept close: matching text placement, type scale, phrase lengths, portrait framing and logo positions. Kal’s identity, supported career details and actual company marks replace the source content.</p><div class="filter"><label for="style">Compare a reference</label><select id="style"><option value="all">All ten</option>'''
    source+=''.join(f'<option value="{slug}">{html.escape(style["name"])}</option>' for slug,style in STYLES.items())
    source+='</select></div>'+''.join(cards)+'''<footer>These are local LinkedIn previews; nothing is published. Independent review means a separate AI reviewer. Secondary labels retain the references’ original scale and may require the desktop view.<br><a href="../../docs/reference-fidelity.md">Rebuild notes and visual review</a> · <a href="../../docs/reference-media-prompts.md">Photographic assets and prompts</a> · <a href="../../README.md">Use the tool</a></footer></main><script>document.querySelector('#style').addEventListener('change',function(){document.querySelectorAll('article').forEach(card=>card.hidden=this.value!=='all'&&card.dataset.style!==this.value)})</script></body></html>'''
    (results/'index.html').write_text(source)
    return results/'index.html'
