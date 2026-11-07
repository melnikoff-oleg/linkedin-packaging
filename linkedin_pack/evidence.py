"""Source-linked case evidence and original company logos, without invented proof."""
from __future__ import annotations
import copy
import hashlib
import io
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from PIL import Image, ImageOps
from .core import write_json
from .providers.apify import _image_url

MAX_LOGO_BYTES = 8_000_000
_METRIC = re.compile(r'(?<!\w)(?:[~≈<>$]|about\s+|roughly\s+|approximately\s+|under\s+)?\s*(\d+(?:\.\d+)?)(?:\+)?\s*(%|×|x\b|seconds?\b|secs?\b|s\b|minutes?\b|mins?\b|ms\b|million\b|billion\b|[mb]\b)', re.I)
_STORY_WORDS = frozenset('outage outages incremental rewrite spreadsheet prototype prototypes pricing quote quotes mentoring mentor authorization fedramp iso27001 compliance acquisition profitability profitable migration migrated latency benchmark bootstrapped patent patents turnaround transplant manufacturing robotics laboratory trials clinical distributed parallel'.split())


def _metrics(text):
    result = set()
    for match in _METRIC.finditer(text or ''):
        number,unit = match.groups();unit=unit.lower()
        if unit in ('seconds','second','sec','secs'):unit='s'
        if unit in ('minutes','minute','min','mins'):unit='min'
        if unit=='×':unit='x'
        if unit=='million':unit='m'
        if unit=='billion':unit='b'
        result.add(number+unit)
    return result


def _story_tokens(text):
    text=text or ''
    words = set(re.findall(r'[a-z]+\d*', text.lower().replace('iso 27001','iso27001')))
    # The same concrete event can be a verb in copy and a noun in its source.
    # Keep this finite: broad stemming would turn generic language into proof.
    words = {'acquisition' if word in ('acquired','acquisitions') else word for word in words}
    # Named projects such as HelloMint/1Quote can anchor a concrete mechanism too.
    names={value.lower() for value in re.findall(r'\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+|\d+[A-Z][A-Za-z]+)\b',text)}
    return (words & _STORY_WORDS) | names


def specificity_inventory(profile):
    """Keep evidence attached to its actual company, role and source section."""
    rows=[]
    for index,item in enumerate(profile.get('experience',[])[:40]):
        if not isinstance(item,dict):continue
        description=str(item.get('description') or '')
        company_id=str(item.get('companyId') or '')
        end=(item.get('endDate') or {}).get('text','') if isinstance(item.get('endDate'),dict) else ''
        rows.append({
            'company_id':company_id, 'company':str(item.get('companyName') or ''),
            'role':str(item.get('position') or ''), 'relationship':'current role' if end.lower()=='present' else 'past role',
            'source':f"{profile.get('url','user-provided context')} · experience[{index}], {item.get('companyName','')}",
            'company_url':str(item.get('companyLinkedinUrl') or ''),
            'description':description, 'metric_tokens':sorted(_metrics(description)),
            'story_tokens':sorted(_story_tokens(description)),
            'logo_available':bool(_image_url(item.get('companyLogo'))),
            'qualification':'Profile-reported role/results; preserve approximation and contribution scope. Employment is not a client endorsement.',
        })
    return rows


def _card_rows(plan, inventory):
    by_id={}
    for row in inventory:
        if row['company_id']:by_id.setdefault(row['company_id'],[]).append(row)
    for card in plan.get('proof_cards',[]):
        company_id=card.get('company_id','')
        company=card.get('company','').strip()
        if not company_id:
            label=re.sub(r'[^a-z0-9]','',company.lower())
            rows=[row for row in inventory if label and label in re.sub(r'[^a-z0-9]','',' '.join(str(row[k]) for k in ('company','role','description')).lower())]
            if not rows:raise ValueError('Named proof-card company or product is absent from source experience; use an exact source identity.')
            yield card,rows
            continue
        if company_id not in by_id:
            raise ValueError('proof_cards company_id must identify a company in the subject source profile.')
        def brand(value):
            value=re.sub(r'\b(?:incorporated|inc|llc|ltd|limited|corporation|corp)\b','',value.lower())
            return re.sub(r'[^a-z0-9]','',value)
        actual=brand(by_id[company_id][0]['company']);label=brand(company)
        explicit_alias=any(label in re.sub(r'[^a-z0-9]','',(row['role']+' '+row['description']).lower()) for row in by_id[company_id])
        if label!=actual and not (actual and re.fullmatch(re.escape(actual)+r'\d+',label) and explicit_alias):
            raise ValueError('Logo company label differs from its source brand. Use an empty company_id for a product/subsidiary case instead of mislabeling the parent logo.')
        yield card,by_id[company_id]


def _supplement_rows(records, inventory):
    rows=[]
    for item in records or []:
        if not isinstance(item,dict) or any(not isinstance(item.get(key),str) or not item[key].strip() for key in ('company','description','source')):
            raise ValueError('Supplemental evidence requires company, exact source description and source URL/section.')
        if item.get('company_id'):
            list(_card_rows({'proof_cards':[item]},inventory))
        description=item['description']
        rows.append({'company_id':item.get('company_id',''),'company':item['company'],
            'role':item.get('role',''),'relationship':'source-described relationship','source':item['source'],
            'description':description,'metric_tokens':sorted(_metrics(description)),
            'story_tokens':sorted(_story_tokens(description)),'company_url':'','logo_available':False,
            'qualification':'Supplemental source-reported case; retain exact source and attribution.'})
    return rows


def _website_rows(website, cards):
    if not website:return []
    url=website.get('source_url');markdown=website.get('markdown') or ''
    if not isinstance(url,str) or not isinstance(markdown,str):return []
    sections=re.split(r'(?m)(?=^#{1,6}\s+)',markdown)
    # A flat page has no named case headings; keep paragraph boundaries instead.
    if len(sections)==1:sections=re.split(r'\n\s*\n',markdown)
    records=[]
    for card in cards:
        if url not in card.get('source',''):continue
        company=card.get('company','')
        if not company:continue
        matches=[section for section in sections if company.casefold() in section.casefold()]
        if matches:
            records.append({'company_id':card.get('company_id',''),'company':company,
                'role':card.get('role',''),'description':'\n'.join(matches),'source':url})
    return records


def _reference_logo_slots(content):
    """Mutable locations for logo keys; color/text fields are never asset paths."""
    slots=[]
    def walk(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ('logos','logo_keys') and isinstance(item,list):
                    slots.extend((item,index) for index in range(len(item)))
                elif key=='key' and isinstance(item,str):
                    slots.append((value,key))
                else:walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    walk(content)
    return slots


def _reference_visible_groups(content):
    """Keep a composed title/card together, without joining unrelated cases."""
    def text(value):
        if isinstance(value,str):return value
        if isinstance(value,list):return ' '.join(text(item) for item in value)
        if isinstance(value,dict):
            return ' '.join(text(item) for key,item in value.items()
                            if key not in ('logos','logo_keys','key','color','accent'))
        return ''
    groups=[]
    title_fields={key for key in content if key.startswith('title')}
    if title_fields:groups.append(' '.join(text(value) for key,value in content.items() if key in title_fields))
    support_fields={key for key in content if key.startswith('support') and key!='support_accent'}
    if support_fields:groups.append(' '.join(text(value) for key,value in content.items() if key in support_fields))
    for key,value in content.items():
        if key in title_fields|support_fields or key in ('logos','logo_keys','support_accent'):continue
        if isinstance(value,list):groups.extend(text(item) for item in value)
        else:groups.append(text(value))
    return [group.strip() for group in groups if group.strip()]


def _reference_named_cases(content):
    cases=[]
    def walk(value):
        if isinstance(value,dict):
            company=value.get('company') or (value.get('name') if 'key' in value else None)
            if isinstance(company,str) and company.strip():
                body=' '.join(str(value.get(key,'')) for key in ('role','text','name','detail','value'))
                cases.append((company.strip(),body))
            for item in value.values():walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    walk(content)
    return cases


def _company_label(value):
    # Normalize presentation punctuation and legal suffixes, not similar brands.
    return re.sub(r'(?:[,\s]+(?:incorporated|inc|llc|ltd|limited|corporation|corp)\.?)+$',
                  '',str(value).strip(),flags=re.I).strip()


def _company_key(value):
    return re.sub(r'[^a-z0-9]','',_company_label(value).casefold())


_ROLE_SCOPE_WORDS = frozenset('and of the for platform platforms infrastructure infra engineering product products technology tech software data analytics ai ml cloud security operations devops sre reliability services systems consumer growth enterprise commercial business sales marketing finance people human resources legal strategy design research development team teams department departments division divisions function functions regional region regions global international domestic corporate internal external north south east west central middle america american americas europe european asia asian pacific asiapacific africa african latin us usa uk eu emea apac latam na anz'.split())


def _role_scope_qualifier(value):
    # Capitalization alone cannot turn an employer's team/function/region into
    # another company. Treat known functional/geographic phrases conservatively
    # as job scope, including combinations such as Infrastructure - APAC.
    words=set(re.findall(r'[a-z]+',value.casefold().replace('.','')))
    return bool(words and words <= _ROLE_SCOPE_WORDS)


def _role_case_names(row):
    """Explicit operating-company annotations, never incidental description names.

    LinkedIn often changes a historical company record to its acquirer's page.
    A role such as CTO (ForeverCar) or VP Engineering [Digital H2O]
    can identify a historical operating company when the source also explicitly
    names that company in a role or acquisition statement. A capitalized
    parenthetical alone is insufficient: retain the employer when ambiguous.
    Functional/team/region qualifiers do not reassign its claims.
    """
    role=row.get('role','')
    candidates=re.findall(r'[\[(]([^]\)]+)[]\)]',role)
    match=re.search(r'\b(?:CTO|CEO|CPO|CIO|chief (?:technology|executive|product|information) officer)\s+(?:of|at|@)\s+(.+)$',role,re.I)
    if match:candidates.append(match.group(1))
    names=[]
    generic={'interim','acting','contract','contractor','consultant','consulting',
             'full time','part time','remote','temporary','freelance'}
    for candidate in candidates:
        candidate=re.split(r'\s*[-–—;,]\s*(?=acquired\b|now\b|formerly\b)|\s+acquired by\b',candidate,flags=re.I)[0].strip()
        if not candidate or len(candidate.split())>8 or re.sub(r'[-_]',' ',candidate.casefold()) in generic:
            continue
        name=r'(?<![a-z0-9])'+re.escape(candidate)+r'(?![a-z0-9])'
        source=role+' '+str(row.get('description') or '')
        acquisition=bool(re.search(name+r'\s*(?:[-–—;,]\s*)?(?:(?:was|is|has been)\s+)?acquired by\b',source,re.I))
        operating_role=bool(re.search(r'\b(?:CTO|CEO|CPO|CIO|chief (?:technology|executive|product|information) officer)\s*(?:of|at|@)\s*'+name,source,re.I))
        same_company=_company_key(candidate)==_company_key(row['company'])
        # A bare annotation can be a team, geography or temporary responsibility.
        # Reassign only with explicit source corroboration; otherwise leave the
        # source employer intact. This parser cannot establish undocumented aliases.
        if (same_company or acquisition or operating_role) and (not _role_scope_qualifier(candidate) or acquisition or same_company):
            names.append(candidate)
    return names


def _case_bindings(inventory):
    """Join evidence only through exact names or aliases explicit in one role."""
    groups=[]
    for row in inventory:
        company=row['company'];aliases=_role_case_names(row)
        names=aliases or [company]
        actual=_company_key(company)
        # A source explicitly using Factor_ and Factor 75 establishes both names.
        # A different acquirer name (e.g. CUNA vs ForeverCar) does not.
        if aliases and any(actual and (actual==_company_key(alias) or
                re.fullmatch(re.escape(actual)+r'\d+',_company_key(alias)) or
                re.fullmatch(re.escape(_company_key(alias))+r'\d+',actual)) for alias in aliases):
            names=[company]+aliases
        keys={_company_key(name) for name in names if _company_key(name)}
        if not keys:continue
        matches=[group for group in groups if group['keys']&keys]
        group={'keys':keys,'names':set(names),'rows':[row]}
        for previous in matches:
            group['keys'].update(previous['keys']);group['names'].update(previous['names'])
            group['rows'].extend(previous['rows']);groups.remove(previous)
        groups.append(group)
    # Keep known parent names recognizable but without borrowing child metrics.
    for row in inventory:
        key=_company_key(row['company'])
        if key and not any(key in group['keys'] for group in groups):
            groups.append({'keys':{key},'names':{row['company']},'rows':[]})
    return groups


def _mentions_company(text,company):
    tokens=re.findall(r'[a-z]+|\d+',_company_label(company).casefold())
    return bool(tokens and re.search(r'(?<![a-z0-9])'+r'[\W_]*'.join(map(re.escape,tokens))+r'(?![a-z0-9])',text.casefold()))


def _brand_in_role(label,item):
    """Alias must identify a documented role, not a parent or incidental client."""
    pattern=r'(?<![a-z0-9])'+r'\s*'.join(re.escape(word) for word in label.casefold().split())+r'(?![a-z0-9])'
    return bool(label.strip() and re.search(pattern,' '.join(str(item.get(key) or '') for key in ('companyName','position')).casefold()))


def _curated_reference_alias(cache,key,profile):
    folder=Path(cache)/'curated';path=folder/(key+'.png');meta=folder/(key+'.json')
    if not path.exists() and not meta.exists():return None
    if not path.is_file() or not meta.is_file() or path.is_symlink() or meta.is_symlink():
        raise ValueError('Curated reference logo needs local PNG and provenance.')
    record=json.loads(meta.read_text())
    if not isinstance(record,dict):raise ValueError('Curated reference logo provenance must be an object.')
    label=record.get('profile_company_name') or record.get('company') or ''
    if not any(_brand_in_role(label,item) for item in profile.get('experience',[]) if isinstance(item,dict)):
        raise ValueError('Curated reference logo identity is absent from the subject source roles.')
    if record.get('company_id') not in ('',key):
        raise ValueError('Curated reference alias must not relabel a parent company ID.')
    if record.get('source_type') not in ('official-brand-asset','official-investor-portfolio-brand-asset'):
        raise ValueError('Curated reference logo requires original brand-asset provenance.')
    for field in ('source_url','source_page'):
        parsed=urlsplit(str(record.get(field,'')))
        if parsed.scheme!='https' or not parsed.hostname:raise ValueError('Curated reference logo needs HTTPS source provenance.')
    data=path.read_bytes();_png_logo(data)
    if record.get('sha256')!=hashlib.sha256(data).hexdigest():raise ValueError('Curated reference logo hash mismatch.')
    if not _transparent_logo(data):raise ValueError('Curated reference logo needs an original transparent background.')
    return path,record


def _transparent_logo(data):
    with Image.open(io.BytesIO(data)) as im:
        alpha=im.convert('RGBA').getchannel('A');histogram=alpha.histogram()
        return sum(histogram[:16])>=im.width*im.height*.01 and alpha.getextrema()[1]>=128


def reference_logo_options(profile,cache_dir=None):
    """Subject-specific identities only; never expose the Kal fixture's marks."""
    options=[]
    for row in specificity_inventory(profile):
        if row['company_id'] and row['logo_available']:
            options.append({'key':row['company_id'],'company':row['company'],'role':row['role'],
                            'relationship':row['relationship'],'source':row['source']})
    if cache_dir:
        for meta in sorted((Path(cache_dir)/'curated').glob('*.json')):
            key=meta.stem
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',key) or any(option['key']==key for option in options):continue
            try:asset=_curated_reference_alias(cache_dir,key,profile)
            except (ValueError,OSError,TypeError):continue
            if asset:
                record=asset[1]
                options.append({'key':key,'company':record.get('company') or record['profile_company_name'],
                                'relationship':record.get('relationship','documented role; not endorsement'),
                                'source':record['source_page']})
    return options


def _collect_reference_logos(plan,profile,destination,cache_dir=None):
    slots=_reference_logo_slots(plan['reference_content'])
    ids=list(dict.fromkeys(container[index] for container,index in slots if container[index]))
    if any(not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',key) for key in ids):
        raise ValueError('Invalid reference logo key')
    if len(ids)>10:raise ValueError('Reference layout supports at most ten original logo identities.')
    cache=Path(cache_dir) if cache_dir else Path(destination)/'logos'
    by_id={str(item.get('companyId')):item for item in profile.get('experience',[]) if isinstance(item,dict)}
    # In layouts with a visible company name beside its mark, the named brand
    # must match that exact asset identity, never a parent-company convenience.
    def bindings(value):
        if isinstance(value,dict):
            if isinstance(value.get('key'),str) and value['key'] and value.get('name'):
                key=value['key'];name=value['name']
                if key in by_id:
                    list(_card_rows({'proof_cards':[{'company_id':key,'company':name}]},specificity_inventory(profile)))
                else:
                    asset=_curated_reference_alias(cache,key,profile)
                    if asset and re.sub(r'[^a-z0-9]','',name.casefold())!=re.sub(r'[^a-z0-9]','',str(asset[1].get('company') or asset[1]['profile_company_name']).casefold()):
                        raise ValueError('Reference logo name must match the product asset, not its parent.')
            for item in value.values():bindings(item)
        elif isinstance(value,list):
            for item in value:bindings(item)
    bindings(plan['reference_content'])
    direct=[key for key in ids if key in by_id]
    assets=collect_company_logos(profile,direct,destination,cache_dir=cache,max_logos=10)
    folder=Path(destination)/'logos';record_path=folder/'provenance.json'
    records=json.loads(record_path.read_text()) if record_path.exists() else {}
    for key in ids:
        if key in by_id:continue
        asset=_curated_reference_alias(cache,key,profile)
        if not asset:raise ValueError('Reference logo key is absent from source companies and verified product-logo provenance.')
        path,record=asset;target=folder/(key+'.png');folder.mkdir(parents=True,exist_ok=True)
        if path.resolve()!=target.resolve():shutil.copyfile(path,target)
        assets[key]='logos/'+key+'.png';records[key]=record
    omitted=[]
    for key in ids:
        path=Path(destination)/assets[key] if key in assets else None
        if path is None or not _transparent_logo(path.read_bytes()):
            omitted.append({'key':key,'reason':'No original transparent logo available; reserved slot remains empty.'})
            assets.pop(key,None);records.pop(key,None)
            for container,index in slots:
                if container[index]==key:container[index]=''
    write_json(record_path,records)
    plan['logo_preparation']={'omitted':omitted,'rule':'Original transparent marks only. No background reconstruction, parent substitution or fabricated endorsement.'}
    return assets


def _visible_copy_fragments(plan):
    """Mirror text slots that the current renderer actually displays.

    Card layouts never render legacy proof_points. The legacy renderer only
    exposes those strings in Diandra's evidence cards or Charlie's label list.
    Keep fields/clauses separate so one company's name cannot lend its metrics
    to a different clause elsewhere in a profile.
    """
    if plan.get('layout_mode')=='reference-faithful':
        fields=[str(plan.get('headline',''))]+_reference_visible_groups(plan.get('reference_content',{}))
        return [part.strip() for value in fields for part in re.split(r'[|;]+',value) if part.strip()]
    keys=['headline','banner_title']
    modern='proof_cards' in plan
    if modern or plan.get('selected_style')!='mattgray1':keys.append('banner_subtitle')
    fields=[str(plan.get(key,'')) for key in keys]
    if not modern and plan.get('selected_style') in ('diandraescobar','charlie-hills'):
        fields.extend(plan.get('proof_points',[]))
    return [part.strip() for value in fields
            for part in re.split(r'[|;\n]+|(?<=[.!?])\s+',value) if part.strip()]


def validate_specificity(plan, profile, *, website=None, supplemental_evidence=None):
    """Reject generic packages when the source already provides concrete cases.

    This is a conservative evidence-retention gate, not a factual verifier or a
    substitute for the independent buyer review. It requires a visible named
    source case with a retained metric or recognizable case mechanism. Industry
    context and everyday comprehension are judged by the isolated visual review;
    a named case passing this check does not establish brand-independent clarity.
    """
    inventory=specificity_inventory(profile)
    supplements=list(supplemental_evidence or [])+_website_rows(website,plan.get('proof_cards',[]))
    inventory+=_supplement_rows(supplements,inventory)
    scoped=list(_card_rows(plan,inventory))
    rich=[row for row in inventory if row['metric_tokens'] or len(row['story_tokens'])>=2]
    fragments=_visible_copy_fragments(plan)
    all_source_metrics={metric for row in inventory for metric in row['metric_tokens']}
    # Context-only input may contain genuine results without a formal job list.
    all_source_metrics.update(_metrics(profile.get('about','')))
    unexpected={metric for fragment in fragments for metric in _metrics(fragment)}-all_source_metrics
    if unexpected:
        raise ValueError('Visible copy contains an outcome metric absent from collected source evidence; verify its source before rendering.')
    supported=[]
    bindings=_case_bindings(inventory)
    if plan.get('layout_mode')=='reference-faithful':
        for company,body in _reference_named_cases(plan.get('reference_content',{})):
            label=_company_key(company)
            rows=[row for group in bindings if label in group['keys'] for row in group['rows']]
            if not rows:
                if company.casefold() not in str(profile.get('about','')).casefold():
                    raise ValueError('Reference case company is absent from the subject source roles.')
                continue
            allowed={metric for row in rows for metric in row['metric_tokens']}
            if _metrics(body)-allowed:
                raise ValueError('Reference named case uses an outcome metric absent from that company source.')
            if (_metrics(body)&allowed) or any(len(_story_tokens(body)&set(row['story_tokens']))>=2 for row in rows):
                supported.append(rows[0]['company_id'] or company)
    for card,rows in scoped:
        visible=' '.join(str(card.get(k,'')) for k in ('company','role','value','detail'))
        metrics=_metrics(visible)
        source_metrics={v for row in rows for v in row['metric_tokens']}
        if metrics-source_metrics:
            raise ValueError('Specific proof card contains a metric absent from its named company source; preserve the exact scoped result.')
        story=_story_tokens(visible)
        if (metrics & source_metrics) or any(len(story & set(row['story_tokens']))>=2 for row in rows):
            if card.get('company','').strip() and card.get('source','').strip():
                supported.append(card['company_id'] or card['company'])
    if not rich:
        return {'status':'limited_source','reason':'No quantified case or distinctive case mechanism in collected experience. Visible outcome metrics were still checked against supplied evidence; do not manufacture proof.'}
    # Ordinary copy can carry the case even when its card shows an award or role,
    # but the company and result must occur together in the same visible clause.
    # Legacy proof cards may carry an explicitly scoped product identity too.
    # Their stricter logo binding has already been checked by _card_rows above.
    for card,rows in scoped:
        key=_company_key(card['company'])
        if key and not any(key in group['keys'] for group in bindings):
            bindings.append({'keys':{key},'names':{card['company']},'rows':rows})
    for group in bindings:
        rows=group['rows']
        for fragment in fragments:
            if any(_mentions_company(fragment,company) for company in group['names']):
                metrics=_metrics(fragment)
                allowed={metric for row in rows for metric in row['metric_tokens']}
                if metrics-allowed:
                    raise ValueError('Specific named case uses an outcome metric absent from that company source.')
                if (metrics&allowed) or any(len(_story_tokens(fragment)&set(row['story_tokens']))>=2 for row in rows):
                    supported.append(rows[0]['company_id'] or rows[0]['company'])
    if not supported:
        raise ValueError('Specific source evidence was discarded: include a named company case with its supported non-tenure metric or concrete story. Generic outcomes and years of experience are not enough.')
    return {'status':'passed','retained_company_ids':sorted(set(supported)),
            'source_cases_available':len(rich),'limitations':'Checks retained source details, not causal attribution, brand-independent clarity or visual distinctiveness. Independent review remains required.'}


def _logo_url(url):
    parsed=urlsplit(str(url))
    host=(parsed.hostname or '').lower()
    if (parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443)
            or not (host=='licdn.com' or host.endswith('.licdn.com'))):
        raise ValueError('Company logo must use an original public HTTPS LinkedIn CDN URL.')
    return str(url)


class _LogoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return super().redirect_request(req,fp,code,msg,headers,_logo_url(newurl))


def _download_logo(url):
    try:
        with build_opener(_LogoRedirect).open(Request(_logo_url(url),headers={'User-Agent':'linkedin-package/1.0'}),timeout=30) as response:
            data=response.read(MAX_LOGO_BYTES+1)
    except (HTTPError,URLError,TimeoutError,OSError):
        raise RuntimeError('Original company logo download failed. Refresh the source snapshot or supply a local original; no logo was invented.') from None
    if len(data)>MAX_LOGO_BYTES:raise ValueError('Company logo exceeds 8 MB.')
    return data


def _png_logo(raw):
    if len(raw)>MAX_LOGO_BYTES:raise ValueError('Company logo exceeds 8 MB.')
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('PNG','JPEG','WEBP') or image.width*image.height>16_000_000:
                raise ValueError('Company logo must be a reasonably sized PNG, JPEG or WebP.')
            image=ImageOps.exif_transpose(image).convert('RGBA')
            image.thumbnail((1200,1200),Image.Resampling.LANCZOS)
            buffer=io.BytesIO();image.save(buffer,format='PNG')
            return buffer.getvalue()
    except (OSError,SyntaxError):
        raise ValueError('Company logo is not a readable image.') from None


def _curated_company_logo(cache, company_id, item):
    """Prefer an explicitly prepared original wordmark over a social avatar.

    Curation is local and deliberate: callers must retain its official source,
    exact profile identity and content hash. This function never fetches an
    arbitrary curation URL or guesses whether a background can be removed.
    """
    folder=Path(cache)/'curated'
    image_path=folder/(company_id+'.png');record_path=folder/(company_id+'.json')
    if not image_path.exists() and not record_path.exists():return None
    if not image_path.is_file() or not record_path.is_file():
        raise ValueError('Curated logo requires both its PNG and provenance record.')
    if (image_path.is_symlink() or record_path.is_symlink() or
            not image_path.resolve().is_relative_to(Path(cache).resolve()) or
            not record_path.resolve().is_relative_to(Path(cache).resolve())):
        raise ValueError('Curated logo files must remain inside their local cache.')
    record=json.loads(record_path.read_text())
    if not isinstance(record,dict):raise ValueError('Curated logo requires an object provenance record.')
    if (record.get('company_id')!=company_id or
            record.get('profile_company_name','').casefold()!=str(item.get('companyName') or '').casefold()):
        raise ValueError('Curated logo identity differs from the selected source company.')
    if record.get('source_type')!='official-brand-asset' or any(
            not isinstance(record.get(key),str) or urlsplit(record[key]).scheme!='https' or not urlsplit(record[key]).hostname
            for key in ('source_url','source_page')):
        raise ValueError('Curated logo must retain its official HTTPS source and source page.')
    data=image_path.read_bytes()
    if record.get('sha256')!=hashlib.sha256(data).hexdigest():
        raise ValueError('Curated logo hash changed; verify the asset and update its provenance.')
    _png_logo(data)  # Validate format, size and dimensions without rewriting the original.
    with Image.open(io.BytesIO(data)) as image:
        alpha=image.convert('RGBA').getchannel('A')
        histogram=alpha.histogram()
        if sum(histogram[:16]) < image.width*image.height*.01 or alpha.getextrema()[1]<128:
            raise ValueError('Curated logo requires genuine transparent background and visible marks.')
    return image_path,record


def collect_company_logos(profile, company_ids, destination, *, cache_dir=None, max_logos=3):
    """Download at most three selected, source-provided logos; return portable paths."""
    ids=list(dict.fromkeys(str(value) for value in company_ids if value))
    if len(ids)>max_logos:raise ValueError(f'Select at most {max_logos} company logos.')
    if any(not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',value) for value in ids):raise ValueError('Invalid company_id for logo file.')
    rows={str(item.get('companyId')):item for item in profile.get('experience',[]) if isinstance(item,dict) and item.get('companyId') is not None}
    if any(value not in rows for value in ids):raise ValueError('Logo company_id is absent from the source profile.')
    destination=Path(destination);cache=Path(cache_dir) if cache_dir else destination/'logos'
    cache.mkdir(parents=True,exist_ok=True);logos=destination/'logos';logos.mkdir(parents=True,exist_ok=True)
    inventory={row['company_id']:row for row in specificity_inventory(profile)}
    assets={};provenance={}
    for company_id in ids:
        item=rows[company_id]
        curated=_curated_company_logo(cache,company_id,item)
        if curated:
            cached,record=curated
            output=logos/(company_id+'.png')
            if cached.resolve()!=output.resolve():shutil.copyfile(cached,output)
            assets[company_id]='logos/'+company_id+'.png';provenance[company_id]=record
            continue
        url=_image_url(item.get('companyLogo'))
        if not url:continue
        _logo_url(url)
        cached=cache/(company_id+'.png');record_file=cache/(company_id+'.json')
        record=json.loads(record_file.read_text()) if record_file.exists() else None
        if not (cached.exists() and record and record.get('source_url')==url
                and record.get('sha256')==hashlib.sha256(cached.read_bytes()).hexdigest()):
            raw=_download_logo(url);data=_png_logo(raw);cached.write_bytes(data)
            record={'company_id':company_id,'company':str(item.get('companyName') or ''),
                    'source_url':url,'company_url':str(item.get('companyLinkedinUrl') or ''),
                    'relationship':inventory.get(company_id,{}).get('relationship','role in profile'),
                    'role':str(item.get('position') or ''),'source_sha256':hashlib.sha256(raw).hexdigest(),
                    'sha256':hashlib.sha256(data).hexdigest(),'downloaded_at':datetime.now(timezone.utc).isoformat(),
                    'treatment':'Original downloaded logo, converted to PNG without changing design; affiliation only, not endorsement.'}
            write_json(record_file,record)
        output=logos/(company_id+'.png')
        if cached.resolve()!=output.resolve():shutil.copyfile(cached,output)
        assets[company_id]='logos/'+company_id+'.png';provenance[company_id]=record
    write_json(logos/'provenance.json',provenance)
    return assets


def enrich_brief_assets(plan, profile, destination, *, cache_dir=None, website=None, supplemental_evidence=None):
    """Validate evidence before any image-generation charge and prepare selected logos."""
    plan=copy.deepcopy(plan)
    plan['specificity_check']=validate_specificity(plan,profile,website=website,supplemental_evidence=supplemental_evidence)
    if plan.get('layout_mode')=='reference-faithful':
        plan['logo_assets']=_collect_reference_logos(plan,profile,destination,cache_dir)
    else:
        plan['logo_assets']=collect_company_logos(profile,[card['company_id'] for card in plan.get('proof_cards',[])],destination,cache_dir=cache_dir)
    return plan


def copy_brief_logos(plan, source_dir, destination):
    """Move a prepared package's original logos for an offline rerender; no network."""
    source_dir=Path(source_dir);destination=Path(destination)
    for company_id,relative in plan.get('logo_assets',{}).items():
        if not isinstance(company_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',company_id) or relative!='logos/'+company_id+'.png':
            raise ValueError('Logo assets must be safe package-relative logos/<company_id>.png paths.')
        source=(source_dir/relative).resolve()
        if not source.is_relative_to(source_dir.resolve()) or not source.is_file():raise ValueError('Prepared logo file is missing or outside its package.')
        _png_logo(source.read_bytes())
        output=destination/relative;output.parent.mkdir(parents=True,exist_ok=True)
        if source!=output.resolve():shutil.copyfile(source,output)
    record=source_dir/'logos/provenance.json'
    if record.is_file() and (source_dir.resolve()!=destination.resolve()):
        (destination/'logos').mkdir(parents=True,exist_ok=True);shutil.copyfile(record,destination/'logos/provenance.json')
    return plan
