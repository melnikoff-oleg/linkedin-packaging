"""Validation, local configuration and safe distribution. No network operations."""
import copy
import hashlib
import json
import math
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY_NAMES = ("APIFY_API_KEY", "KIE_AI_API_KEY", "FIRECRAWL_API_KEY")
BRIEF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        **{key: {"type": "string"} for key in [
            "name", "audience", "positioning", "selected_style", "headline", "banner_title",
            "banner_subtitle", "cta", "portrait_prompt", "rationale"]},
        "proof_points": {"type": "array", "items": {"type": "string"}},
        "proof_cards": {"type": "array", "items": {"type":"object", "additionalProperties":False,
            "properties":{key:{"type":"string"} for key in ('company_id','company','role','value','detail','source')},
            "required":['company_id','company','role','value','detail','source']}},
        "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False,
            "properties": {"claim": {"type": "string"}, "source": {"type": "string"}},
            "required": ["claim", "source"]}},
    },
}
BRIEF_SCHEMA["required"] = list(BRIEF_SCHEMA["properties"])


def reference_slot_contract(style):
    """Expose structure and lengths, never the fixture person's facts."""
    from .reference_layout import registry, content_schema
    if style not in registry():
        raise ValueError('Unknown reference template')
    example=registry()[style][1]
    schema=content_schema(example)
    budgets={};style_values={}
    def walk(value,path):
        if isinstance(value,dict):
            for key,item in value.items():walk(item,path+'.'+key)
        elif isinstance(value,list):
            for index,item in enumerate(value):walk(item,f'{path}[{index}]')
        elif isinstance(value,bool):
            style_values[path]=value
        elif isinstance(value,str):
            if path.endswith('.color'):
                style_values[path]=value
            # Array length and typography are fixed. This draft budget does not
            # certify glyph fit; the rendered reference QA remains authoritative.
            is_logo=any(token in path for token in ('.logos[','.logo_keys[','.key'))
            budgets[path]=60 if is_logo else max(3,len(value)+max(2,len(value)//10))
    walk(example,'reference_content')
    return {'schema':schema,'character_budgets':budgets,'fixed_style_values':style_values,
            'rule':'Keep every slot and line count. Rewrite copy to fit; never change layout, font size or spacing. Empty unavailable proof/logo slots are allowed; invented facts are not.'}


def validate_reference_copy_budgets(brief):
    contract=reference_slot_contract(brief['selected_style'])
    budgets=contract['character_budgets'];style_values=contract['fixed_style_values']
    def walk(value,path):
        if isinstance(value,dict):
            for key,item in value.items():walk(item,path+'.'+key)
        elif isinstance(value,list):
            for index,item in enumerate(value):walk(item,f'{path}[{index}]')
        elif path in style_values and value!=style_values[path]:
            raise ValueError(f'Reference style value changed at {path}; preserve the reference treatment.')
        elif isinstance(value,str) and len(value)>budgets.get(path,500):
            raise ValueError(f'Reference copy exceeds the fixed phrase budget at {path}; rewrite, never resize the layout.')
    walk(brief['reference_content'],'reference_content')


def reference_brief_schema(style):
    """A subject-neutral generation schema for one fixed reference layout."""
    schema=copy.deepcopy(BRIEF_SCHEMA)
    schema['properties']['selected_style']={'type':'string','enum':[style]}
    schema['properties']['layout_mode']={'type':'string','enum':['reference-faithful']}
    schema['properties']['reference_content']=reference_slot_contract(style)['schema']
    for key in ('proof_cards','proof_points'):
        schema['properties'][key]['maxItems']=0
    schema['required']=list(schema['properties'])
    return schema


def load_keys(root=ROOT, env=None):
    values = {}
    for filename in ("api_keys.md", ".env"):
        path = Path(root) / filename
        if path.is_file():
            for line in path.read_text().splitlines():
                key, sep, value = line.partition("=")
                if sep and key.strip() in KEY_NAMES:
                    value=value.strip().strip("\"'")
                    if value and not value.startswith('your_'):
                        values[key.strip()] = value
    environment = os.environ if env is None else env
    values.update({key: environment[key] for key in KEY_NAMES if environment.get(key)})
    return values


def safe_slug(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", value):
        raise ValueError("Use a lowercase slug containing letters, digits, hyphens or underscores.")
    return value


def validate_brief(data):
    if not isinstance(data, dict):
        raise ValueError("Brief must be a JSON object")
    for key, spec in BRIEF_SCHEMA["properties"].items():
        if key=='proof_cards' and key not in data:
            continue  # Older saved briefs remain readable; new generated briefs require cards.
        if key not in data:
            raise ValueError(f"Missing brief field: {key}")
        if spec["type"] == "string" and not isinstance(data[key], str):
            raise ValueError(f"{key} must be text")
    limits = {"headline": 220, "banner_title": 90, "banner_subtitle": 120, "cta": 48}
    for key, limit in limits.items():
        if len(data[key]) > limit:
            raise ValueError(f"{key} exceeds {limit} characters; rewrite instead of truncating")
    if not data["headline"].strip() or not data["banner_title"].strip():
        raise ValueError("headline and banner_title must not be empty")
    safe_slug(data["selected_style"])
    if not isinstance(data["proof_points"], list) or len(data["proof_points"]) > 3:
        raise ValueError("proof_points must be a list of up to three claims")
    if any(not isinstance(p, str) or len(p) > 65 for p in data["proof_points"]):
        raise ValueError("proof_points must be strings of at most 65 characters")
    if 'proof_cards' in data and data['proof_points']:
        raise ValueError('proof_points must be empty in modern briefs; place supported facts in visible banner text or proof_cards.')
    if not isinstance(data["evidence"], list):
        raise ValueError("evidence must be a list")
    for item in data["evidence"]:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ("claim", "source")):
            raise ValueError("Every evidence entry needs claim and source text")
    if data["proof_points"] and not data["evidence"]:
        raise ValueError("proof_points require evidence; never invent credibility")
    cards=data.get('proof_cards',[])
    if not isinstance(cards,list) or len(cards)>3:
        raise ValueError('proof_cards must contain up to three named, source-backed cases')
    for card in cards:
        if not isinstance(card,dict) or set(card)!={'company_id','company','role','value','detail','source'}:
            raise ValueError('Each proof card needs company_id, company, role, value, detail and source')
        limits={'company_id':60,'company':42,'role':42,'value':42,'detail':100,'source':500}
        for key,limit in limits.items():
            if not isinstance(card[key],str) or len(card[key])>limit or (key not in ('company_id','role','detail') and not card[key].strip()):
                raise ValueError(f'Invalid proof_cards {key}; use source-linked concise text')
        if card['company_id'] and not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',card['company_id']):
            raise ValueError('Invalid proof_cards company_id')
    if cards and not data['evidence']:
        raise ValueError('proof_cards require evidence; never invent credibility')
    logos=data.get('logo_assets',{})
    if not isinstance(logos,dict) or any(not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',key) or value!='logos/'+key+'.png' for key,value in logos.items()):
        raise ValueError('logo_assets must use safe package-relative logos/<company_id>.png paths')
    if 'layout_mode' in data and data['layout_mode'] not in ('reference-faithful', 'evidence'):
        raise ValueError('Unknown layout_mode')
    if data.get('layout_mode')=='reference-faithful':
        from .reference_layout import validate_reference_content
        validate_reference_content(data)
        if not data['evidence']:
            raise ValueError('Reference content requires source evidence entries; never invent visible proof.')
        if data.get('proof_cards') or data.get('proof_points'):
            raise ValueError('Reference briefs keep proof_cards and proof_points empty; visible evidence belongs in reference_content.')
    elif 'reference_content' in data:
        raise ValueError('reference_content requires layout_mode=reference-faithful')
    if 'photo_framing' in data:
        from .visual_assets import BANNER_PHOTO_STYLES
        framing = data['photo_framing']
        scale = framing.get('scale') if isinstance(framing, dict) else None
        if (not isinstance(framing, dict) or set(framing) != {'scale'} or
                isinstance(scale, bool) or not isinstance(scale, (int, float)) or
                not .5 <= scale <= 1 or not math.isfinite(scale) or
                data.get('layout_mode') != 'reference-faithful' or
                data['selected_style'] not in BANNER_PHOTO_STYLES):
            raise ValueError('photo_framing requires a reference photo layout and scale from 0.5 to 1.')
    if 'mobile_safe_copy' in data:
        from .reference_layout import MOBILE_SAFE_COPY_CSS
        if (type(data['mobile_safe_copy']) is not bool or
                data.get('layout_mode') != 'reference-faithful' or
                data['selected_style'] not in MOBILE_SAFE_COPY_CSS):
            raise ValueError('mobile_safe_copy requires a boolean in a supported reference layout.')
    if 'company_brand' in data:
        from .company_brand import validate_brand_spec
        if data.get('layout_mode') != 'reference-faithful':
            raise ValueError('company_brand requires a reference-faithful composition.')
        validate_brand_spec(data['company_brand'])
    return data


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _validate_finalized_examples(root):
    """Drafts are portable; an existing example release must still be current.

    Read the manifest against the supplied export root, never the checkout's
    script globals. Recheck local sources and the latest matching independent
    reviews before creating the archive, including later rejecting reviews.
    """
    from .evidence import _reference_logo_slots
    from .reference_review import FILES
    from .review import PACKAGE_FILES
    from .styles import STYLES
    from .visual_assets import BANNER_PHOTO_STYLES
    from .company_brand import load_brand, brand_record

    downloads = ('banner.png', 'portrait.png', 'preview.png', 'headline.txt')
    outputs = set(FILES) | set(downloads) | {'preview-mobile.png', 'reference-desktop.png'}
    backgrounds = {'mattgray1': 'mountain-background-reference.png',
                   'liamkarlsson': 'liam-background-reference.png'}

    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))

    def digest(path):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Release files must remain inside the export root.')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def hashes(base, names):
        if any(not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts for name in names):
            raise ValueError('Invalid release hash path.')
        return {name: digest(base / name) for name in names}

    def review(folder, style, pattern, expected, buyer=False):
        for path in sorted((folder / 'reviews').glob(pattern), key=lambda p: p.stem, reverse=True):
            report = read(path)
            entries = report.get('reviews', []) if buyer else [report.get('reviews', {}).get(style)]
            for item in entries:
                if not isinstance(item, dict) or (buyer and item.get('style') != style) or item.get('sha256') != expected:
                    continue
                if (item.get('verdict') != 'accept' or
                        (buyer and item.get('required_findings') != []) or
                        (not buyer and (not isinstance(item.get('findings'), list) or
                         any(isinstance(f, dict) and f.get('required') is True for f in item['findings'])))):
                    raise ValueError(f'Independent review no longer accepts {style}.')
                return {**item, 'report': str(path.relative_to(root)), 'report_sha256': digest(path)}
        raise ValueError(f'Current independent review missing for {style}.')

    for folder in sorted((root / 'examples').glob('*')):
        if not folder.is_dir() or not ((folder / 'manifest.json').exists() or any(folder.rglob('package.zip'))):
            continue
        try:
            account, manifest = read(folder / 'account.json'), read(folder / 'manifest.json')
            rows = manifest['packages']
            if (manifest.get('account') != folder.name or manifest.get('subject') != account['name'] or
                    manifest.get('reference_count') != len(STYLES) or manifest.get('download_files') != list(downloads) or
                    manifest.get('acceptance') != 'all-ten-current-reference-and-independent-buyer-reviews-accepted' or
                    not isinstance(rows, list) or len(rows) != len(STYLES) or
                    {row['style'] for row in rows} != set(STYLES)):
                raise ValueError('A complete current ten-style manifest is required.')
            if set(folder.rglob('package.zip')) != {folder / 'results' / style / 'package.zip' for style in STYLES}:
                raise ValueError('Only the ten current finalized package ZIPs may be exported.')
            if account.get('company_brand') and manifest.get('company_brand') != brand_record(folder, account['company_brand']):
                raise ValueError('Finalized company brand source record changed or is missing.')
            for row in rows:
                style = row['style']; output = folder / 'results' / style
                brief, qa = read(output / 'brief.json'), read(output / 'qa.json')
                if (brief.get('name') != account['name'] or brief.get('selected_style') != style or
                        brief.get('layout_mode') != 'reference-faithful' or row.get('technical_qa') != 'passed' or
                        qa.get('passed') is not True or qa.get('failures') != []):
                    raise ValueError(f'Current account identity and technical QA required: {style}.')
                logos = brief.get('logo_assets', {})
                if not isinstance(logos, dict) or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', key) or
                        value != f'logos/{key}.png' for key, value in logos.items()):
                    raise ValueError('Invalid released logo asset paths.')
                files = outputs | {'brief.json', 'banner.html', 'qa.json', 'visual-assets.json', 'logos/provenance.json'} | set(logos.values())
                if account.get('company_brand'):
                    if brief.get('company_brand') != {'manifest': 'company-brand/brand.json'}:
                        raise ValueError('Released company brand is missing its local bundle.')
                    _, brand_files = load_brand(output, brief['company_brand'])
                    files.update(path.relative_to(output).as_posix() for path in brand_files)
                    current_brand = brand_record(output, brief['company_brand'])
                    if (qa.get('company_brand') != current_brand or row.get('company_brand') != current_brand
                            or qa.get('company_brand_typography', {}).get('status') != 'passed'):
                        raise ValueError('Released company brand or typography evidence changed.')
                elif brief.get('company_brand'):
                    raise ValueError('Released brand override is not authorized by the account.')
                if (row.get('sha256') != hashes(output, files) or
                        qa.get('example_output_sha256') != hashes(output, outputs) or
                        qa.get('input_sha256') != hashes(output, ('brief.json', 'banner.html')) or
                        qa.get('render_sha256') != hashes(output, PACKAGE_FILES)):
                    raise ValueError(f'Released files changed or hashes missing: {style}.')

                assets = account.get('assets', {})
                settings = {key: assets[key] for key in ('portrait', 'banner_photo') if key in assets}
                settings.update(assets.get('styles', {}).get(style, {}))
                def asset(relative):
                    if not isinstance(relative, str) or not relative.startswith('source/'):
                        raise ValueError('Invalid account source path.')
                    path = (folder / relative).resolve()
                    if not path.is_relative_to((folder / 'source').resolve()):
                        raise ValueError('Account source escapes its own folder.')
                    return path
                sources = [folder / 'account.json', folder / 'source/profile.json',
                           folder / 'source/briefs' / f'{style}.json',
                           asset(settings.get('portrait', f'source/portraits/{style}.png'))]
                if account.get('company_brand'):
                    if account['company_brand'].get('manifest') != 'source/company-brand/brand.json':
                        raise ValueError('Company brand must belong to its account source tree.')
                    _, brand_sources = load_brand(folder, account['company_brand'])
                    sources.extend(brand_sources)
                    original_brand = brand_record(folder, account['company_brand'])
                    if {Path(name).relative_to('source').as_posix(): value for name, value in original_brand['files_sha256'].items()} != current_brand['files_sha256']:
                        raise ValueError('Released company brand differs from its account source bundle.')
                if style in BANNER_PHOTO_STYLES:
                    sources.append(asset(settings.get('banner_photo', f'source/banner-photos/{style}.png')))
                if settings.get('background'):
                    sources.append(asset(settings['background']))
                elif style in backgrounds:
                    sources.append(root / 'test_account/source' / backgrounds[style])
                supplemental = folder / 'source/supplemental-evidence.json'
                if supplemental.exists():
                    sources.append(supplemental)
                source_brief = read(folder / 'source/briefs' / f'{style}.json')
                for container, index in _reference_logo_slots(source_brief['reference_content']):
                    key = container[index]
                    if not key:
                        continue
                    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', key):
                        raise ValueError('Invalid source logo key.')
                    sources.extend(folder / 'source/company-logos/curated' / (key + ext) for ext in ('.png', '.json'))
                source_hashes = {str(path.relative_to(root)): digest(path) for path in sources}
                reference = root / 'references' / style
                references = (reference / 'banner.jpg', reference / 'headline.txt', *reference.glob('portrait.*'))
                reference_hashes = {str(path.relative_to(root)): digest(path) for path in references}
                if (row.get('source_sha256') != source_hashes or qa.get('account_source_sha256') != source_hashes or
                        row.get('reference_source_sha256') != reference_hashes or qa.get('reference_source_sha256') != reference_hashes):
                    raise ValueError(f'Released account or reference sources changed: {style}.')
                if row.get('visual_review') != review(folder, style, 'reference-independent-*.json', hashes(output, FILES)):
                    raise ValueError(f'Reference review changed since finalization: {style}.')
                if row.get('buyer_review') != review(folder, style, 'reference-buyer-release*.json',
                        hashes(output, ('review-desktop.png', 'review-mobile.png')), buyer=True):
                    raise ValueError(f'Buyer review changed since finalization: {style}.')
                package = output / 'package.zip'
                if row.get('package_zip_sha256') != digest(package):
                    raise ValueError(f'Released ZIP changed: {style}.')
                with zipfile.ZipFile(package) as archive:
                    if archive.namelist() != list(downloads) or any(
                            hashlib.sha256(archive.read(name)).hexdigest() != row['sha256'][name] for name in downloads):
                        raise ValueError(f'Released ZIP contents differ from current deliverables: {style}.')
        except (OSError, ValueError, TypeError, KeyError, AttributeError, zipfile.BadZipFile) as error:
            raise ValueError(f'Export blocked: finalized example {folder.name} is stale or incomplete. {error}') from None


def export_shareable(root, output):
    """Build a portable ZIP from known project directories; never ship live credentials."""
    root, output = Path(root).resolve(), Path(output).resolve()
    _validate_finalized_examples(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    allowed_dirs = {"linkedin_pack", "tests", "assets", "scripts", "docs", "prompts", "references", "test_account", "examples", "brands"}
    allowed_files = {"README.md", "WORKFLOW.md", "AGENTS.md", "LICENSE", "THIRD_PARTY.md", "pyproject.toml",
                     "setup.sh", "setup.ps1", "package.sh", ".env.example", ".gitignore", "reference_accounts.md", "test_account.md"}
    forbidden = {"api_keys.md", ".env", ".cache", "__pycache__", ".venv", "dist", ".git", ".DS_Store"}
    secrets = [value.encode() for value in load_keys(root).values() if len(value) >= 12]
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            if not path.is_file() or path.is_symlink() or any(p in forbidden for p in rel.parts):
                continue
            if len(rel.parts) == 1 and path.name not in allowed_files:
                continue
            if len(rel.parts) > 1 and rel.parts[0] not in allowed_dirs:
                continue
            if path.name.endswith((".pyc", ".log")) or path.name.startswith(".env") and path.name != ".env.example":
                continue
            content = path.read_bytes()
            if any(secret in content for secret in secrets):
                raise ValueError(f"Export blocked: credential detected in {rel}")
            archive.writestr("linkedin-package/" + rel.as_posix(), content)
    return output
