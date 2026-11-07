"""Measured, reference-faithful Matt, Rob and Jake compositions.

Coordinates are original 1400×350 source pixels multiplied by 1584/1400.
These layouts deliberately retain their original information hierarchies.
"""

REFERENCE_CONTENT = {
    'mattgray1': {
        'title_prefix': 'From ',
        'title_emphasis': 'spreadsheet prototype',
        'title_suffix': ' to SaaS, acquired by Genscape.',
    },
    'rob-hoffman-ceo': {
        'brand': 'w27collective',
        'title_lines': ['The fractional CTO', 'built for what’s next.'],
        'support': 'Factor: daily peak outages ended',
        'logos_label': 'PAST OPERATING ROLES:',
        'logo_keys': ['2839269', 'forevercar', '1167899'],
        'award_label': 'FOREVERCAR’S',
        'award_product': '1Quote',
        'award_name': 'Bronze Stevie',
        'award_year': '2018',
    },
    'jakezward': {
        'brand': 'w27collective',
        'title_prefix': '~30% ',
        'title_emphasis': 'higher throughput',
        'title_second': '~25% less testing effort.',
        'logos_label': 'PAST ROLES',
        'logo_keys': ['2839269', 'forevercar', '2454643', '1009', 'digitalh2o'],
    },
}

REFERENCE_REGIONS = {
    'mattgray1': {
        'title': {'x':156,'y':86,'width':925,'height':44},
        'photo': {'x':1104,'y':55,'width':257,'height':341},
    },
    'rob-hoffman-ceo': {
        'brand': {'x':42,'y':48,'width':192,'height':46},
        'title': {'x':619,'y':62,'width':548,'height':125},
        'support': {'x':621,'y':216,'width':482,'height':30},
        'logos': {'x':621,'y':280,'width':432,'height':75},
        'photo': {'x':1186,'y':17,'width':301,'height':379},
        'award': {'x':1495,'y':25,'width':67,'height':92},
    },
    'jakezward': {
        'brand': {'x':42,'y':40,'width':145,'height':36},
        'title': {'x':446,'y':100,'width':641,'height':116},
        'capsule': {'x':438,'y':261,'width':837,'height':70},
        'photo': {'x':1233,'y':23,'width':319,'height':373},
        'orbits': {'x':1082,'y':45,'width':502,'height':351},
    },
}


def _content(ctx, slug):
    # Dispatcher requires explicit content; do not inject Kal into other users.
    return ctx['brief']['reference_content']


def render_mattgray1(ctx):
    e=ctx['esc']; c=_content(ctx,'mattgray1')
    title=(e(c['title_prefix'])+'<em>'+e(c['title_emphasis'])+'</em>'+e(c['title_suffix']))
    body=f'''<img class="rf-matt-landscape" src="{e(ctx['background'])}" alt="">
    <div class="rf-matt-shade"></div>
    <h1 class="rf-matt-title" data-ref="title" data-qa="essential">{title}</h1>
    <div class="rf-matt-photo" data-ref="photo"><img src="{e(ctx['photo'])}" alt=""></div>'''
    css='''
    .banner{background:#21342b}
    .rf-matt-landscape{position:absolute;inset:0;width:1584px;height:396px;object-fit:cover;object-position:center;filter:saturate(.72) contrast(.90) brightness(1.04)}
    .rf-matt-shade{position:absolute;inset:0;background:linear-gradient(90deg,#05100e50 0%,#05100e25 52%,transparent 75%)}
    .rf-matt-title{position:absolute;left:156px;top:86px;width:925px;height:44px;margin:0;font:400 41px/1.073 CormorantGaramond,Georgia,serif;letter-spacing:-.5px;white-space:nowrap;color:#fff}
    .rf-matt-title em{font-style:normal;color:#d2e873}
    .rf-matt-photo{position:absolute;left:1104px;top:55px;width:257px;height:341px;overflow:visible}
    .rf-matt-photo img{position:absolute;left:-62px;top:-4px;width:333px;height:auto;max-width:none}
    '''
    return body,css


def render_rob_hoffman_ceo(ctx):
    e=ctx['esc']; c=_content(ctx,'rob-hoffman-ceo');logo=ctx['logo']
    marks=''.join('<div class="rf-rob-mark">'+logo(k,w,h,'#ffffff')+'</div>' for k,w,h in zip(c['logo_keys'],[112,177,70],[27,29,44]))
    lines=''.join(f'<span>{e(t)}</span>' for t in c['title_lines'])
    body=f'''<div class="rf-rob-glow left"></div><div class="rf-rob-glow right"></div>
    <div class="rf-rob-brand" data-ref="brand" data-qa="essential">{e(c['brand'])}</div>
    <h1 class="rf-rob-title" data-ref="title" data-qa="essential">{lines}</h1>
    <div class="rf-rob-support" data-ref="support" data-qa="essential">{e(c['support'])}</div>
    <div class="rf-rob-logos" data-ref="logos"><div class="rf-rob-label" data-qa="essential">{e(c['logos_label'])}</div><div class="rf-rob-marks">{marks}</div></div>
    <div class="rf-rob-photo" data-ref="photo"><img src="{e(ctx['photo'])}" alt=""></div>
    <div class="rf-rob-award" data-ref="award" data-qa="essential"><small>{e(c['award_label'])}</small><strong>{e(c['award_product'])}</strong><span>{e(c['award_name'])}</span><b>{e(c['award_year'])}</b></div>'''
    css='''
    .banner{background:#111211;color:#fff;font-family:Inter,Arial,sans-serif}
    .rf-rob-glow{position:absolute;pointer-events:none;border-radius:50%}
    .rf-rob-glow.left{left:-215px;bottom:-218px;width:530px;height:530px;background:radial-gradient(ellipse,#91ac12 0%,#81990c85 29%,transparent 66%)}
    .rf-rob-glow.right{right:-182px;top:-229px;width:555px;height:555px;background:radial-gradient(ellipse,#c5ec0b 0%,#b4d620da 28%,#8ba30c60 43%,transparent 68%)}
    .rf-rob-brand{position:absolute;left:42px;top:48px;width:192px;height:46px;font-size:34px;line-height:1.1;letter-spacing:-1.8px;font-weight:650;color:#fff}
    .rf-rob-title{position:absolute;left:619px;top:62px;width:548px;height:125px;margin:0;font-size:61px;line-height:1.025;font-weight:400;letter-spacing:-1.9px;white-space:nowrap}
    .rf-rob-title span{display:block}.rf-rob-title span:last-child{color:#c6eb2d}
    .rf-rob-support{position:absolute;left:621px;top:216px;width:482px;height:30px;font-size:26px;line-height:30px;letter-spacing:-.5px;white-space:nowrap}
    .rf-rob-logos{position:absolute;left:621px;top:280px;width:432px;height:75px}
    .rf-rob-label{font-size:17px;line-height:21px;font-weight:600;letter-spacing:-.3px}
    .rf-rob-marks{display:flex;align-items:center;gap:24px;height:52px;padding-top:9px}
    .rf-rob-mark{display:flex;align-items:center;flex:none}.rf-rob-mark img{object-fit:contain}
    .rf-rob-photo{position:absolute;left:1186px;top:17px;width:301px;height:379px;overflow:visible}
    .rf-rob-photo img{position:absolute;left:-15px;top:-4px;width:331px;height:auto;max-width:none;filter:grayscale(1)}
    .rf-rob-award{position:absolute;left:1495px;top:25px;width:67px;height:92px;display:flex;flex-direction:column;align-items:center;gap:3px;color:#101509;text-align:center;z-index:3}
    .rf-rob-award small{font-size:8px;line-height:10px;font-weight:650;white-space:nowrap}.rf-rob-award strong{font:700 25px/25px CormorantGaramond,serif;letter-spacing:-.5px}.rf-rob-award span{font-size:9.8px;line-height:13px;font-weight:700;white-space:nowrap}.rf-rob-award b{font:700 18px/20px Georgia,serif}
    '''
    return body,css


def render_jakezward(ctx):
    e=ctx['esc'];c=_content(ctx,'jakezward');logo=ctx['logo']
    marks=''.join('<div class="rf-jake-mark">'+logo(k,w,h,'#74777b')+'</div>' for k,w,h in zip(c['logo_keys'],[112,145,99,53,117],[24,26,34,25,26]))
    # Abstract engineering glyphs retain the source's orbit structure without
    # suggesting use, partnership or certification by unrelated AI platforms.
    glyphs=[('one','⌘'),('two','✳'),('three','⌁'),('four','◇'),('five','⌘')]
    disks=''.join(f'<span class="rf-jake-disk {name}" aria-hidden="true">{glyph}</span>' for name,glyph in glyphs)
    body=f'''<div class="rf-jake-brand" data-ref="brand" data-qa="essential">{e(c['brand'])}</div>
    <div class="rf-jake-orbits" data-ref="orbits"><div class="ring one"></div><div class="ring two"></div>{disks}</div>
    <h1 class="rf-jake-title" data-ref="title" data-qa="essential"><span>{e(c['title_prefix'])}<em>{e(c['title_emphasis'])}</em></span><span>{e(c['title_second'])}</span></h1>
    <div class="rf-jake-capsule" data-ref="capsule"><span class="rf-jake-label" data-qa="essential">{e(c['logos_label'])}</span>{marks}</div>
    <div class="rf-jake-photo" data-ref="photo"><img src="{e(ctx['photo'])}" alt=""></div>'''
    css='''
    .banner{background:#fafaf8;color:#101111;font-family:Inter,Arial,sans-serif}
    .banner:before{content:'';position:absolute;right:-105px;bottom:-180px;width:650px;height:620px;background:radial-gradient(ellipse,#ff83617d 0%,#f5c4b655 46%,transparent 70%)}
    .rf-jake-brand{position:absolute;left:42px;top:40px;width:145px;height:36px;font-size:25.5px;line-height:1.1;font-weight:650;letter-spacing:-1.3px}
    .rf-jake-title{position:absolute;left:446px;top:100px;width:641px;height:116px;margin:0;font-size:60px;line-height:.97;font-weight:700;letter-spacing:-2.1px;white-space:nowrap}
    .rf-jake-title span{display:block}.rf-jake-title em{font-family:Inter,Arial,sans-serif;font-style:italic;color:#ff5031}
    .rf-jake-capsule{position:absolute;left:438px;top:261px;width:837px;height:70px;display:flex;align-items:center;gap:25px;padding:0 38px 0 44px;border:1px solid #cbccc8;border-radius:36px;background:linear-gradient(#f0f0ed80,#ffffff20 50%,#f7f7f4a0);box-shadow:inset 0 2px 7px #00000003}
    .rf-jake-label{font-size:12px;font-weight:650;color:#74777b;line-height:15px;white-space:nowrap;flex:none}
    .rf-jake-mark{display:flex;align-items:center;flex:none}.rf-jake-mark img{object-fit:contain}
    .rf-jake-photo{position:absolute;left:1233px;top:23px;width:319px;height:373px;overflow:visible;z-index:2}
    .rf-jake-photo img{position:absolute;left:-73px;top:-4px;width:398px;height:auto;max-width:none}
    .rf-jake-orbits{position:absolute;left:1082px;top:45px;width:502px;height:351px}
    .rf-jake-orbits .ring{position:absolute;border:1px dotted #e7ac9d;border-radius:50%}
    .rf-jake-orbits .ring.one{left:0;top:0;width:650px;height:650px}.rf-jake-orbits .ring.two{left:73px;top:62px;width:495px;height:495px}
    .rf-jake-disk{position:absolute;width:43px;height:43px;border-radius:50%;background:white;border:1px solid #e9e4df;box-shadow:0 2px 3px #00000030;display:flex;align-items:center;justify-content:center;font:400 29px/1 Arial,sans-serif;z-index:1}
    .rf-jake-disk.one{left:117px;top:27px;color:#202321}.rf-jake-disk.two{left:390px;top:-2px;color:#d97550}.rf-jake-disk.three{left:97px;top:141px;color:#2683cd}.rf-jake-disk.four{left:458px;top:67px;color:#bb5ad3}.rf-jake-disk.five{left:50px;top:312px;color:#368d8c}
    '''
    return body,css
