"""Deterministic HTML typography, browser rasterization, profile previews and QA."""
from __future__ import annotations
import base64
import hashlib
import io
import html
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageOps
from .core import ROOT, validate_brief, write_json
from .styles import STYLES
from .visual_assets import BANNER_PHOTO_STYLES, validate_photo_pair, has_transparent_background


def esc(value):
    return html.escape(str(value), quote=True)


def contrast(a, b):
    def lum(value):
        rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
        linear=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
        return sum(x*w for x,w in zip(linear,[.2126,.7152,.0722]))
    x,y=sorted([lum(a),lum(b)])
    return (y+.05)/(x+.05)


def data_uri(path, trim_alpha=False):
    path=Path(path)
    if trim_alpha:
        with Image.open(path) as source:
            rgba=source.convert('RGBA')
            # Generated cutouts sometimes contain remote alpha=1 specks. They
            # are effectively invisible but can double the crop width and make
            # the subject appear tiny. Use visible alpha for the crop bounds;
            # retain every original pixel/alpha value inside the resulting crop.
            bounds=rgba.getchannel('A').point(lambda value: 255 if value > 1 else 0).getbbox()
            if bounds:
                # Remove empty canvas only; retain a small transparent inset.
                left,top,right,bottom=bounds
                rgba=rgba.crop((max(0,left-12),max(0,top-12),min(rgba.width,right+12),min(rgba.height,bottom+12)))
            buffer=io.BytesIO();rgba.save(buffer,format='PNG')
            return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
    mime='image/png' if path.suffix.lower()=='.png' else 'image/jpeg'
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()


def font_css():
    normal='\n'.join(f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{base64.b64encode((ROOT/'assets/fonts'/f'{name}.ttf').read_bytes()).decode()});font-weight:{weight};}}" for name,weight in [('Inter','100 900'),('Manrope','200 800'),('DMSerifDisplay','400')])
    italic=ROOT/'assets/fonts/DMSerifDisplay-Italic.ttf'
    normal+=(f"\n@font-face{{font-family:'DMSerifDisplay';src:url(data:font/ttf;base64,{base64.b64encode(italic.read_bytes()).decode()});font-style:italic;font-weight:400;}}" if italic.exists() else '')
    elegant=ROOT/'assets/fonts/CormorantGaramond.ttf'
    return normal+(f"\n@font-face{{font-family:'CormorantGaramond';src:url(data:font/ttf;base64,{base64.b64encode(elegant.read_bytes()).decode()});font-weight:300 700;}}" if elegant.exists() else '')


def wave_svg():
    paths=''.join(f'<path d="M-100 {y} C 360 {y-220}, 460 {y+210}, 850 {y-20} S 1450 {y-220}, 1720 {y+20}"/>' for y in range(130,680,9))
    return f'<svg class="waves" viewBox="0 0 1584 396" aria-hidden="true"><g fill="none" stroke="#e4b96f" stroke-width="1.3" opacity=".58">{paths}</g></svg>'


def banner_html(brief, style, banner_photo_path=None, background_path=None, asset_root=None):
    validate_brief(brief)
    if brief.get('layout_mode')=='reference-faithful':
        from .reference_layout import reference_banner_html
        return reference_banner_html(brief,style,banner_photo_path,background_path,asset_root)
    s=dict(STYLES[style])
    palette=brief.get('brand_palette', {})
    if not isinstance(palette,dict) or any(k not in ('bg','fg','accent') or not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for k,v in palette.items()):
        raise ValueError('brand_palette must contain only bg, fg, accent in #RRGGBB format')
    s.update(palette)
    if palette and (contrast(s['fg'],s['bg'])<4.5 or contrast(s['accent'],s['bg'])<4.5):
        raise ValueError('Brand palette needs foreground contrast >=4.5 and accent contrast >=4.5')
    if 'proof_cards' in brief:
        from .evidence_layout import evidence_banner_html
        return evidence_banner_html(brief,style,s,banner_photo_path,background_path,asset_root)
    title=brief['banner_title'].split('\n')
    # Explicit line breaks make typography editable and deterministic.
    title_html='<br>'.join(f'<span class="line line-{i}">{esc(line)}</span>' for i,line in enumerate(title))
    proof=''.join(f'<span>{esc(p)}</span>' for p in brief['proof_points'])
    portrait=f'<img class="hero-portrait" alt="" src="{data_uri(banner_photo_path,trim_alpha=True)}">' if banner_photo_path and style in BANNER_PHOTO_STYLES else ''
    bg=f'<img class="landscape" alt="" src="{data_uri(background_path)}">' if background_path else ''
    name=esc(brief['name'])
    subtitle=esc(brief['banner_subtitle'])
    cta=esc(brief['cta'])
    # Text slots only use the subject's evidence; reference logos/testimonials are never inserted.
    body=f'''<div class="brand" data-qa="essential">{name}</div>
    <div class="content"><h1 data-qa="essential">{title_html}</h1><div class="subtitle" data-qa="essential">{subtitle}</div>
    <div class="proof" data-qa="essential">{proof}</div><div class="cta" data-qa="essential">{cta}</div></div>{portrait}'''
    extras=''
    if style=='diandraescobar':
        extras='<div class="evidence-cards">'+''.join(f'<div class="evidence-card" data-qa="essential"><small>EXPERIENCE</small><strong>{esc(p)}</strong></div>' for p in brief['proof_points'])+'</div>'
    if style=='donnellychris':
        extras='<div class="globe"></div>'
    if style=='jakezward':
        extras='<div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>'
    if style=='charlie-hills':
        extras='<div class="systems">'+''.join(f'<div class="system-row" data-qa="essential"><span class="system-number">0{i+1}</span><span>{esc(label)}</span></div>' for i,label in enumerate(brief['proof_points']))+'</div>'
    if style=='adrian-kul':
        extras='<div class="quiet-form"></div><div class="quiet-mark" aria-hidden="true">↗</div>'
    if style=='liamkarlsson':
        extras=wave_svg()
    styles='''
    *{box-sizing:border-box}html,body{margin:0;width:1584px;height:396px;overflow:hidden}
    .banner{position:relative;width:1584px;height:396px;overflow:hidden;background:var(--bg);color:var(--fg);font-family:Inter,Arial,sans-serif}
    .brand{position:absolute;left:56px;top:37px;font-size:26px;letter-spacing:-.8px;font-weight:700;z-index:4;max-width:360px}
    .content{position:absolute;left:460px;right:65px;top:68px;z-index:3}
    h1{font-size:58px;line-height:1.06;letter-spacing:-2.4px;font-weight:720;margin:0 0 23px;white-space:nowrap}
    .line:last-child{color:var(--accent)}
    .subtitle{font-size:23px;line-height:1.25;max-width:920px;letter-spacing:-.4px}
    .proof{display:flex;gap:28px;margin-top:30px;font-size:17px;font-weight:600;letter-spacing:.15px;align-items:center}
    .proof span+span{border-left:1px solid currentColor;padding-left:28px}
    .cta{font-size:16px;margin-top:20px;font-weight:500}
    .hero-portrait{position:absolute;right:0;bottom:0;width:440px;height:396px;object-fit:contain;object-position:50% 100%;z-index:2;mask-image:linear-gradient(to right,transparent 0%,black 22%)}
    .landscape{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
    .waves{position:absolute;inset:0;width:100%;height:100%;z-index:0}
    .clarekitching{background-image:linear-gradient(#ffffff08 1px,transparent 1px),linear-gradient(90deg,#ffffff08 1px,transparent 1px);background-size:80px 80px}
    .clarekitching:after{content:'';position:absolute;bottom:0;left:0;width:100%;height:27px;background:linear-gradient(90deg,#ffc493 28%,#70c4c1 28% 64%,#06585b 64%)}
    .clarekitching .content{left:695px;top:46px;right:50px}
    .clarekitching h1{font-family:DMSerifDisplay,Georgia,serif;font-size:58px;font-weight:400;letter-spacing:-1px;line-height:1.09}
    .clarekitching .line:last-child{background:var(--accent);color:#003b3d;font-style:italic;padding:0 5px}
    .clarekitching .subtitle{font-size:25px;max-width:750px}
    .clarekitching .proof{margin-top:24px;font-size:16px;gap:20px}.clarekitching .proof span+span{padding-left:20px}
    .clarekitching .hero-portrait,.clarekitching .cta{display:none}
    .diandraescobar{background:radial-gradient(ellipse at 42% 58%,#36706d 0%,#003337 40%,#001c20 82%)}
    .diandraescobar .content{left:1145px;right:34px;top:52px}.diandraescobar h1{font-size:57px;letter-spacing:-2.3px;line-height:1.04;margin-bottom:20px}
    .diandraescobar .subtitle{font-size:20px;max-width:380px}.diandraescobar .proof{display:none}.diandraescobar .cta{font-size:16px;max-width:320px}
    .diandraescobar .hero-portrait{right:400px;width:430px;mask-image:linear-gradient(to right,transparent,black 20%,black 80%,transparent)}
    .evidence-cards{position:absolute;left:445px;top:43px;width:340px;z-index:4;display:flex;flex-direction:column;gap:19px}.evidence-card{background:#f7faf7;color:#162f30;padding:14px 19px;border:1px solid #aec9c5;border-radius:12px;box-shadow:0 6px 18px #00191a40}.evidence-card:nth-child(3){margin-left:90px;margin-right:-90px}.evidence-card:nth-child(2){margin-left:35px;margin-right:-35px}.evidence-card small{display:block;font-size:10px;font-weight:700;letter-spacing:2px;color:#537a75;margin-bottom:7px}.evidence-card strong{font-size:21px;letter-spacing:-.6px;font-weight:650}
    .laraacostar{background:radial-gradient(ellipse at 43% 65%,#723727,transparent 37%),linear-gradient(135deg,#050505,#1c1c1c)}
    .laraacostar .content{left:875px;right:40px;top:62px}.laraacostar h1{font-size:49px;line-height:1.1;letter-spacing:-2px}.laraacostar .subtitle{font-size:22px}.laraacostar .proof{font-size:16px;gap:20px;margin-top:47px}.laraacostar .proof span+span{padding-left:20px}.laraacostar .cta{display:none}
    .laraacostar .hero-portrait{left:455px;right:auto;width:400px;mask-image:linear-gradient(to right,transparent,black 15%,black 85%,transparent)}
    .mattgray1:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#071e14b0,transparent 85%)}
    .mattgray1 .content{left:155px;right:480px;top:50px}.mattgray1 h1{font-family:DMSerifDisplay,Georgia,serif;font-size:43px;letter-spacing:-.4px;font-weight:400;line-height:1.2}.mattgray1 .subtitle{font-size:21px;max-width:780px}.mattgray1 .brand,.mattgray1 .proof,.mattgray1 .cta{display:none}.mattgray1 .hero-portrait{width:450px;z-index:2;mask-image:linear-gradient(90deg,transparent,black 25%)}
    .adrian-kul .brand{font-size:19px;font-weight:600;top:44px;left:54px}.adrian-kul .content{left:742px;right:55px;top:228px}.adrian-kul h1{font-size:36px;letter-spacing:-.8px;line-height:1.2;font-weight:600;margin-bottom:12px}.adrian-kul .line:last-child{color:var(--fg)}.adrian-kul .subtitle{font-size:19px;color:#656b64}.adrian-kul .proof,.adrian-kul .cta,.adrian-kul .hero-portrait{display:none}.quiet-form{position:absolute;width:770px;height:380px;right:-90px;top:-130px;border:1px solid #e9ebe7;border-radius:120px;transform:rotate(-18deg);box-shadow:0 0 0 7px #f8f9f6,0 0 0 9px #f0f2ee,0 0 40px #eef0eb}.quiet-mark{position:absolute;left:765px;top:95px;font-size:65px;font-weight:800;color:#111}
    .donnellychris .content{left:970px;right:45px;top:63px}.donnellychris h1{font-size:59px;letter-spacing:-2.5px;line-height:1.07;font-weight:580}.donnellychris .line:last-child{color:white}.donnellychris .subtitle{font-size:21px}.donnellychris .proof{font-size:14px;gap:18px;margin-top:28px}.donnellychris .proof span+span{padding-left:18px}.donnellychris .hero-portrait{display:none}.donnellychris .cta{position:absolute;left:-430px;top:220px;white-space:nowrap;background:#ffffff2d;border:1px solid #ffffff70;padding:13px 24px;border-radius:40px;font-size:20px;margin:0}.globe{position:absolute;left:230px;top:10px;width:890px;height:890px;border-radius:50%;background-image:radial-gradient(#fff8 1px,transparent 1.5px);background-size:7px 7px;mask-image:radial-gradient(ellipse,black 48%,transparent 70%)}.capability-icons{position:absolute;left:470px;top:59px;display:flex;gap:28px;color:white;font-size:120px;line-height:1.2}
    .rob-hoffman-ceo{background:radial-gradient(ellipse at 100% 8%,#6c850a,transparent 30%),radial-gradient(ellipse at 0% 100%,#475a0b,transparent 24%),#11140f}.rob-hoffman-ceo .content{left:605px;right:400px;top:65px}.rob-hoffman-ceo h1{font-size:51px;font-weight:550;letter-spacing:-2px}.rob-hoffman-ceo .subtitle{font-size:24px}.rob-hoffman-ceo .proof{font-size:16px;gap:20px;margin-top:38px}.rob-hoffman-ceo .proof span+span{padding-left:20px}.rob-hoffman-ceo .cta{display:none}.rob-hoffman-ceo .hero-portrait{width:350px;filter:grayscale(1);mix-blend-mode:normal}
    .jakezward{background:radial-gradient(ellipse at 94% 80%,#ffc3ae,transparent 32%),#fafaf7}.jakezward .content{left:440px;right:410px;top:80px}.jakezward h1{font-size:57px;font-weight:780;letter-spacing:-2.4px;line-height:1.05}.jakezward .line:last-child{font-style:italic}.jakezward .subtitle{font-size:22px;margin-left:90px}.jakezward .proof{margin-left:90px;margin-top:26px;font-size:15px;background:#ffffff99;border:1px solid #ced0ca;border-radius:40px;padding:17px 23px;gap:20px;white-space:nowrap}.jakezward .proof span+span{padding-left:20px}.jakezward .cta{display:none}.jakezward .hero-portrait{width:390px}.orbit{position:absolute;right:-130px;bottom:-330px;width:650px;height:650px;border:1px dotted #e5a593;border-radius:50%}.orbit-two{width:800px;height:800px;right:-200px;bottom:-410px}
    .charlie-hills{background-image:linear-gradient(#edf0f2 1px,transparent 1px),linear-gradient(90deg,#edf0f2 1px,transparent 1px);background-size:40px 40px}.charlie-hills .brand{font-size:23px}.charlie-hills .content{left:450px;right:480px;top:100px}.charlie-hills h1{font-size:56px;font-weight:750}.charlie-hills .subtitle{font-size:23px;margin-left:80px}.charlie-hills .proof,.charlie-hills .cta{display:none}.charlie-hills .hero-portrait{right:132px;bottom:74px;width:225px;height:225px;border-radius:50%;border:5px solid white;object-position:50% 35%;mask-image:none;box-shadow:0 8px 22px #135b9730}.topic{position:absolute;z-index:4;background:white;border:1px solid #dbe3eb;color:#0876d3;border-radius:40px;padding:12px 20px;font-size:14px;letter-spacing:1px;font-weight:750;box-shadow:0 3px 8px #174f8920}.topic-one{right:289px;top:61px}.topic-two{right:34px;top:170px}.topic-three{right:195px;bottom:45px}
    .liamkarlsson .content{left:480px;right:70px;top:64px}.liamkarlsson h1{font-family:Manrope,Arial,sans-serif;font-size:57px;line-height:1.08;font-weight:800;letter-spacing:-1.5px}.liamkarlsson .line:last-child{color:white}.liamkarlsson .subtitle{font-size:24px}.liamkarlsson .proof{margin-left:60px;font-size:18px;display:inline-flex;background:#082d77;border:1px solid #e4b96f70;padding:16px 25px;border-radius:8px;margin-top:30px}.liamkarlsson .cta,.liamkarlsson .hero-portrait{display:none}.liamkarlsson .content:before{content:'';position:absolute;inset:-30px -40px;background:#082d77b8;filter:blur(24px);z-index:-1}
    .systems{position:absolute;right:56px;top:81px;width:350px;display:flex;flex-direction:column;gap:15px}
    .system-row{display:flex;align-items:center;gap:20px;border-bottom:1px solid #c8d7e8;padding:13px 4px;font-size:23px;font-weight:620;color:#195178;letter-spacing:-.5px}
    .system-number{font-size:13px;letter-spacing:1px;color:#6b8eaa;font-weight:500}
    .banner .hero-portrait{top:12px;bottom:auto;height:470px;mask-image:none;object-fit:contain;object-position:50% 0%}
    /* Keep the banner readable as part of a 390px profile, not only at export size. */
    .banner .brand,.banner .proof,.banner .cta{display:none}
    .banner .subtitle{font-size:32px}
    .mattgray1 .content{top:35px}
    .mattgray1 h1{font-size:50px}
    .mattgray1 .subtitle{display:none}
    .adrian-kul .content{top:200px}
    .adrian-kul h1{font-size:44px}
    .adrian-kul .subtitle{color:#444b43}
    .evidence-card small{display:none}
    .evidence-card strong{font-size:30px;line-height:1.2}
    .evidence-cards{left:535px;width:320px}
    .evidence-card:nth-child(2),.evidence-card:nth-child(3){margin-left:0;margin-right:0}
    .donnellychris .subtitle{color:#301a09}
    .system-row{font-size:30px}
    .system-number{display:none}
    '''
    brand_override=''
    if palette:
        ink='#000000' if contrast('#000000',s['accent'])>=contrast('#ffffff',s['accent']) else '#ffffff'
        # Explicit overrides cover every reference-specific surface. Color roles
        # stay consistent even when a dark reference adopts a light website.
        brand_override=f'''<style id="brand-override">
        .banner{{background:var(--bg)!important;color:var(--fg)!important}}
        .banner .brand,.banner h1,.banner .subtitle,.banner .proof,.banner .cta{{color:var(--fg)!important}}
        .banner .line{{color:var(--fg)!important;background:transparent!important}}
        .banner .line:last-child{{color:var(--accent)!important}}
        .banner .proof,.banner .evidence-card,.banner .topic{{background:var(--bg)!important;color:var(--fg)!important;border-color:var(--accent)!important}}
        .banner .evidence-card small{{color:var(--fg)!important}}
        .banner .quiet-mark,.banner .capability-icons{{color:var(--accent)!important}}
        .banner .content:before{{background:var(--bg)!important}}
        .banner .waves g{{stroke:var(--accent)}}
        .banner .globe{{background-image:radial-gradient(var(--accent) 1px,transparent 1.5px)}}
        .banner .hero-portrait{{mix-blend-mode:normal}}
        .clarekitching .line:last-child{{background:var(--accent)!important;color:{ink}!important}}
        .clarekitching:after{{background:var(--accent)}}
        </style>'''
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}\n{styles}</style>{brand_override}</head><body><main class="banner {style}" style="--bg:{s["bg"]};--fg:{s["fg"]};--accent:{s["accent"]}">{bg}{extras}{body}</main></body></html>'


def preview_html(brief, banner_src, portrait_src, location='', mobile=False):
    width=390 if mobile else 848
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f3f2ef;color:#191919;font-family:Arial,sans-serif;width:{width}px}}
    .top{{height:56px;background:#fff;border-bottom:1px solid #ddd;display:flex;align-items:center;gap:12px;padding:0 32px;color:#626262;font-size:12px}}.in{{background:#0a66c2;color:white;font-size:27px;font-weight:bold;line-height:31px;padding:0 3px;border-radius:2px}}.search{{background:#edf3f8;padding:10px 16px;width:200px;border-radius:5px}}.nav{{margin-left:auto;word-spacing:22px}}
    .layout{{padding:24px 28px;display:flex;gap:24px}}.card{{width:792px;border:1px solid #dcdcdc;background:white;border-radius:10px;overflow:hidden;position:relative;flex-shrink:0}}
    .cover{{display:block;width:100%;height:198px;object-fit:cover}}.avatar{{position:absolute;left:24px;top:102px;width:160px;height:160px;border-radius:50%;border:4px solid white;object-fit:cover;background:white}}.info{{padding:94px 24px 24px}}h1{{margin:0 0 7px;font-size:26px;font-weight:600;letter-spacing:-.6px}}.headline{{font-size:16px;line-height:1.35;max-width:680px;margin:0 0 8px}}.location{{font-size:14px;color:#666;margin:0 0 20px}}.buttons{{display:flex;gap:8px}}button{{font-size:14px;font-weight:600;background:white;border:1px solid #777;border-radius:20px;padding:7px 18px;color:#444}}button:first-child{{background:#0a66c2;color:white;border-color:#0a66c2}}.side{{width:220px;height:130px;background:white;border:1px solid #ddd;border-radius:10px;padding:20px;line-height:1.5;color:#666;font-size:13px}}.note{{padding:0 32px 24px;font-size:12px;color:#686868}}
    {'.layout{padding:12px 0}.card{width:390px;border-radius:0;border-left:0;border-right:0}.cover{height:97.5px}.avatar{width:112px;height:112px;left:16px;top:40px}.info{padding:69px 16px 22px}h1{font-size:24px}.headline{font-size:15px}.side,.nav,.search{display:none}.top{height:48px;padding:0 16px}.note{padding:0 16px 16px}' if mobile else ''}
    </style></head><body><div class="top"><span class="in">in</span><span class="search">Search</span><span class="nav">Home Network Jobs Messaging</span></div><div class="layout"><main class="card"><img class="cover" src="{esc(banner_src)}"><img class="avatar" src="{esc(portrait_src)}"><div class="info"><h1>{esc(brief['name'])}</h1><p class="headline">{esc(brief['headline'])}</p><p class="location">{esc(location)}</p><div class="buttons"><button>Message</button><button>Connect</button><button>More</button></div></div></main></div><div class="note">Layout preview · simulated LinkedIn profile · final crop can vary by device</div></body></html>'''


def check_images(output, brief):
    failures=[]; assets={}
    for filename, expected in [('banner.png',(3168,792)),('portrait.png',(800,800)),('preview.png',None)]:
        path=Path(output)/filename
        if not path.exists():
            failures.append(f'Missing {filename}');continue
        try:
            with Image.open(path) as img:
                assets[filename]={'dimensions':list(img.size),'bytes':path.stat().st_size,'format':img.format}
                if expected and img.size!=expected: failures.append(f'{filename}: incorrect dimensions')
                if path.stat().st_size>=8_000_000: failures.append(f'{filename}: exceeds 8 MB')
        except OSError: failures.append(f'{filename}: invalid image')
    if len(brief['headline'])>220: failures.append('Headline exceeds 220 characters')
    return {'passed':not failures,'failures':failures,'assets':assets,'headline_characters':len(brief['headline'])}


def mobile_portrait_overlap(box):
    """Circle from the 390px preview, mapped into the 1584px banner coordinate space."""
    scale=1584/390
    cx,cy,r=72*scale,96*scale,56*scale
    x=max(box['x'],min(cx,box['x']+box['width']))
    y=max(box['y'],min(cy,box['y']+box['height']))
    return (x-cx)**2+(y-cy)**2<r*r


def text_regions_overlap(first,second):
    """Independent text groups must not intersect, even when each fits the canvas."""
    width=min(first['x']+first['width'],second['x']+second['width'])-max(first['x'],second['x'])
    height=min(first['y']+first['height'],second['y']+second['height'])-max(first['y'],second['y'])
    return width>1 and height>1


def measure_design_details(page):
    """Measure text ink, highlight paint and edge space in the actual browser.

    Canvas font metrics refine DOM Range line boxes: a serif's descender can
    paint below its CSS line-height. This is a conservative geometry audit,
    not an assertion that a font size alone establishes visual readability.
    """
    return page.evaluate('''() => {
      const banner=document.querySelector('.banner');
      if(!banner)return {status:'missing_canvas',reason:'Missing banner canvas; typography cannot be audited.',text:[],title_lines:[],cards:[],logos:[]};
      const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
      const box=r=>({x:r.x,y:r.y,width:r.width,height:r.height});
      const union=rects=>{const x=Math.min(...rects.map(r=>r.x)),y=Math.min(...rects.map(r=>r.y));return {x,y,width:Math.max(...rects.map(r=>r.x+r.width))-x,height:Math.max(...rects.map(r=>r.y+r.height))-y};};
      const visible=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&parseFloat(s.opacity)!==0&&e.getClientRects().length;};
      const painted=e=>{const s=getComputedStyle(e);return s.backgroundImage!=='none'||!['rgba(0, 0, 0, 0)','transparent'].includes(s.backgroundColor);};
      function metrics(e,text,r){
        const s=getComputedStyle(e),size=parseFloat(s.fontSize);
        ctx.font=[s.fontStyle,s.fontWeight,s.fontSize,s.fontFamily].join(' ');
        if('letterSpacing' in ctx)ctx.letterSpacing=s.letterSpacing==='normal'?'0px':s.letterSpacing;
        const m=ctx.measureText(text),baseline=r.y+(m.fontBoundingBoxAscent??size*.8);
        return {text,font_family:s.fontFamily,font_size:size,line_height:s.lineHeight==='normal'?null:parseFloat(s.lineHeight),letter_spacing:s.letterSpacing==='normal'?0:parseFloat(s.letterSpacing),
          desktop_font_px:size*.5,mobile_font_px:size*390/1584,box:box(r),
          ink:{x:r.x,y:baseline-m.actualBoundingBoxAscent,width:r.width,height:m.actualBoundingBoxAscent+m.actualBoundingBoxDescent}};
      }
      const titleElements=[...banner.querySelectorAll('h1 .line')].filter(visible);
      const text=[],walker=document.createTreeWalker(banner,NodeFilter.SHOW_TEXT);
      while(walker.nextNode()){
        const node=walker.currentNode,e=node.parentElement,value=node.textContent.trim();
        if(!value||!visible(e)||e.closest('svg,script,style,[aria-hidden="true"]'))continue;
        const range=document.createRange();range.selectNodeContents(node);
        const rects=[...range.getClientRects()].filter(r=>r.width&&r.height);
        const lineIndex=titleElements.indexOf(e.closest('h1 .line'));
        const clipping_ancestors=[];
        for(let ancestor=e;ancestor&&ancestor!==banner;ancestor=ancestor.parentElement){
          const s=getComputedStyle(ancestor),clip_x=['hidden','clip','scroll','auto'].includes(s.overflowX),clip_y=['hidden','clip','scroll','auto'].includes(s.overflowY);
          if(!clip_x&&!clip_y)continue;
          const r=ancestor.getBoundingClientRect();
          clipping_ancestors.push({element:ancestor.className||ancestor.tagName.toLowerCase(),x:r.x+ancestor.clientLeft,y:r.y+ancestor.clientTop,width:ancestor.clientWidth,height:ancestor.clientHeight,clip_x,clip_y});
        }
        for(const r of rects)text.push({...metrics(e,value,r),kind:e.closest('h1')&&!e.closest('.metric-caption')?'headline':'support',element:e.className||e.tagName.toLowerCase(),title_line_index:lineIndex>=0?lineIndex:null,clipping_ancestors});
      }
      const title_lines=titleElements.map((e,index)=>{
        const parts=text.filter(item=>item.title_line_index===index);
        const surfaces=[e,...e.querySelectorAll('*')].filter(node=>visible(node)&&painted(node));
        return {text:e.innerText,index,box:box(e.getBoundingClientRect()),ink:parts.length?union(parts.map(item=>item.ink)):null,
          glyph_parts:parts.map(({text,kind,font_size,ink})=>({text,kind,font_size,ink})),paint:surfaces.map(node=>box(node.getBoundingClientRect()))};
      }).filter(item=>item.ink);
      const cards=[...banner.querySelectorAll('.proof-card')].filter(visible).map(e=>({text:e.innerText,box:box(e.getBoundingClientRect())}));
      const logos=[...banner.querySelectorAll('.company-logo')].filter(visible).map(e=>{const s=getComputedStyle(e);return {label:e.getAttribute('alt')||e.getAttribute('aria-label')||'',box:box(e.getBoundingClientRect()),background:s.backgroundColor,padding:[s.paddingTop,s.paddingRight,s.paddingBottom,s.paddingLeft].map(parseFloat),border_radius:s.borderRadius};});
      const content=banner.querySelector('.content'),proof=banner.querySelector('.proof-grid');
      let content_proof=null;
      if(content&&proof&&visible(content)&&visible(proof)){
        const children=[...content.children].filter(visible).map(e=>({element:e.className||e.tagName.toLowerCase(),box:box(e.getBoundingClientRect())}));
        for(const node of content.childNodes){
          if(node.nodeType!==Node.TEXT_NODE||!node.textContent.trim())continue;
          const range=document.createRange();range.selectNodeContents(node);
          children.push({element:'direct text',box:box(range.getBoundingClientRect())});
        }
        content_proof={content:box(content.getBoundingClientRect()),children,proof:box(proof.getBoundingClientRect())};
      }
      return {status:'measured',layout_mode:banner.classList.contains('evidence-layout')?'modern':'legacy',canvas:{width:1584,height:396},text,title_lines,cards,logos,content_proof};
    }''')


def audit_design_details(report):
    """Reject mechanically unsafe detail while preserving measured evidence."""
    report=dict(report);report['failures']=[]
    if report['status']=='missing_canvas':
        report['status']='failed';report['failures'].append('Missing banner canvas; cannot approve typography.')
        return report
    thresholds={'support_font_px':48,'headline_font_px':56,'edge_clearance_px':32,'headline_clearance_px':12,'headline_column_clearance_px':24,'content_proof_gap_px':12}
    report['thresholds']=thresholds
    failures=report['failures']
    def edges(rect):
        return {'left':rect['x'],'top':rect['y'],'right':1584-rect['x']-rect['width'],'bottom':396-rect['y']-rect['height']}
    for item in report['text']:
        minimum=thresholds['headline_font_px' if item['kind']=='headline' else 'support_font_px']
        if item['font_size']<minimum-.1:
            failures.append(f'Text below minimum ({item["font_size"]:g}px < {minimum}px): {item["text"][:100]}')
        item['edge_clearance']=edges(item['ink'])
        if min(item['edge_clearance'].values())<thresholds['edge_clearance_px']-.5:
            failures.append(f'Text edge clearance below {thresholds["edge_clearance_px"]}px: {item["text"][:100]}')
    collisions=[]
    for index,first in enumerate(report['text']):
        for other_index,second in enumerate(report['text'][index+1:],start=index+1):
            if text_regions_overlap(first['ink'],second['ink']):
                collisions.append({'first_text_index':index,'second_text_index':other_index})
                failures.append(f'Text ink overlap: {first["text"][:80]} / {second["text"][:80]}')
    report['text_ink_collisions']=collisions
    for item in report['cards']:
        item['edge_clearance']=edges(item['box'])
        if min(item['edge_clearance'].values())<thresholds['edge_clearance_px']-.5:
            failures.append(f'Card edge clearance below {thresholds["edge_clearance_px"]}px: {item["text"][:100]}')
    for item in report['logos']:
        rect=item['box'];item['edge_clearance']=edges(rect)
        if min(item['edge_clearance'].values())<-.5:
            failures.append(f'Logo outside banner: {item["label"]}')
        elif min(item['edge_clearance'].values())<thresholds['edge_clearance_px']-.5:
            failures.append(f'Logo edge clearance below {thresholds["edge_clearance_px"]}px: {item["label"]}')
        item['desktop_portrait_overlap']=rect['x']<428 and rect['y']+rect['height']>178
        item['mobile_portrait_overlap']=mobile_portrait_overlap(rect)
        if item['desktop_portrait_overlap']:
            failures.append(f'Logo enters desktop portrait exclusion zone: {item["label"]}')
        if item['mobile_portrait_overlap']:
            failures.append(f'Logo overlaps mobile portrait: {item["label"]}')
    lines=report['title_lines'];gaps=[]
    for first,second in zip(lines,lines[1:]):
        first_surfaces=[first['ink'],*first['paint']]
        second_surfaces=[second['ink'],*second['paint']]
        first_left=min(r['x'] for r in first_surfaces);first_right=max(r['x']+r['width'] for r in first_surfaces)
        second_left=min(r['x'] for r in second_surfaces);second_right=max(r['x']+r['width'] for r in second_surfaces)
        columns_overlap=min(first_right,second_right)>max(first_left,second_left)+1
        if columns_overlap:
            first_bottom=max(r['y']+r['height'] for r in first_surfaces)
            second_top=min(r['y'] for r in second_surfaces)
            clearance=second_top-first_bottom
            axis='vertical';minimum=thresholds['headline_clearance_px']
        else:
            clearance=max(first_left,second_left)-min(first_right,second_right)
            axis='horizontal';minimum=thresholds['headline_column_clearance_px']
        gaps.append({'after_line':first['index'],'before_line':second['index'],'axis':axis,'clearance':clearance})
        if clearance<-.5:
            failures.append(f'Headline ink/background overlap: {first["text"]} / {second["text"]} ({-clearance:.1f}px)')
        elif clearance<minimum-.5:
            failures.append(f'Headline {"column" if axis=="horizontal" else "line"} clearance below {minimum}px: {first["text"]} / {second["text"]} ({clearance:.1f}px)')
    report['title_line_gaps']=gaps
    groups=report.get('content_proof')
    if groups:
        pairs=[]
        for child in groups['children']:
            first,second=child['box'],groups['proof']
            columns_overlap=min(first['x']+first['width'],second['x']+second['width'])>max(first['x'],second['x'])+1
            above,below=sorted((first,second),key=lambda r:r['y'])
            clearance=below['y']-above['y']-above['height'] if columns_overlap else None
            pairs.append({'element':child['element'],'columns_overlap':columns_overlap,'clearance':clearance})
            if columns_overlap and clearance<thresholds['content_proof_gap_px']-.5:
                failures.append(f'Content/proof separation below {thresholds["content_proof_gap_px"]}px for {child["element"]} ({clearance:.1f}px)')
        applicable=[pair['clearance'] for pair in pairs if pair['columns_overlap']]
        report['content_proof_gap']={'columns_overlap':bool(applicable),'clearance':min(applicable) if applicable else None,'pairs':pairs}
    report['status']='passed' if not failures else 'failed'
    report['limitations']='Geometry and scaled font sizes do not establish optical balance, logo fidelity, contrast over imagery or actual reading comfort. Inspect the full-size desktop/mobile screenshots.'
    return report


def render_package(brief, portrait_path, output, *, style=None, location='', background_path=None, banner_photo_path=None):
    """Do not leave the local preview permanently busy after a render error."""
    try:
        return _render_package(brief, portrait_path, output, style=style, location=location,
                               background_path=background_path, banner_photo_path=banner_photo_path)
    except (Exception, KeyboardInterrupt):
        qa_path = Path(output) / 'qa.json'
        try:
            qa = json.loads(qa_path.read_text())
            if qa.get('acceptance') == 'render_in_progress':
                write_json(qa_path, {'passed': False, 'acceptance': 'render_failed',
                                     'visual_review': 'required',
                                     'failures': ['Rendering did not complete. Ask the agent to fix the inputs and rerender.']})
        except (OSError, ValueError, AttributeError):
            pass
        raise


def _render_package(brief, portrait_path, output, *, style=None, location='', background_path=None, banner_photo_path=None):
    from playwright.sync_api import sync_playwright
    validate_brief(brief)
    style=style or brief['selected_style']; output=Path(output)
    assets={'banner_photo':None,'combined_profile_review':'required'}
    if style in BANNER_PHOTO_STYLES:
        if banner_photo_path is None:
            raise ValueError('This layout requires a separate banner photograph; the profile portrait is never reused.')
        assets=validate_photo_pair(portrait_path,banner_photo_path)
        if not has_transparent_background(banner_photo_path):
            raise ValueError('Banner photograph needs a transparent cutout; opaque photo panels are not accepted in this layout.')
    elif banner_photo_path is not None:
        raise ValueError('This layout uses no banner photograph; do not supply a second portrait.')
    output.mkdir(parents=True,exist_ok=True)
    # Invalidate acceptance before replacing any deliverable.
    write_json(output/'qa.json',{'passed':False,'acceptance':'render_in_progress','visual_review':'required'})
    (output/'blind-review.json').unlink(missing_ok=True)
    write_json(output/'visual-assets.json',assets)
    # Resize/crop only; no identity alteration. Kie performs the creative edit.
    with Image.open(portrait_path) as im:
        ImageOps.fit(ImageOps.exif_transpose(im).convert('RGB'),(800,800),method=Image.Resampling.LANCZOS).save(output/'portrait.png',optimize=True)
    (output/'banner.html').write_text(banner_html(brief,style,banner_photo_path,background_path,asset_root=output),encoding='utf-8')
    (output/'headline.txt').write_text(brief['headline']+'\n',encoding='utf-8')
    write_json(output/'brief.json',brief)
    geometry=[]
    company_brand_typography=None
    brand_network_requests=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1584,'height':396},device_scale_factor=2)
        if brief.get('company_brand'):
            from .company_brand import block_brand_network
            block_brand_network(page.context,brand_network_requests)
        page.goto((output/'banner.html').resolve().as_uri());page.evaluate('document.fonts.ready')
        # No layout rescues overlong copy by shrinking it to legend size.
        # Copy that cannot fit at the headline floor must be revised.
        if brief.get('layout_mode')!='reference-faithful':
            page.evaluate('''() => { const minimum=56;for (const el of document.querySelectorAll('h1')) { let n=parseFloat(getComputedStyle(el).fontSize); while(el.scrollWidth>el.clientWidth+1 && n>minimum){n=Math.max(minimum,n-.5);el.style.fontSize=n+'px';} } }''')
        geometry=page.locator('[data-qa="essential"]').evaluate_all('''els=>els.filter(e=>getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().width).map(e=>{const r=e.getBoundingClientRect();return {text:e.innerText,x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,fontSize:parseFloat(getComputedStyle(e).fontSize)}})''')
        if brief.get('layout_mode')=='reference-faithful':
            from .reference_qa import measure_reference_design
            design_details=measure_reference_design(page,brief['selected_style'])
        else:
            design_details=audit_design_details(measure_design_details(page))
        if brief.get('company_brand'):
            from .company_brand import load_brand, audit_brand_typography
            brand,_=load_brand(output,brief['company_brand'])
            company_brand_typography=audit_brand_typography(page,brand,design_details)
        # Persist final fitted typography, so editable HTML matches the delivered PNG.
        (output/'banner.html').write_text(page.content(),encoding='utf-8')
        page.screenshot(path=str(output/'banner.png'))
        page.close()
        for mobile in [False,True]:
            filename='preview-mobile' if mobile else 'preview'
            source=preview_html(brief,'banner.png','portrait.png',location,mobile)
            (output/f'{filename}.html').write_text(source,encoding='utf-8')
            page=browser.new_page(viewport={'width':390 if mobile else 848,'height':680},device_scale_factor=2 if mobile else 1)
            if brief.get('company_brand'):
                block_brand_network(page.context,brand_network_requests)
            page.goto((output/f'{filename}.html').resolve().as_uri())
            page.locator('img').evaluate_all('els=>Promise.all(els.map(e=>e.decode()))')
            page.locator('body').screenshot(path=str(output/f'{filename}.png'))
            # Neutral reviewer inputs use actual CSS display pixels. Enlarged
            # retina exports can make small mobile labels look falsely easy.
            page.locator('.card').screenshot(path=str(output/('review-mobile.png' if mobile else 'review-desktop.png')),scale='css')
            page.close()
        browser.close()
    qa=check_images(output,brief);qa['geometry']=geometry
    qa['design_details']=design_details
    qa['failures'].extend(design_details['failures'])
    if company_brand_typography is not None:
        from .company_brand import brand_record
        qa['company_brand']=brand_record(output,brief['company_brand'])
        qa['company_brand_typography']=company_brand_typography
        qa['failures'].extend(company_brand_typography['failures'])
        qa['company_brand_network']={'status':'failed' if brand_network_requests else 'passed','blocked_requests':brand_network_requests}
        qa['failures'].extend(f'Company brand render attempted a non-local asset: {url}' for url in brand_network_requests)
    for box in geometry:
        if box['x']<0 or box['y']<0 or box['x']+box['width']>1585 or box['y']+box['height']>397:
            qa['failures'].append(f'Text outside banner: {box["text"]}')
        if box['scrollWidth']>box['clientWidth']+2:
            qa['failures'].append(f'Text overflow: {box["text"]}')
        # Conservative desktop safe area. Mobile gets separate visual inspection.
        if brief.get('layout_mode')!='reference-faithful' and box['x']<428 and box['y']+box['height']>178:
            qa['failures'].append(f'Text enters portrait exclusion zone: {box["text"]}')
        if brief.get('layout_mode')!='reference-faithful' and mobile_portrait_overlap(box):
            qa['failures'].append(f'Text overlaps mobile portrait: {box["text"]}')
    for index,first in enumerate(geometry):
        for second in geometry[index+1:]:
            if text_regions_overlap(first,second):
                qa['failures'].append(f'Overlapping text groups: {first["text"][:90]} / {second["text"][:90]}')
    qa['passed']=not qa['failures'];qa['visual_review']='required';qa['style']=style
    qa['photo_roles']=assets
    qa['acceptance']='awaiting_blind_combined_profile_review'
    from .review import PACKAGE_FILES
    qa['render_sha256']={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in PACKAGE_FILES}
    if brief.get('layout_mode')=='reference-faithful':
        qa['input_sha256']={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in ('brief.json','banner.html')}
        reference=ROOT/'references'/style
        qa['reference_source_sha256']={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in (reference/'banner.jpg',reference/'headline.txt',*reference.glob('portrait.*')) if path.is_file()}
    write_json(output/'qa.json',qa)
    return qa
