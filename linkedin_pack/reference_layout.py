"""Reference-fidelity layouts. Fixed source geometry; copy is the variable.

This mode deliberately preserves the source's hierarchy, including small
secondary labels. It never stretches all supporting copy to a global floor.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import re
from PIL import Image

MOBILE_SAFE_COPY_CSS = {
    'charlie-hills': '.rfc-h-support{padding-left:96px}',
    'donnellychris': '.rfc-c-support{padding-left:56px}',
    # Take only the label out of flow. The first mark stays within 2.5 design
    # pixels of the two account layouts; subsequent gaps and mark sizes stay.
    'jakezward': '.rf-jake-capsule{padding-left:161px}.rf-jake-label{position:absolute;left:76px;top:50%;transform:translateY(-50%)}',
    'diandraescobar': '.a-diandra-card-4{padding-left:66px}',
}


def registry():
    from . import reference_group_a as a, reference_group_b as b, reference_group_c as c
    modules=(a,b,c)
    return {slug: (getattr(m,'render_'+slug.replace('-','_')),m.REFERENCE_CONTENT[slug],
                   getattr(m,'REFERENCE_REGIONS',{}).get(slug,{}))
            for m in modules for slug in m.REFERENCE_CONTENT}


def content_schema(value):
    """A fixed slot tree: editing text cannot silently remove visual structure."""
    if isinstance(value,dict):
        return {'type':'object','additionalProperties':False,
                'properties':{k:content_schema(v) for k,v in value.items()},'required':list(value)}
    if isinstance(value,list):
        if not value: return {'type':'array','items':{'type':'string'}}
        return {'type':'array','items':content_schema(value[0]),'minItems':len(value),'maxItems':len(value)}
    if isinstance(value,str): return {'type':'string'}
    if isinstance(value,bool): return {'type':'boolean'}
    if isinstance(value,(int,float)): return {'type':'number'}
    raise ValueError('Unsupported reference-content type')


def validate_reference_content(brief):
    if brief.get('layout_mode')!='reference-faithful':
        raise ValueError('Reference renderer requires layout_mode=reference-faithful')
    if brief['selected_style'] not in registry(): raise ValueError('Unknown reference template')
    if 'reference_content' not in brief: raise ValueError('Reference slots must be supplied explicitly; never use another person’s facts')
    _,example,_=registry()[brief['selected_style']]
    def check(actual,expected,path):
        if isinstance(expected,dict):
            if not isinstance(actual,dict) or set(actual)!=set(expected): raise ValueError(f'Invalid reference slots: {path}')
            for key in expected: check(actual[key],expected[key],path+'.'+key)
        elif isinstance(expected,list):
            if not isinstance(actual,list) or len(actual)!=len(expected): raise ValueError(f'Invalid reference slot count: {path}')
            for i,(item,old) in enumerate(zip(actual,expected)):check(item,old,f'{path}[{i}]')
        elif not isinstance(actual,type(expected)):
            raise ValueError(f'Invalid reference slot type: {path}')
        elif isinstance(actual,str) and len(actual)>500:
            raise ValueError(f'Reference slot is too long: {path}')
    check(brief['reference_content'],example,'reference_content')


def reference_banner_html(brief, style, photo=None, background=None, asset_root=None):
    from .render import esc,data_uri,font_css
    validate_reference_content(brief)
    root=Path(asset_root or '.').resolve()
    records=json.loads((root/'logos/provenance.json').read_text()) if (root/'logos/provenance.json').exists() else {}
    def logo(key,width,height,color=None):
        if key=='':return f'<span data-empty-logo-slot style="display:inline-block;width:{float(width)}px;height:{float(height)}px"></span>'
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',str(key)):raise ValueError('Invalid logo key')
        relative=brief.get('logo_assets',{}).get(str(key))
        if not relative:raise ValueError(f'Reference logo slot has no supplied source asset: {key}')
        if relative!=f'logos/{key}.png':raise ValueError('Invalid logo path')
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing logo source')
        record=records.get(str(key),{})
        if record.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Logo provenance hash mismatch')
        with Image.open(path) as im:
            im=im.convert('RGBA')
            if im.getchannel('A').getextrema()[0]>=16:raise ValueError('Reference logo needs original transparent asset')
            bounds=im.getchannel('A').getbbox()
            if bounds:im=im.crop(bounds)
            buffer=io.BytesIO();im.save(buffer,format='PNG')
        uri='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
        label=record.get('display_company') or record.get('company') or str(key)
        filter_css=''
        preserve_internal_contrast=record.get('preserve_internal_contrast') is True
        if color and not preserve_internal_contrast:
            # CSS alpha mask tints original geometry, never redraws a logo.
            return f'<span class="company-logo" role="img" aria-label="{esc(label)}" data-logo-key="{esc(key)}" style="display:inline-block;width:{float(width)}px;height:{float(height)}px;background:{esc(color)};mask:url({uri}) center/contain no-repeat;-webkit-mask:url({uri}) center/contain no-repeat"></span>'
        # A multitone mark can encode essential internal shapes in luminance,
        # not alpha. Only an exact opt-in in the verified asset record retains
        # its original pixels; ordinary CSS may then adapt their presentation.
        preservation=' data-preserve-internal-contrast="true"' if preserve_internal_contrast else ''
        return f'<img class="company-logo" data-logo-key="{esc(key)}"{preservation} src="{uri}" alt="{esc(label)}" style="width:{float(width)}px;height:{float(height)}px;object-fit:contain">'
    def logo_component(key,width,height,color=None):
        # Exact, detached native symbol components. Hashes bind crop coordinates
        # to inspected official assets. Never guess a crop on another logo.
        components={
            '2454643':('9ebdcce2a22c6ecd16d95330e9e383d3f9bd484e97bb1df088c8e853e12645df',4150,1349,1574,1349),
            'digitalh2o':('f84a829db0861a6e793e15f20a894f6b62e912a73af9b4d8a8da1ddc02278fec',1920,267,266,267),
            'forevercar':('f34f92cd35fe05e15f213e3b9bb9b96ad8cf0a8d74d28d83817871d30dddafc7',343,55,80,55),
        }
        component=components.get(key)
        if not component or records.get(key,{}).get('sha256')!=component[0]:return logo(key,width,height,color)
        _,iw,ih,cw,ch=component
        scale=min(width/cw,height/ch)
        cropped_w,cropped_h=cw*scale,ch*scale
        original=logo(key,iw*scale,ih*scale,color)
        return f'<span class="logo-component" data-native-component="{esc(key)}" style="display:inline-flex;align-items:center;justify-content:center;width:{float(width)}px;height:{float(height)}px;flex:none"><span style="display:block;overflow:hidden;width:{cropped_w}px;height:{cropped_h}px;flex:none;line-height:0">{original}</span></span>'
    renderer,_,_=registry()[style]
    body,css=renderer({'esc':esc,'logo':logo,'logo_component':logo_component,'photo':data_uri(photo,trim_alpha=True) if photo else '',
                       'background':data_uri(background) if background else '', 'brief':brief})
    scale=brief.get('photo_framing',{}).get('scale',1)
    if scale!=1:
        # Subject proportions differ. An explicit, validated fit changes only
        # the photograph inside the source frame; outer geometry/type are fixed.
        css+=f'\n[data-ref="photo"]>img{{transform:scale({scale});transform-origin:top center}}'
    if brief.get('mobile_safe_copy'):
        # Opt-in local text insets protect existing copy from the native mobile
        # avatar circle. Reference frame coordinates and type sizes stay fixed.
        css+='\n'+MOBILE_SAFE_COPY_CSS[style]
    base='*{box-sizing:border-box}html,body{margin:0;width:1584px;height:396px;overflow:hidden}.banner{position:relative;width:1584px;height:396px;overflow:hidden;font-family:Inter,Arial,sans-serif}h1,p{margin:0}.company-logo{vertical-align:middle}'
    if brief.get('company_brand'):
        from .company_brand import brand_styles
        fonts,overrides=brand_styles(root,brief['company_brand'])
        css+='\n'+overrides
    else:
        fonts=font_css()
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{fonts}\n{base}\n{css}</style></head><body><main class="banner reference-faithful {style}">{body}</main></body></html>'
