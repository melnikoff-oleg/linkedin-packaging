"""Reference-locked Clare, Diandra and Lara compositions (1584 x 396).

These templates intentionally retain the reference hierarchy, including smaller
secondary type. They must not be fed through the old one-unit/48px layout rules.
Callers explicitly provide reference_content: defaults below are the sourced Kal
fixture, not a fallback identity for another subject.
"""

REFERENCE_CONTENT = {
    'clarekitching': {
        'brand': 'W27', 'brand_suffix': 'collective',
        'title': ['From minutes of waiting', 'to quotes in <5 seconds'],
        'support': ['ForeverCar’s pricing,', 'built in-house as CTO.'],
        'support_accent': 'built in-house as CTO.',
        'relationship': 'PAST OPERATING ROLES',
        'logos': ['2839269', '1167899', 'forevercar'],
    },
    'diandraescobar': {
        'brand': 'W27',
        'title': ['Your', 'Fractional', 'CTO'],
        'support': 'Former engineering leader at',
        'logos': ['2839269', '1167899', 'forevercar'],
        'cards': [
            {'company': 'Factor', 'role': 'Former CTO', 'text': 'Daily peak outages ended\nwithout a full rewrite.'},
            {'company': 'Double Good', 'role': 'Former VP', 'text': 'Release throughput up ~30%.'},
            {'company': 'ForeverCar', 'role': 'Former CTO', 'text': 'From >5 minutes to <5 seconds\nfor vehicle-protection quotes.'},
            {'company': 'Double Good', 'role': 'Former VP', 'text': 'AI-assisted QA workflows:\n~25% less testing effort.'},
            {'company': 'HelloFresh', 'role': 'Former engineering lead', 'text': 'Mentoring: one team to global.'},
        ],
    },
    'laraacostar': {
        'intro': 'Fractional CTO & hands-on builder',
        'title': [
            [{'text': 'At Factor, daily peak ', 'accent': False}, {'text': 'outages', 'accent': True}],
            [{'text': 'ended.', 'accent': True}, {'text': ' No full rewrite needed.', 'accent': False}],
        ],
        'credentials': ['INCREMENTAL REBUILD', 'FORMER FACTOR CTO'],
        'relationship': 'PAST ROLES',
        'logos': ['2839269', '1167899', 'forevercar', '2454643'],
    },
}

# Approximate source-raster ink/region bounds, normalized to 1584 x 396.
# Fixed outer regions carry data-ref; content keeps the source visual proportions.
REFERENCE_REGIONS = {
    'clarekitching': {
        'brand': {'x': 55, 'y': 44, 'width': 237, 'height': 54},
        'title': {'x': 757, 'y': 43, 'width': 635, 'height': 130},
        'support': {'x': 905, 'y': 185, 'width': 465, 'height': 85},
        'logos': {'x': 999, 'y': 311, 'width': 585, 'height': 85},
    },
    'diandraescobar': {
        'brand': {'x': 45, 'y': 38, 'width': 96, 'height': 66},
        'cards': {'x': 326, 'y': 35, 'width': 589, 'height': 315},
        'photo': {'x': 804, 'y': 13, 'width': 324, 'height': 383},
        'title': {'x': 1190, 'y': 40, 'width': 340, 'height': 205},
        'support': {'x': 1202, 'y': 269, 'width': 332, 'height': 31},
        'logos': {'x': 1202, 'y': 310, 'width': 326, 'height': 32},
    },
    'laraacostar': {
        'intro': {'x': 42, 'y': 31, 'width': 430, 'height': 30},
        'photo': {'x': 516, 'y': 12, 'width': 322, 'height': 384},
        'title': {'x': 878, 'y': 63, 'width': 663, 'height': 102},
        'support': {'x': 878, 'y': 200, 'width': 635, 'height': 34},
        'logos': {'x': 837, 'y': 279, 'width': 747, 'height': 117},
    },
}


def _content(ctx, slug):
    content = ctx['brief']['reference_content']
    if not isinstance(content, dict):
        raise ValueError('reference_content must be an object')
    return content


def _lines(value, esc):
    return '<br>'.join(esc(x) for x in value.split('\n'))


def render_clarekitching(ctx):
    c = _content(ctx, 'clarekitching'); e = ctx['esc']; logo = ctx['logo']
    marks = ''.join(f'<span class="a-clare-mark mark-{i}">{logo(key, w, h, "#ffffff")}</span>'
                    for i, (key, w, h) in enumerate(zip(c['logos'], [155, 91, 195], [32, 51, 38])))
    support = '<br>'.join(f'<strong>{e(line)}</strong>' if line == c['support_accent'] else e(line) for line in c['support'])
    body = f'''<div class="a-clare-grid" aria-hidden="true"></div>
<div class="a-clare-brand" data-ref="brand"><b>{e(c['brand'])}</b><span>{e(c['brand_suffix'])}</span></div>
<div class="a-clare-title" data-ref="title"><div class="a-clare-upright">{e(c['title'][0])}</div><div class="a-clare-italic">{e(c['title'][1])}</div></div>
<div class="a-clare-elbow" aria-hidden="true"></div>
<div class="a-clare-support" data-ref="support">{support}</div>
<div class="a-clare-stripes" aria-hidden="true"></div>
<div class="a-clare-logos" data-ref="logos"><span class="a-clare-relation">{e(c['relationship'])}</span><div class="a-clare-mark-row">{marks}</div></div>'''
    css = '''
.banner{background:#00373b;color:#fff9ef;font-family:Inter,Arial,sans-serif}
.a-clare-grid{position:absolute;inset:0;background-image:linear-gradient(#b9f6ef12 1px,transparent 1px),linear-gradient(90deg,#b9f6ef12 1px,transparent 1px),linear-gradient(120deg,#00464b55,transparent 60%);background-size:80px 80px,80px 80px,100% 100%;background-position:55px 55px}
.a-clare-grid:after{content:"";position:absolute;left:457px;top:135px;width:80px;height:80px;background:#00545a30;box-shadow:80px -80px #00545a22,160px 0 #00545a30,-80px 80px #00545a20}
.a-clare-brand{position:absolute;left:55px;top:44px;width:237px;height:54px;display:flex;align-items:center;gap:12px;white-space:nowrap;color:#fff9ef}
.a-clare-brand b{font-size:53px;font-weight:750;letter-spacing:-3px;line-height:1}
.a-clare-brand span{font-size:27px;font-weight:500;letter-spacing:-1px;padding-top:5px}
.a-clare-brand b:after{content:"";display:inline-block;width:9px;height:9px;background:#ffc38a;margin-left:4px;border-radius:2px}
.a-clare-title{position:absolute;left:757px;top:43px;width:635px;height:130px;font-family:DMSerifDisplay,Georgia,serif;letter-spacing:-.7px;font-weight:400;white-space:nowrap}
.a-clare-upright{font-size:56px;line-height:1.04;padding-left:7px}
.a-clare-italic{position:absolute;top:66px;left:0;width:max-content;max-width:635px;padding:0 9px 4px;background:#f29be5;color:#00343a;font-size:57px;line-height:1;font-style:italic;letter-spacing:-.8px}
.a-clare-elbow{position:absolute;left:808px;top:183px;width:78px;height:44px;border-left:3px solid #ed9cdf;border-bottom:3px solid #ed9cdf}
.a-clare-support{position:absolute;left:905px;top:185px;width:465px;height:85px;font-size:36px;line-height:1.18;letter-spacing:-.35px;font-weight:400}
.a-clare-support strong{color:#ffc382;font-weight:700}
.a-clare-stripes{position:absolute;bottom:0;left:0;right:0;height:30px;background:linear-gradient(90deg,#ffc78d 0 28.4%,#78c6c2 28.4% 64%,#005158 64%)}
.a-clare-logos{position:absolute;left:999px;top:311px;width:585px;height:85px;background:#005258;clip-path:polygon(7% 0,100% 0,100% 100%,0 100%);padding-left:58px}
.a-clare-relation{position:absolute;left:67px;top:7px;font-size:9px;letter-spacing:2.2px;color:#ffffffc9}
.a-clare-mark-row{position:absolute;left:64px;right:24px;top:26px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:18px}
.a-clare-mark{display:flex;align-items:center;justify-content:center;flex:none}
'''
    return body, css


def render_diandraescobar(ctx):
    c = _content(ctx, 'diandraescobar'); e = ctx['esc']; logo = ctx['logo']
    card_parts = []
    for i, card in enumerate(c['cards']):
        if not any(card[key].strip() for key in ('company', 'role', 'text')):
            # An unavailable proof item still reserves its original region; it
            # must not fabricate an initial, author or generic career claim.
            card_parts.append(f'<section class="a-diandra-card a-diandra-card-{i}" data-empty-proof-slot="true" aria-hidden="true" style="visibility:hidden"></section>')
        elif not card['company'].strip():
            # A supplied source-backed phrase may have no company attribution.
            # Keep the actual words rather than silently dropping partial input.
            role = f'<div class="a-diandra-card-head"><small>{e(card["role"])}</small></div>' if card['role'].strip() else ''
            card_parts.append(f'<section class="a-diandra-card a-diandra-card-{i}">{role}<div class="a-diandra-card-text">{_lines(card["text"], e)}</div></section>')
        else:
            card_parts.append(f'''<section class="a-diandra-card a-diandra-card-{i}"><div class="a-diandra-card-head"><span class="a-diandra-initial" aria-hidden="true">{e(card['company'][0])}</span><span><b>{e(card['company'])}</b><small>{e(card['role'])} · career result</small></span></div><div class="a-diandra-card-text">{_lines(card['text'], e)}</div></section>''')
    cards = ''.join(card_parts)
    title = ''.join(f'<span class="a-diandra-line line-{i}">{e(line)}</span>' for i,line in enumerate(c['title']))
    marks = ''.join(logo(key,w,h,'#ffffff') for key,w,h in zip(c['logos'],[106,54,119],[22,32,24]))
    body = f'''<div class="a-diandra-orb orb-left" aria-hidden="true"></div><div class="a-diandra-orb orb-right" aria-hidden="true"></div>
<div class="a-diandra-brand" data-ref="brand">{e(c['brand'])}</div>
<div class="a-diandra-cards" data-ref="cards"><div class="a-diandra-ghost ghost-1" aria-hidden="true"></div><div class="a-diandra-ghost ghost-2" aria-hidden="true"></div>{cards}</div>
<div class="a-diandra-photo-frame" data-ref="photo"><img class="a-diandra-photo" src="{e(ctx['photo'])}" alt="{e(ctx['brief'].get('name', 'Subject'))} in a wider, gesturing pose"></div>
<div class="a-diandra-title" data-ref="title">{title}</div>
<div class="a-diandra-support" data-ref="support">{e(c['support'])}</div><div class="a-diandra-logos" data-ref="logos">{marks}</div>'''
    css = '''
.banner{background:radial-gradient(ellipse at 43% 30%,#254442 0%,#01272a 39%,#001b1e 74%);color:#fff;font-family:Inter,Arial,sans-serif}
.a-diandra-orb{position:absolute;border-radius:50%;pointer-events:none}
.a-diandra-orb.orb-left{left:226px;top:-190px;width:716px;height:654px;box-shadow:inset 20px -10px 35px #64d7d222;transform:rotate(-14deg);background:radial-gradient(ellipse at 44% 35%,transparent 54%,#43a8a419 66%,#93ffff20 68%,transparent 73%)}
.a-diandra-orb.orb-right{right:-29px;top:-53px;width:420px;height:441px;box-shadow:inset -14px 9px 16px #75e5de3a;transform:rotate(-25deg)}
.a-diandra-brand{position:absolute;left:45px;top:38px;width:96px;height:66px;white-space:nowrap;font-size:48px;font-weight:750;letter-spacing:-3px;line-height:1.2}
.a-diandra-cards{position:absolute;left:326px;top:35px;width:589px;height:315px;z-index:1}
.a-diandra-card{position:absolute;background:#fdfefe;border:2px solid #b4c4c1;border-radius:14px;box-shadow:0 2px 4px #0003;color:#0c1414;padding:7px 9px 6px;overflow:hidden}
.a-diandra-card-head{height:20px;display:flex;align-items:center;gap:5px;margin-bottom:3px}
.a-diandra-initial{display:flex;align-items:center;justify-content:center;width:19px;height:19px;border-radius:50%;background:#d7e5de;color:#25524c;font-size:10px;font-weight:700;flex:none}
.a-diandra-card-head b{font-size:8px;line-height:9px;display:block;font-weight:650}
.a-diandra-card-head small{font-size:6px;line-height:7px;display:block;color:#637370}
.a-diandra-card-text{font-size:15px;line-height:1.08;letter-spacing:-.4px;white-space:nowrap}
.a-diandra-card-0{left:0;top:6px;width:249px;height:72px}
.a-diandra-card-1{left:289px;top:0;width:237px;height:63px}
.a-diandra-card-2{left:139px;top:91px;width:262px;height:66px}
.a-diandra-card-3{left:251px;top:168px;width:338px;height:76px}
.a-diandra-card-4{left:136px;top:258px;width:338px;height:57px;background:#e9eeec}
.a-diandra-card-4 .a-diandra-card-head{height:16px;margin-bottom:2px}
.a-diandra-card-4 .a-diandra-initial{height:16px;width:16px}
.a-diandra-ghost{position:absolute;background:#bac9c86b;border-radius:14px;filter:blur(6px);opacity:.45}
.a-diandra-ghost:after{content:"";position:absolute;left:22px;right:24px;top:21px;height:4px;background:#15353288;box-shadow:0 12px #15353288,0 24px #15353288}
.a-diandra-ghost.ghost-1{left:45px;top:117px;width:330px;height:76px}
.a-diandra-ghost.ghost-2{left:306px;top:280px;width:264px;height:80px;opacity:.18}
.a-diandra-photo-frame{position:absolute;left:804px;top:13px;width:324px;height:383px;z-index:2;overflow:visible}
.a-diandra-photo{position:absolute;left:-6px;top:-6px;width:344px;height:auto;display:block}
.a-diandra-title{position:absolute;left:1190px;top:40px;width:340px;height:205px;font-size:68px;line-height:.98;letter-spacing:-2.2px;font-weight:750;z-index:3}
.a-diandra-line{display:block;width:max-content;max-width:100%;white-space:nowrap;position:relative;isolation:isolate}
.a-diandra-line:not(:first-child):after{content:"";position:absolute;left:1px;right:-3px;bottom:1px;height:31px;background:#4b9ea0;z-index:-1}
.a-diandra-support{position:absolute;left:1202px;top:269px;width:332px;height:31px;font-size:21px;line-height:1.35;letter-spacing:-.3px;font-weight:350;color:#d2dddc;white-space:nowrap}
.a-diandra-logos{position:absolute;left:1202px;top:310px;width:326px;height:32px;display:flex;align-items:center;justify-content:space-between;gap:15px}
'''
    return body, css


def render_laraacostar(ctx):
    c = _content(ctx, 'laraacostar'); e = ctx['esc']; logo = ctx['logo']
    title = ''.join('<div class="a-lara-line">'+''.join(f'<span class="{"accent" if part["accent"] else "normal"}">{e(part["text"])}</span>' for part in line)+'</div>' for line in c['title'])
    icons = [
        '<svg viewBox="0 0 28 28" aria-hidden="true"><rect x="3" y="3" width="9" height="9" rx="1"/><rect x="16" y="3" width="9" height="9" rx="1"/><rect x="3" y="16" width="9" height="9" rx="1"/><path d="M16 21h9m-4-4 4 4-4 4"/></svg>',
        '<svg viewBox="0 0 28 28" aria-hidden="true"><path d="M6 22 22 6M9 6h13v13"/><path d="M4 7v17h17" opacity=".5"/></svg>',
    ]
    credentials = ''.join(f'<span class="a-lara-credential">{icon}<span>{e(label)}</span></span>' for icon,label in zip(icons,c['credentials']))
    marks = ''.join(f'<span class="a-lara-mark mark-{i}">{logo(key,w,h,"#ffffff")}</span>' for i,(key,w,h) in enumerate(zip(c['logos'],[153,95,184,170],[34,60,44,53])))
    body = f'''<div class="a-lara-glow" aria-hidden="true"></div>
<div class="a-lara-intro" data-ref="intro">{e(c['intro'])}</div>
<div class="a-lara-photo-frame" data-ref="photo"><img class="a-lara-photo" src="{e(ctx['photo'])}" alt="{e(ctx['brief'].get('name', 'Subject'))} in a separate arms-folded portrait"></div>
<div class="a-lara-title" data-ref="title">{title}</div>
<div class="a-lara-support" data-ref="support">{credentials}</div>
<div class="a-lara-logos" data-ref="logos"><div class="a-lara-mark-row">{marks}</div></div>
<div class="a-lara-relation">{e(c['relationship'])}</div>'''
    css = '''
.banner{background:linear-gradient(135deg,#050505 15%,#191919 51%,#050505 100%);color:#fff;font-family:Inter,Arial,sans-serif}
.a-lara-glow{position:absolute;left:380px;top:-98px;width:560px;height:550px;background:radial-gradient(ellipse at 48% 45%,#ab5845b0,transparent 64%);opacity:.8}
.a-lara-intro{position:absolute;left:42px;top:31px;width:430px;height:30px;font-size:24px;font-weight:720;letter-spacing:-.9px;line-height:1.2;white-space:nowrap}
.a-lara-photo-frame{position:absolute;left:516px;top:12px;width:322px;height:384px;z-index:2;overflow:visible}
.a-lara-photo{position:absolute;left:-12px;top:-7px;width:366px;height:auto;display:block}
.a-lara-title{position:absolute;left:878px;top:63px;width:663px;height:102px;font-size:48px;line-height:1.065;letter-spacing:-2px;font-weight:750;z-index:3}
.a-lara-line{white-space:nowrap}
.a-lara-title .accent{color:#d84e39}
.a-lara-line .accent + .normal{margin-left:6px}
.a-lara-support{position:absolute;left:878px;top:200px;width:635px;height:34px;display:flex;align-items:center;gap:35px;z-index:3}
.a-lara-credential{display:flex;align-items:center;gap:23px;white-space:nowrap;font-size:13px;font-weight:700;letter-spacing:3.3px}
.a-lara-credential svg{width:27px;height:27px;flex:none;fill:none;stroke:#e4b77a;stroke-width:1.6}
.a-lara-credential:first-child svg{stroke:#e67c6e}
.a-lara-logos{position:absolute;left:837px;top:279px;width:747px;height:117px;z-index:1;background-color:#202020;background-image:linear-gradient(45deg,#17171744 25%,transparent 25%,transparent 75%,#17171744 75%),linear-gradient(45deg,#10101044 25%,transparent 25%,transparent 75%,#10101044 75%);background-size:28px 28px;background-position:0 0,14px 14px}
.a-lara-mark-row{position:absolute;left:-43px;right:32px;top:37px;height:61px;display:flex;justify-content:space-between;align-items:center;gap:28px}
.a-lara-mark{display:flex;align-items:center;justify-content:center;flex:none}
.a-lara-relation{position:absolute;left:612px;top:343px;font-size:13px;font-weight:700;letter-spacing:4px;color:#fff;z-index:4;white-space:nowrap}
'''
    return body, css
