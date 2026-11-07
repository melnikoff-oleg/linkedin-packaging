"""Reference-led, optically spaced compositions with readable source-backed proof.

All dimensions are 1584×396 design pixels. Typography QA measures the actual
font ink, not just CSS line boxes. Transparent original marks have no plaques.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import re
from PIL import Image
from .visual_assets import BANNER_PHOTO_STYLES


def _readable_wordmark(root, key, path):
    """Transparency is not proof of a legible brand name: require attestation."""
    try:
        records=json.loads((root/'logos/provenance.json').read_text())
        record=records.get(key,{})
        return (isinstance(record,dict) and record.get('readable_wordmark') is True and
                record.get('sha256')==hashlib.sha256(path.read_bytes()).hexdigest())
    except (OSError,ValueError,AttributeError,TypeError):
        return False


def evidence_banner_html(brief, style, palette, banner_photo=None, background=None, asset_root=None):
    from .render import esc, data_uri, font_css, wave_svg, contrast
    root=Path(asset_root or '.').resolve()
    logos={}
    for key,relative in brief.get('logo_assets',{}).items():
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',str(key)) or relative!=f'logos/{key}.png':
            raise ValueError('Logo paths must remain within package logos/<company_id>.png.')
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Original company logo is missing from this package.')
        with Image.open(path) as original:
            im=original.convert('RGBA')
            transparent=im.getchannel('A').getextrema()[0]<16
            # An opaque social avatar is not a prepared logo. Retain its named
            # identity below; blending or guessing its background makes plaques.
            if not transparent:continue
            bounds=im.getchannel('A').getbbox()
            if bounds:im=im.crop(bounds)  # Empty canvas only; original mark unchanged.
            aspect=im.width/im.height
            clip_right=0
            readable_wordmark=transparent and _readable_wordmark(root,key,path)
            if readable_wordmark:
                record=json.loads((root/'logos/provenance.json').read_text()).get(key,{})
                clip=record.get('display_clip_right_fraction',0)
                if type(clip) in (int,float) and 0<=clip<=.08:
                    clip_right=clip*100
            # Optical presets preserve exact aspect ratios. Broad wordmarks need
            # width, stacked lettering needs height; neither gets a white tile.
            height=60 if aspect>5 else 100
            width=min(400,aspect*height)
            if key=='1009':height=72;width=aspect*height
            if key=='forevercar':width=580
            height=width/aspect
            if not readable_wordmark:width=height=64
            buffer=io.BytesIO();im.save(buffer,format='PNG')
            logos[key]={'uri':'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode(),
                        'transparent':transparent,'readable_wordmark':readable_wordmark,'clip_right':clip_right,'width':width,'height':height}
    cards=[]
    for card in brief['proof_cards']:
        key=card['company_id'] or re.sub(r'[^a-z0-9]','',card['company'].lower())
        logo=logos.get(key)
        symbol_size=';width:64px;height:64px' if logo and not logo['readable_wordmark'] else ''
        clip_style=f';clip-path:inset(0 {logo["clip_right"]:.6f}% 0 0)' if logo and logo['clip_right'] else ''
        mark=(f'<img class="company-logo {"transparent" if logo["transparent"] else "opaque"}" data-logo-key="{esc(key)}" '
              f'data-readable-wordmark="{str(logo["readable_wordmark"]).lower()}" style="--logo-w:{logo["width"]:.2f}px;--logo-h:{logo["height"]:.2f}px{symbol_size}{clip_style}" src="{logo["uri"]}" alt="{esc(card["company"])}">') if logo else ''
        name=f'<div class="company-name">{esc(card["company"])}</div>' if not logo or not logo['readable_wordmark'] or style=='jakezward' else ''
        role=f'<div class="company-role">{esc(card["role"])}</div>' if card['role'].strip() else ''
        info=f'<div class="company-info">{name}{role}</div>' if name or role else ''
        detail=f'<div class="card-detail">{esc(card["detail"])}</div>' if card['detail'].strip() else ''
        cards.append(f'<section class="proof-card" data-qa="essential"><div class="company-row">{mark}{info}</div><div class="card-value">{esc(card["value"])}</div>{detail}</section>')
    lines=[]
    metric_layout=style=='donnellychris' and all(re.match(r'^\s*[~≈<>+]?\d+(?:\.\d+)?%',line) for line in brief['banner_title'].split('\n')) and len(brief['banner_title'].split('\n'))==2
    for index,line in enumerate(brief['banner_title'].split('\n')):
        if metric_layout:
            match=re.match(r'^\s*([~≈<>+]?\d+(?:\.\d+)?%)(.*)',line)
            text=f'<span class="metric">{esc(match[1])}</span><span class="metric-caption">{esc(match[2].strip().rstrip("."))}</span>'
        else:text=esc(line)
        lines.append(f'<span class="line line-{index}">{text}</span>')
    title=''.join(lines)
    photo=f'<img class="hero-portrait" src="{data_uri(banner_photo,trim_alpha=True)}" alt="">' if banner_photo and style in BANNER_PHOTO_STYLES else ''
    scenery=f'<img class="landscape" src="{data_uri(background)}" alt="">' if background else ''
    decor=wave_svg() if style=='liamkarlsson' else '<div class="decor" aria-hidden="true"></div>'
    if style=='jakezward':decor+='<div class="orbit"></div><div class="orbit second"></div>'
    css='''
    *{box-sizing:border-box}html,body{margin:0;width:1584px;height:396px;overflow:hidden}
    .banner{position:relative;width:1584px;height:396px;overflow:hidden;background:var(--bg);color:var(--fg);font-family:Inter,Arial,sans-serif;--logo-filter:brightness(0) invert(1)}
    .content{position:absolute;left:540px;right:48px;top:28px;z-index:3}
    h1{display:grid;row-gap:14px;font-size:64px;line-height:1.12;letter-spacing:-1px;margin:0 0 14px;font-weight:720}
    .line{display:block;width:max-content;max-width:100%;white-space:nowrap}
    .line:last-child{color:var(--accent)}
    .subtitle{font-size:48px;line-height:1.2;letter-spacing:-.4px;white-space:pre-line}
    .proof-grid{position:absolute;left:540px;right:48px;bottom:40px;display:grid;grid-template-columns:1fr;z-index:4}
    .proof-card{position:relative;min-width:0;display:flex;align-items:center;gap:32px}
    .company-row{display:flex;align-items:center;gap:24px;min-width:0}
    .company-logo{display:block;flex:none;width:var(--logo-w);height:var(--logo-h);object-fit:contain;filter:var(--logo-filter);background:none;border:0;padding:0;border-radius:0}
    .company-name,.company-role{font-size:48px;line-height:1.15;letter-spacing:-.4px;white-space:pre-line}
    .company-name{font-weight:650}
    .card-value,.card-detail{font-size:48px;line-height:1.2;letter-spacing:-.4px;white-space:pre-line}
    .card-value{font-weight:500}
    .hero-portrait{position:absolute;top:16px;right:24px;width:330px;height:430px;object-fit:contain;object-position:center top;z-index:2}
    .landscape{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
    .waves{position:absolute;inset:0;width:100%;height:100%;opacity:.5;z-index:0}
    .clarekitching{background-image:linear-gradient(#ffffff05 1px,transparent 1px),linear-gradient(90deg,#ffffff05 1px,transparent 1px);background-size:80px 80px}
    .clarekitching:after{content:'';position:absolute;bottom:0;width:100%;height:12px;background:linear-gradient(90deg,#ffc493 28%,#70c4c1 28% 64%,#06585b 64%)}
    .clarekitching .content{top:24px}
    .clarekitching h1{font-family:DMSerifDisplay,Georgia,serif;font-size:60px;font-weight:400;letter-spacing:-.6px;line-height:1.16;row-gap:16px;margin-bottom:10px}
    .clarekitching .line:last-child{color:#003b3d;background:var(--accent);font-style:italic;padding:0 14px 3px;margin-left:-14px}
    .clarekitching .proof-grid:before{content:'';position:absolute;inset:-18px -48px -28px -30px;background:linear-gradient(180deg,#06484b00,#06484b 36px);clip-path:polygon(3% 0,100% 0,100% 100%,0 100%);z-index:-1}
    .diandraescobar{background:radial-gradient(ellipse at 48% 68%,#306660,transparent 56%),var(--bg)}
    .diandraescobar .content{left:1180px;right:48px;top:64px}
    .diandraescobar h1{font-size:60px;letter-spacing:-.8px;line-height:1.13;row-gap:14px;margin-bottom:24px}
    .diandraescobar .subtitle{font-size:48px;line-height:1.2}
    .diandraescobar .hero-portrait{left:912px;right:auto;width:250px;height:425px;top:24px}
    .diandraescobar .proof-grid{left:520px;right:auto;top:108px;bottom:auto;width:380px}
    .diandraescobar .proof-card{padding:24px 18px;flex-direction:column;align-items:flex-start;gap:20px;background:#f5f8f4;color:#113b36;border-radius:16px;box-shadow:0 6px 20px #00181920;--logo-filter:brightness(0)}
    .diandraescobar .company-logo{width:344px;height:48px}
    .laraacostar{background:radial-gradient(ellipse at 40% 62%,#6b3026,transparent 44%),linear-gradient(135deg,#080808,#191919)}
    .laraacostar .hero-portrait{left:455px;right:auto;width:345px;height:430px;top:16px}
    .laraacostar .content{left:836px;right:48px;top:36px}
    .laraacostar h1{font-size:60px;line-height:1.15;letter-spacing:-.8px;margin-bottom:18px}
    .laraacostar .proof-grid{left:836px;right:48px}
    .laraacostar .proof-grid:before{content:'';position:absolute;inset:-20px -48px -40px -40px;background:#151615;z-index:-1;border-top:1px solid #ffffff1a}
    .mattgray1:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#061d15d0 0%,#061d15c0 74%,#061d1530 91%)}
    .mattgray1 .content{left:160px;right:400px;top:44px}
    .mattgray1 h1{font-family:DMSerifDisplay,Georgia,serif;font-size:60px;line-height:1.16;font-weight:400;letter-spacing:-.3px;margin-bottom:22px}
    .mattgray1 .subtitle{margin-left:380px;padding-left:20px;border-left:3px solid var(--accent)}
    .mattgray1 .hero-portrait{right:24px;top:24px;width:310px;height:415px}
    .mattgray1 .proof-grid{right:400px}
    .mattgray1 .proof-card{flex-direction:column;align-items:flex-start;gap:16px}
    .adrian-kul{--logo-filter:brightness(0)}
    .adrian-kul .decor{position:absolute;width:1000px;height:330px;right:-180px;top:-200px;border:1px solid #e6e9e4;border-radius:100px;transform:rotate(-17deg);box-shadow:0 0 0 8px #f8f9f6,0 0 0 10px #eef1ec}
    .adrian-kul .content{left:620px;top:40px}
    .adrian-kul h1{font-size:60px;line-height:1.14;font-weight:620;letter-spacing:-.9px}
    .adrian-kul .line:last-child{color:var(--fg)}
    .adrian-kul .subtitle{color:#344138}
    .adrian-kul .proof-grid{left:620px;bottom:44px}
    .adrian-kul .proof-card{border-top:1px solid #bdc9be;padding-top:16px}
    .donnellychris{--logo-filter:brightness(0)}
    .donnellychris .decor{position:absolute;left:240px;top:-90px;width:850px;height:850px;border-radius:50%;background-image:radial-gradient(#ffffff35 1px,transparent 1.5px);background-size:8px 8px;mask-image:linear-gradient(90deg,black,transparent 80%)}
    .donnellychris .content{left:540px;top:48px}
    .donnellychris h1{font-size:64px;line-height:1.14;letter-spacing:-1px}
    .donnellychris .line:last-child{color:white}
    .donnellychris.metric-layout h1{grid-template-columns:1fr 1fr;column-gap:40px;width:620px;margin:0}
    .donnellychris.metric-layout .line{width:100%;white-space:normal;display:flex;flex-direction:column;gap:18px}
    .donnellychris .metric{font-size:104px;line-height:1;letter-spacing:-2.5px;font-weight:760;color:white}
    .donnellychris .metric-caption{font-size:48px;line-height:1.15;letter-spacing:-.4px;color:#301d10;font-weight:600;max-width:290px}
    .donnellychris.metric-layout .subtitle{position:absolute;left:660px;top:0;width:336px;color:#301d10;font-size:48px;line-height:1.15}
    .donnellychris .proof-grid{left:1200px;right:48px;top:184px;bottom:auto}
    .donnellychris .proof-card{flex-direction:column;align-items:flex-start;gap:18px;color:#301d10}
    .donnellychris .proof-grid:before{content:'';position:absolute;inset:-12px -16px;background:#ffd5b9;border-radius:18px;z-index:-1}
    .rob-hoffman-ceo{background:radial-gradient(ellipse at 95% 12%,#52650d,transparent 30%),radial-gradient(ellipse at 0% 100%,#324108,transparent 25%),var(--bg)}
    .rob-hoffman-ceo .content{right:390px;top:32px}
    .rob-hoffman-ceo h1{font-size:60px;line-height:1.14;letter-spacing:-.7px}
    .rob-hoffman-ceo .proof-grid{right:390px}
    .rob-hoffman-ceo .proof-card{flex-direction:column;align-items:flex-start;gap:20px}
    .rob-hoffman-ceo .hero-portrait{width:360px;height:480px;top:-24px;right:8px;filter:grayscale(1)}
    .jakezward{background:radial-gradient(ellipse at 100% 90%,#ffe1d4,transparent 40%),var(--bg);--logo-filter:brightness(0)}
    .jakezward .content{left:540px;right:390px;top:28px}
    .jakezward h1{font-size:60px;line-height:1.14;letter-spacing:-.8px;row-gap:14px;margin-bottom:12px}
    .jakezward .line:last-child{font-style:italic;color:#a93422}
    .jakezward .hero-portrait{width:330px;right:16px}
    .jakezward .proof-grid{left:540px;right:390px}
    .jakezward .proof-card{gap:24px;border:1px solid #d7d7cf;background:#fffdf9;padding:16px 20px;border-radius:55px}
    .jakezward .company-logo{position:fixed;left:64px;top:40px;width:160px;height:100px}
    .orbit{position:absolute;right:-240px;bottom:-390px;width:740px;height:740px;border:1px dotted #e4b6a6;border-radius:50%;mask-image:linear-gradient(90deg,transparent,black 55%)}
    .orbit.second{width:890px;height:890px;right:-310px;bottom:-465px}
    .charlie-hills{background-image:linear-gradient(#eef3f7 1px,transparent 1px),linear-gradient(90deg,#eef3f7 1px,transparent 1px);background-size:40px 40px;--logo-filter:brightness(0)}
    .charlie-hills .content{left:520px;right:600px;top:40px}
    .charlie-hills h1{font-size:64px;letter-spacing:-.8px;line-height:1.14}
    .charlie-hills .subtitle{font-size:48px;line-height:1.2}
    .charlie-hills .proof-grid{left:1040px;right:48px;top:48px;bottom:auto}
    .charlie-hills .proof-card{flex-direction:column;align-items:flex-start;gap:24px}
    .charlie-hills .company-row{flex-direction:column;align-items:flex-start;gap:16px}
    .charlie-hills .card-value{font-size:48px;line-height:1.2;color:#0862a1}
    .liamkarlsson .content{top:32px}
    .liamkarlsson h1{font-family:Manrope,Arial,sans-serif;font-size:64px;line-height:1.14;letter-spacing:-1px;font-weight:760;margin-bottom:12px}
    .liamkarlsson .line:last-child{color:white}
    .liamkarlsson .waves{opacity:.32;mask-image:linear-gradient(90deg,black,transparent 60%)}
    .liamkarlsson .proof-grid:before{content:'';position:absolute;inset:-18px -24px;background:#092d74;border:1px solid #d7b47899;border-radius:12px;z-index:-1}
    '''
    proof_grid=f'<div class="proof-grid">{"".join(cards)}</div>' if cards else ''
    overrides=''
    if brief.get('brand_palette'):
        light=contrast('#000000',palette['bg'])>=contrast('#ffffff',palette['bg'])
        highlight='#000000' if contrast('#000000',palette['accent'])>=contrast('#ffffff',palette['accent']) else '#ffffff'
        logo_filter='brightness(0)' if light else 'brightness(0) invert(1)'
        overrides=f'''<style id="brand-override">.banner{{background:var(--bg)!important;--logo-filter:{logo_filter}}}.banner .subtitle,.banner .line,.banner .proof-card{{color:var(--fg)!important}}.banner .proof-card,.banner .proof-grid:before{{--logo-filter:{logo_filter}!important;background:var(--bg)!important;border-color:var(--accent)!important}}.banner .line:last-child{{color:var(--accent)!important;background:transparent!important}}.banner .waves g{{stroke:var(--accent)}}.clarekitching .line:last-child{{background:var(--accent)!important;color:{highlight}!important}}.banner .metric{{color:var(--fg)!important}}.banner .metric-caption{{color:var(--fg)!important}}</style>'''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}\n{css}</style>{overrides}</head><body><main class="banner evidence-layout {style}{' metric-layout' if metric_layout else ''}" style="--bg:{palette['bg']};--fg:{palette['fg']};--accent:{palette['accent']};--count:{len(cards)}">{scenery}{decor}{photo}<div class="content"><h1 data-qa="essential">{title}</h1><div class="subtitle" data-qa="essential">{esc(brief['banner_subtitle'])}</div></div>{proof_grid}</main></body></html>'''
