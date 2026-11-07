"""Explicit, offline company-brand overrides for the fixed reference layouts.

Every dependency is local, hash-bound and copied with each editable package.
The original reference mode never enters this path unless company_brand is set.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
from pathlib import Path


def validate_brand_css(css):
    """Allow authored visual rules, never independent resource dependencies.

    Escapes and at-rules are unnecessary in this deliberately small override
    format. A function allowlist also closes quoted image()/image-set() sources
    and future resource functions without attempting to guess their URL syntax.
    """
    if '\\' in css or re.search(r'</style', css, re.I):
        raise ValueError('Company stylesheet cannot contain CSS escapes or embedded markup.')
    plain = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    allowed = {
        'var', 'calc', 'min', 'max', 'clamp', 'env',
        'rgb', 'rgba', 'hsl', 'hsla', 'hwb', 'lab', 'lch', 'oklab', 'oklch', 'color', 'color-mix',
        'linear-gradient', 'radial-gradient', 'conic-gradient',
        'repeating-linear-gradient', 'repeating-radial-gradient', 'repeating-conic-gradient',
        'grayscale', 'brightness', 'contrast', 'hue-rotate', 'saturate', 'sepia', 'blur', 'drop-shadow', 'invert', 'opacity',
        'translate', 'translatex', 'translatey', 'translatez', 'translate3d',
        'scale', 'scalex', 'scaley', 'scalez', 'scale3d', 'rotate', 'rotatex', 'rotatey', 'rotatez', 'rotate3d',
        'skew', 'skewx', 'skewy', 'matrix', 'matrix3d', 'perspective', 'polygon', 'inset', 'circle', 'ellipse',
        'repeat', 'minmax', 'fit-content', 'not', 'is', 'where', 'has',
        'nth-child', 'nth-last-child', 'nth-of-type', 'nth-last-of-type',
    }
    functions = {name.lower() for name in re.findall(r'([-a-zA-Z][\w-]*)\s*\(', plain)}
    if '@' in plain or functions - allowed:
        raise ValueError('Company stylesheet must be authored overrides without external or unbound assets; unsupported CSS function or at-rule.')


def block_brand_network(context, blocked):
    """Fail closed if an undeclared remote asset reaches the offline browser."""
    def abort(route):
        blocked.append(route.request.url)
        route.abort('blockedbyclient')
    context.route(re.compile(r'^https?://', re.I), abort)


def validate_brand_spec(spec):
    if not isinstance(spec, dict) or set(spec) != {'manifest'}:
        raise ValueError('company_brand requires one explicit local manifest path.')
    path = spec['manifest']
    if (not isinstance(path, str) or Path(path).is_absolute() or '..' in Path(path).parts
            or not path.endswith('/brand.json')):
        raise ValueError('company_brand manifest must be a safe local brand.json path.')


def _local(root, relative):
    if (not isinstance(relative, str) or not relative or Path(relative).is_absolute()
            or '..' in Path(relative).parts):
        raise ValueError('Company brand assets require safe relative paths.')
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing or non-local company brand asset: {relative}')
    return path


def load_brand(asset_root, spec):
    """Validate a bundle and return its manifest plus complete dependency list."""
    validate_brand_spec(spec)
    manifest = _local(Path(asset_root), spec['manifest'])
    root = manifest.parent
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', data.get('id', '')):
        raise ValueError('Unsupported company brand manifest or invalid brand id.')
    if not isinstance(data.get('name'), str) or not data['name'].strip() or not str(data.get('website', '')).startswith('https://'):
        raise ValueError('Company brand requires its name and official HTTPS website.')
    palette = data.get('palette')
    if not isinstance(palette, dict) or not palette or any(
            not re.fullmatch(r'[a-z][a-z0-9_-]*', role) or not isinstance(value, str)
            or not re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})', value)
            for role, value in palette.items()):
        raise ValueError('Company brand palette requires named hexadecimal color roles.')
    files = [manifest]
    fonts = data.get('fonts')
    if not isinstance(fonts, list) or not fonts:
        raise ValueError('Company brand requires real local font files.')
    families = set()
    for font in fonts:
        family = font.get('family', '')
        if not isinstance(family, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _-]{0,99}', family):
            raise ValueError('Invalid company font family.')
        path = _local(root, font.get('path'))
        raw = path.read_bytes()
        if raw[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'wOFF', b'wOF2', b'ttcf'):
            raise ValueError(f'Company font is not a supported font file: {path.name}')
        if hashlib.sha256(raw).hexdigest() != font.get('sha256'):
            raise ValueError(f'Company font hash mismatch: {path.name}')
        if (not re.fullmatch(r'[1-9]00(?: [1-9]00)?', str(font.get('weight', '')))
                or font.get('style') not in ('normal', 'italic')
                or not str(font.get('source_url', '')).startswith('https://')):
            raise ValueError('Company fonts require weight, style and original HTTPS source URL.')
        families.add(family)
        files.append(path)
    typography = data.get('typography', {})
    if any(typography.get(key) not in families for key in ('display_family', 'body_family')):
        raise ValueError('Company display and body typography must use supplied local fonts.')
    stylesheet = _local(root, data.get('stylesheet'))
    css = stylesheet.read_text(encoding='utf-8')
    validate_brand_css(css)
    provenance = _local(root, data.get('provenance'))
    if not isinstance(json.loads(provenance.read_text(encoding='utf-8')), dict):
        raise ValueError('Company brand provenance must be a JSON object.')
    files.extend((stylesheet, provenance))
    return data, list(dict.fromkeys(files))


def brand_record(asset_root, spec):
    data, files = load_brand(asset_root, spec)
    root = Path(asset_root)
    return {key: data[key] for key in ('id', 'name', 'website', 'palette', 'typography')} | {
        'manifest': spec['manifest'],
        'files_sha256': {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }


def copy_brand_bundle(source_manifest, destination):
    """Copy only declared, validated dependencies; omit unrelated website files."""
    source_manifest, destination = Path(source_manifest), Path(destination)
    data, files = load_brand(source_manifest.parent.parent, {'manifest': source_manifest.parent.name + '/' + source_manifest.name})
    destination.mkdir(parents=True, exist_ok=True)
    for path in files:
        target = destination / path.relative_to(source_manifest.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.resolve() != target.resolve():
            shutil.copy2(path, target)
    return data


def brand_styles(asset_root, spec):
    data, _ = load_brand(asset_root, spec)
    root = (Path(asset_root) / spec['manifest']).parent
    faces = []
    for font in data['fonts']:
        raw = (root / font['path']).read_bytes()
        mime = 'font/woff2' if raw[:4] == b'wOF2' else 'font/woff' if raw[:4] == b'wOFF' else 'font/otf' if raw[:4] == b'OTTO' else 'font/ttf'
        faces.append("@font-face{font-family:'%s';src:url(data:%s;base64,%s);font-weight:%s;font-style:%s;font-display:block;}" % (
            font['family'], mime, base64.b64encode(raw).decode(), font['weight'], font['style']))
    body, display = (data['typography'][key] for key in ('body_family', 'display_family'))
    # Zero-specificity defaults replace all legacy font declarations while the
    # authored stylesheet can explicitly assign another supplied brand family.
    overrides = (f":where(.banner,.banner *){{font-family:'{body}'!important;font-synthesis:none}}\n"
                 f":where(.banner [data-ref=title],.banner [data-ref=title] *){{font-family:'{display}'!important}}\n")
    return '\n'.join(faces), overrides + (root / data['stylesheet']).read_text(encoding='utf-8')


def audit_brand_typography(page, data, design):
    families = sorted({font['family'] for font in data['fonts']})
    # Ask the browser to resolve each displayed weight/style using the same CSS
    # face-matching algorithm used to paint it. A regular face must never hide
    # a failed bold or italic face belonging to the same family. Variable-face
    # ranges and legitimate nearest-weight matches remain browser-resolved.
    font_report = page.evaluate('''async families => {
      const familyName=name=>name.split(',')[0].trim().replace(/^['"]|['"]$/g,'');
      const describe=font=>({family:familyName(font.family),weight:font.weight,style:font.style,
        stretch:font.stretch,status:font.status,loaded:font.status==='loaded'});
      const banner=document.querySelector('.banner'),groups=new Map();
      const walker=document.createTreeWalker(banner,NodeFilter.SHOW_TEXT);
      while(walker.nextNode()){
        const node=walker.currentNode,e=node.parentElement,text=node.textContent.trim();
        if(!text||e.closest('svg,script,style,[aria-hidden="true"]'))continue;
        const s=getComputedStyle(e);
        if(s.display==='none'||s.visibility==='hidden'||parseFloat(s.opacity)===0||!e.getClientRects().length)continue;
        const item={family:familyName(s.fontFamily),weight:s.fontWeight,style:s.fontStyle};
        const key=JSON.stringify(item),old=groups.get(key);
        if(old)old.text+=' '+text;else groups.set(key,{...item,text});
      }
      const used_faces=[];
      for(const group of groups.values()){
        const {text,...item}=group;
        if(!families.includes(item.family)){
          used_faces.push({...item,loaded:false,matching_faces:[],error:'Font family is outside the company brand'});continue;
        }
        try{
          const matching=await document.fonts.load(`${item.style} ${item.weight} 16px ${JSON.stringify(item.family)}`,text);
          const faces=matching.map(describe);
          used_faces.push({...item,loaded:faces.length>0&&faces.every(face=>face.loaded),matching_faces:faces});
        }catch(error){
          used_faces.push({...item,loaded:false,matching_faces:[],error:String(error)});
        }
      }
      return {used_faces,font_faces:[...document.fonts].map(describe).filter(face=>families.includes(face.family))};
    }''', families)
    failures = []
    used = sorted({item['font_family'].split(',')[0].strip(' \"\'') for item in design['text']})
    for family in used:
        if family not in families:
            failures.append(f'Banner text uses a font outside the company brand: {family}')
    for face in font_report['used_faces']:
        if not face['loaded']:
            failures.append(f'Company font face did not load: {face["family"]} weight {face["weight"]} style {face["style"]}')
    if used and not font_report['used_faces']:
        failures.append('No displayed company font faces could be audited.')
    return {'status': 'failed' if failures else 'passed', 'families_used': used,
            **font_report, 'failures': failures}
