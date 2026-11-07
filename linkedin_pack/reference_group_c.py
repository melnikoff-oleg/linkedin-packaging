"""Reference-faithful Adrian, Chris, Charlie and Liam compositions.

Coordinates reproduce the saved source rasters on the 1584 × 396 design canvas.
Only subject-specific copy/marks are substituted. Secondary type deliberately
retains the source hierarchy instead of the superseded universal 48px minimum.
"""
import math

REFERENCE_CONTENT = {
    'adrian-kul': {
        'brand': 'KW',
        'title': 'Fractional CTO & technology partner for scaling teams',
    },
    'donnellychris': {
        'brand': 'W27 Collective',
        'title_lines': ['Outages ended', 'No full rewrite'],
        'logo_keys': ['1167899', '2454643', 'digitalh2o'],
        'logo_relation': 'PAST OPERATING ROLES',
        'support': 'At Factor: rebuilt without interrupting growth',
        'award_label': 'FOREVERCAR · PRODUCT AWARDS',
        'awards': [
            {'name': 'Red Herring', 'detail': 'Top 100 Global', 'year': '2018'},
            {'name': 'CODiE', 'detail': 'Insurance Solution', 'year': '2018'},
            {'name': 'Stevie', 'detail': 'Bronze · 1Quote', 'year': '2018'},
            {'name': 'Chicago', 'detail': 'Innovation Award', 'year': '2016'},
        ],
    },
    'charlie-hills': {
        'title_lines': ['From a spreadsheet', 'to acquired business'],
        'support_primary': 'Digital H2O',
        'support_secondary': ' · Founding technology leader',
        'companies': [
            {'key': 'digitalh2o', 'name': 'Digital H2O', 'role': 'Founding tech lead', 'color': '#73b5d4'},
            {'key': '2839269', 'name': 'Factor', 'role': 'Former CTO', 'color': '#163e98'},
            {'key': '1167899', 'name': 'Double Good', 'role': 'Former VP Eng.', 'color': '#a93863'},
            {'key': 'forevercar', 'name': 'ForeverCar', 'role': 'Former CTO', 'color': '#ed4b06'},
        ],
    },
    'liamkarlsson': {
        'brand': 'W27',
        'title_lines': ['From daily outages to stability', 'At Factor, without a full software rewrite'],
        'support': 'Factor CTO · Incremental rebuild',
        'logo_relation': 'PAST OPERATING ROLES',
        'logo_keys': ['2839269', '1167899', 'forevercar', 'digitalh2o', '2454643', '1009'],
    },
}

# Source measurements below are normalized, then converted to design pixels.
# Public REFERENCE_REGIONS always contains 1584 × 396 pixel coordinates.
# Decorative background spans the canvas and is judged visually, not as text.
REFERENCE_REGIONS = {
    'adrian-kul': {
        'brand': {'x': 676/1400, 'y': 96/350, 'width': 50/1400, 'height': 43/350},
        'title': {'x': 677/1400, 'y': 281/350, 'width': 537/1400, 'height': 26/350},
    },
    'donnellychris': {
        'brand': {'x': 70/1400, 'y': 60/349, 'width': 230/1400, 'height': 36/349},
        'logos': {'x': 419/1400, 'y': 61/349, 'width': 414/1400, 'height': 120/349},
        'title': {'x': 855/1400, 'y': 55/349, 'width': 470/1400, 'height': 139/349},
        'support': {'x': 417/1400, 'y': 236/349, 'width': 572/1400, 'height': 60/349},
        'awards': {'x': 1074/1400, 'y': 232/349, 'width': 250/1400, 'height': 66/349},
    },
    'charlie-hills': {
        'title': {'x': 370/1400, 'y': 93/349, 'width': 489/1400, 'height': 109/349},
        'support': {'x': 370/1400, 'y': 222/349, 'width': 484/1400, 'height': 24/349},
        'logos': {'x': 885/1400, 'y': 81/349, 'width': 478/1400, 'height': 177/349},
    },
    'liamkarlsson': {
        'brand': {'x': 35/1400, 'y': 20/349, 'width': 190/1400, 'height': 50/349},
        'title': {'x': 394/1400, 'y': 58/349, 'width': 947/1400, 'height': 102/349},
        'support': {'x': 966/1400, 'y': 207/349, 'width': 377/1400, 'height': 45/349},
        'logos': {'x': 766/1400, 'y': 273/349, 'width': 578/1400, 'height': 43/349},
    },
}


REFERENCE_REGIONS = {slug: {name: {key: value * (1584 if key in ("x", "width") else 396) for key, value in box.items()} for name, box in regions.items()} for slug, regions in REFERENCE_REGIONS.items()}


def _content(ctx, slug):
    return ctx['brief']['reference_content']


def _lines(lines, esc):
    return ''.join(f'<span>{esc(x)}</span>' for x in lines)


def render_adrian_kul(ctx):
    c = _content(ctx, 'adrian-kul'); e = ctx['esc']
    body = f'''<div class="rfc-adrian">
      <svg class="rfc-a-geometry" viewBox="0 0 1584 396" aria-hidden="true"><defs>
       <filter id="rfc-a-soft"><feGaussianBlur stdDeviation="1.2"/></filter>
      </defs><g fill="none" stroke="#f6f6f6" stroke-width="3" filter="url(#rfc-a-soft)">
       <path d="M904,-50 C895,12 897,65 904,119 Q911,160 882,173 L770,209 Q734,220 737,263"/>
       <path d="M919,-50 C912,13 912,68 918,120 Q925,165 896,178 L786,216 Q751,230 756,268"/>
       <path d="M1584,-13 L982,180 Q931,198 954,239 L976,274"/>
       <path d="M1584,1 L989,193 Q950,206 969,241 L990,272"/>
      </g><g fill="none" stroke="#fbfbfb" stroke-width="1.5">
       <path d="M900,-50 C891,12 893,65 900,119 Q907,158 877,169 L765,204 Q729,215 731,260"/>
       <path d="M913,-50 C906,13 906,68 912,120 Q919,161 890,174 L780,212 Q745,226 750,264"/>
       <path d="M1584,-7 L984,186 Q939,201 962,239 L982,271"/>
      </g></svg>
      <div class="rfc-a-brand" data-ref="brand" aria-label="Personal initials"><span>{e(c['brand'])}</span></div>
      <h1 class="rfc-a-title" data-ref="title">{e(c['title'])}</h1>
    </div>'''
    css = '''
    .rfc-adrian{position:absolute;inset:0;background:#fff;color:#080808;font-family:Inter,Arial,sans-serif}
    .rfc-a-geometry{position:absolute;inset:0;width:100%;height:100%}
    .rfc-a-brand{position:absolute;left:764.85px;top:108.62px;width:56.57px;height:48.65px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:850;letter-spacing:-3.6px;line-height:1}.rfc-a-brand span{display:flex;align-items:center;justify-content:center;width:49px;height:46px;background:#050505;color:#fff;border-radius:50%;padding-right:3px}
    .rfc-a-title{position:absolute;left:766px;top:318px;width:608px;height:30px;margin:0;font-size:25.5px;line-height:30px;letter-spacing:-.65px;font-weight:620;white-space:nowrap}
    '''
    return body, css


def _globe():
    # Dense spherical stippling follows the original rising globe rather than
    # an unrelated rectangular dot gradient. It is deterministic vector art.
    dots=[]
    for row in range(83):
        y=17+row*5.1
        cy=397; ry=378; rx=640; cx=798
        dy=(y-cy)/ry
        if abs(dy)>1: continue
        half=rx*math.sqrt(1-dy*dy)
        for col in range(int(half*2/5.2)+1):
            x=cx-half+col*5.2
            norm=abs(x-cx)/max(half,1)
            r=.45+1.10*(1-norm)**.35
            # Gentle unevenness resembles screen-print ink, not random noise.
            r*=.70+.30*(.5+.5*math.sin(x*.41+y*.73))
            dots.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r:.2f}" ry="{r*1.28:.2f}"/>')
    return '<svg class="rfc-c-globe" viewBox="0 0 1584 396" aria-hidden="true"><g fill="#fff2df" opacity=".8">'+''.join(dots)+'</g></svg>'


def render_donnellychris(ctx):
    c = _content(ctx, 'donnellychris'); e=ctx['esc']; logo=ctx['logo']
    component=ctx.get('logo_component',logo)
    sizes=[(174,132),(145,132),(125,132)]
    marks=''.join(f'<div class="rfc-c-logo logo-{i}">{(logo if i==0 else component)(key,*sizes[i%3],"#ffffff")}</div>' for i,key in enumerate(c['logo_keys']))
    badges=''.join(f'<div class="rfc-c-award"><div class="rfc-c-award-year">{e(a["year"])}</div><strong>{e(a["name"])}</strong><span>{e(a["detail"])}</span></div>' for a in c['awards'])
    body=f'''<div class="rfc-chris">{_globe()}
      <div class="rfc-c-brand" data-ref="brand"><span class="rfc-c-brandmark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>{e(c['brand'])}</div>
      <div class="rfc-c-logos" data-ref="logos">{marks}<div class="rfc-c-relation">{e(c['logo_relation'])}</div></div>
      <h1 class="rfc-c-title" data-ref="title">{_lines(c['title_lines'],e)}</h1>
      <div class="rfc-c-support" data-ref="support"><span>{e(c['support'])}</span><b aria-hidden="true">↓</b></div>
      <div class="rfc-c-awards" data-ref="awards"><div class="rfc-c-awards-label">{e(c['award_label'])}</div>{badges}</div>
    </div>'''
    css='''
    .rfc-chris{position:absolute;inset:0;overflow:hidden;background:#fe4d00;color:#fff;font-family:Inter,Arial,sans-serif}
    .rfc-c-globe{position:absolute;inset:0;width:100%;height:100%}
    .rfc-c-brand{position:absolute;left:79.2px;top:68px;width:260.23px;height:40.85px;display:flex;gap:7px;align-items:center;font-size:33.5px;line-height:1;font-weight:560;letter-spacing:-1.8px;white-space:nowrap}
    .rfc-c-brandmark{width:37px;height:34px;flex:none;display:grid;grid-template-columns:1fr 1fr;gap:3px}
    .rfc-c-brandmark i{background:#fff;border-radius:10px 0 0 0}.rfc-c-brandmark i:nth-child(2){border-radius:0 0 12px 0}.rfc-c-brandmark i:nth-child(3){border-radius:0 0 0 12px}.rfc-c-brandmark i:nth-child(4){border-radius:0 12px 0 0}
    .rfc-c-logos{position:absolute;left:474px;top:69px;width:468.4px;height:136.2px;display:flex;align-items:center;justify-content:space-between;gap:12px}
    .rfc-c-logo{width:146px;height:132px;flex:none;display:flex;align-items:center;justify-content:center}.rfc-c-logo img{max-width:100%;max-height:100%;object-fit:contain}.rfc-c-logo.logo-0{width:174px}.rfc-c-logo.logo-1{width:145px}.rfc-c-logo.logo-2{width:125px}
    .rfc-c-relation{position:absolute;top:143px;left:0;right:0;text-align:center;font-size:12px;letter-spacing:2.2px;font-weight:650;color:#fff}
    .rfc-c-title{position:absolute;left:967.4px;top:62.4px;width:531.8px;height:157.8px;margin:0;text-align:right;font-size:80.2px;line-height:.985;letter-spacing:-2.4px;font-weight:420;white-space:nowrap}
    .rfc-c-title span{display:block}
    .rfc-c-support{position:absolute;left:471.8px;top:267.8px;width:647.1px;height:68.1px;padding:0 17px 0 24px;background:#ff995fdb;border:1px solid #ffc29ccc;border-radius:40px;display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:27.5px;font-weight:400;letter-spacing:-.45px;white-space:nowrap}
    .rfc-c-support b{flex:none;display:flex;justify-content:center;align-items:center;width:29px;height:29px;border:1.5px solid #fff;border-radius:50%;font-size:25px;font-weight:400;line-height:1}
    .rfc-c-awards{position:absolute;left:1215.2px;top:263.2px;width:282.9px;height:74.9px;display:flex;gap:7px}
    .rfc-c-awards-label{position:absolute;left:0;right:0;top:-19px;text-align:center;white-space:nowrap;font-size:10.5px;letter-spacing:.4px;font-weight:650}
    .rfc-c-award{position:relative;flex:1;min-width:0;text-align:center;background:#fff;color:#171717;padding:3px 3px 12px;clip-path:polygon(0 0,100% 0,100% 81%,50% 100%,0 81%);display:flex;align-items:center;flex-direction:column;box-shadow:inset 0 -10px #f6be4a}
    .rfc-c-award-year{font-size:7px;line-height:10px;font-weight:700;width:100%;border-bottom:1px solid #ccc}
    .rfc-c-award strong{font-size:10.7px;line-height:12px;margin-top:5px;letter-spacing:-.2px}
    .rfc-c-award span{font-size:7.4px;line-height:9px;margin-top:3px;letter-spacing:-.1px}
    '''
    return body,css


def render_charlie_hills(ctx):
    c=_content(ctx,'charlie-hills');e=ctx['esc'];logo=ctx['logo']
    people=''
    for i,co in enumerate(c['companies']):
        width,height=((87,35) if co["key"]=="digitalh2o" else ((124,58) if co["key"]!="1167899" else (92,76)))
        people+=f'''<div class="rfc-h-circle circle-{i}" style="--company-color:{e(co['color'])}"><div class="rfc-h-mark">{logo(co['key'],width,height,'#ffffff')}</div><div class="rfc-h-caption"><strong>{e(co['name'])}</strong><span>{e(co['role'])}</span></div></div>'''
    lines=c['title_lines']
    body=f'''<div class="rfc-charlie">
      <h1 class="rfc-h-title" data-ref="title"><span>{e(lines[0])}</span><span>{e(lines[1])}</span></h1>
      <div class="rfc-h-support" data-ref="support"><strong>{e(c['support_primary'])}</strong><span>{e(c['support_secondary'])}</span></div>
      <div class="rfc-h-companies" data-ref="logos">{people}</div>
    </div>'''
    css='''
    .rfc-charlie{position:absolute;inset:0;background:#fff;color:#202121;font-family:Inter,Arial,sans-serif;background-image:linear-gradient(#f0f0f0 1px,transparent 1px),linear-gradient(90deg,#f0f0f0 1px,transparent 1px);background-size:39.6px 39.7px}
    .rfc-h-title{position:absolute;left:418.63px;top:105.5px;width:553.27px;height:123.68px;margin:0;font-size:59.8px;line-height:1.075;letter-spacing:-2.4px;font-weight:710;white-space:nowrap}
    .rfc-h-title span{display:block}.rfc-h-title span:last-child{color:#0875d3}
    .rfc-h-support{position:absolute;left:418.63px;top:251.9px;width:547.61px;height:27.23px;white-space:nowrap;font-size:25.1px;line-height:27.23px;font-weight:580;letter-spacing:-.45px;color:#787878}
    .rfc-h-support strong{font-weight:750;color:#202121}
    .rfc-h-companies{position:absolute;left:1001.31px;top:91.91px;width:540.82px;height:200.85px}
    .rfc-h-circle{position:absolute;top:21px;width:140px;height:140px;border:4px solid #fff;border-radius:50%;background:var(--company-color);box-shadow:0 8px 14px #1d558d16}
    .rfc-h-mark{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:10px}.rfc-h-mark img{max-width:100%;max-height:100%;object-fit:contain}
    .rfc-h-circle.circle-0{left:0;z-index:1}.circle-0 .rfc-h-mark{justify-content:flex-start;padding-left:10px}
    .rfc-h-circle.circle-1{left:104px;top:0;width:184px;height:184px;z-index:3}
    .rfc-h-circle.circle-2{left:269px;z-index:2}
    .rfc-h-circle.circle-3{left:400.8px;z-index:1}
    .rfc-h-caption{position:absolute;top:103px;left:6px;right:6px;padding:6px 3px 5px;background:var(--company-color);border:3px solid #fff;border-radius:26px;box-shadow:0 7px 15px #144f8f20;text-align:center;color:#fff;white-space:nowrap}
    .rfc-h-caption strong{display:block;font-size:15.1px;line-height:17px;letter-spacing:-.35px;font-weight:750}
    .rfc-h-caption span{display:block;font-size:12px;line-height:13.2px;letter-spacing:-.35px}
    .circle-1 .rfc-h-caption{top:148px;left:32px;right:32px}
    '''
    return body,css


def _engraving():
    # Deterministic stippled fallback. The final build can supply the faithful
    # clean reference background through ctx['reference_background'].
    dots=[]
    for row in range(100):
        y=row*4.2
        for col in range(386):
            x=col*4.15
            edge=70 + 190*math.exp(-((x-980)/310)**2) - 115*math.exp(-((x-1450)/220)**2)
            edge+=18*math.sin(x*.014)+12*math.sin(x*.055)
            density=1/(1+math.exp(-(y-edge)/13))
            texture=.5+.5*math.sin(x*.73+y*.41+5*math.sin(x*.012+y*.031))
            if texture < density*.91:
                rad=.50+1.2*(.5+.5*math.sin(x*.43-y*.7))
                dots.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rad:.2f}" ry="{rad*1.28:.2f}"/>')
    return '<svg class="rfc-l-texture" viewBox="0 0 1584 396" aria-hidden="true"><g fill="#d6ac73">'+''.join(dots)+'</g></svg>'


def render_liamkarlsson(ctx):
    c=_content(ctx,'liamkarlsson');e=ctx['esc'];logo=ctx['logo']
    background=ctx.get("reference_background") or ctx.get("background")
    texture=f'<img class="rfc-l-texture" src="{background}" alt="">' if background else _engraving()
    sizes=[(161,46),(78,48),(70,48),(48,48),(58,48),(126,48)]
    component=ctx.get('logo_component',logo)
    component_keys={'forevercar','digitalh2o','2454643'}
    marks=''.join(f'<span>{(component if key in component_keys else logo)(key,*sizes[i%len(sizes)],"#ffffff")}</span>' for i,key in enumerate(c['logo_keys']))
    body=f'''<div class="rfc-liam">{texture}
      <div class="rfc-l-brand" data-ref="brand"><span class="rfc-l-monogram" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span><span>{e(c['brand'])}</span></div>
      <h1 class="rfc-l-title" data-ref="title">{_lines(c['title_lines'],e)}</h1>
      <div class="rfc-l-support" data-ref="support">{e(c['support'])}</div>
      <div class="rfc-l-logos" data-ref="logos"><small>{e(c['logo_relation'])}</small>{marks}</div>
    </div>'''
    css='''
    .rfc-liam{position:absolute;inset:0;overflow:hidden;background:#072a76;color:#fff;font-family:Inter,Arial,sans-serif}
    .rfc-l-texture{position:absolute;inset:0;width:100%;height:100%;object-fit:fill;filter:saturate(.90) brightness(1.06) contrast(.97)}
    .rfc-l-brand{position:absolute;left:39.6px;top:22.69px;width:215px;height:56.73px;display:flex;align-items:center;gap:13px;font-family:Georgia,serif;font-size:52px;line-height:1;letter-spacing:-1px}
    .rfc-l-monogram{flex:none;width:53px;height:53px;display:grid;grid-template-columns:repeat(3,1fr);gap:3px;transform:rotate(45deg);padding:3px}
    .rfc-l-monogram i{background:white}.rfc-l-monogram i:nth-child(even){opacity:.15}
    .rfc-l-title{position:absolute;left:445.8px;top:65.81px;width:1071.46px;height:115.74px;margin:0;text-align:right;font-size:55.2px;line-height:1.19;font-weight:700;letter-spacing:-.75px;white-space:nowrap;text-shadow:0 1px 1px #072a7620}
    .rfc-l-title span{display:block}
    .rfc-l-support{position:absolute;left:1092.96px;top:234.88px;width:426.55px;height:51.06px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:#072a76;color:#fff;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:18.8px;font-weight:650;letter-spacing:.2px;white-space:nowrap}
    .rfc-l-logos{position:absolute;left:866.74px;top:309.82px;width:653.97px;height:48.79px;display:flex;align-items:center;justify-content:space-between;gap:8px}
    .rfc-l-logos>span{display:flex;align-items:center;justify-content:center;flex:none}.rfc-l-logos img{object-fit:contain}
    .rfc-l-logos small{position:absolute;left:0;top:-15px;font-size:9px;letter-spacing:1.8px;font-weight:650;color:#fff}
    '''
    return body,css
