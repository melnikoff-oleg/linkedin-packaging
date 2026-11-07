"""Context-isolated, hash-bound first-impression review of finished profile cards.

Kie supports Responses input_image content alongside input_text:
https://docs.kie.ai/market/chat/gpt-6-1-sol
Only a buyer persona and two neutral screenshots enter the model request. This
module does not read briefs, source portraits, style names or generator prompts.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
import math
import re
import time
from pathlib import Path
from PIL import Image
from .core import ROOT
from .providers.kie import KieClient, KieError, SubmissionUnknown, API_BASE, _hash, _write_json

REVIEW_IMAGES=('review-desktop.png','review-mobile.png')
PACKAGE_FILES=('banner.png','portrait.png','headline.txt',*REVIEW_IMAGES)


def _package_hashes(output):
    output=Path(output)
    hashes={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in PACKAGE_FILES}
    qa=json.loads((output/'qa.json').read_text())
    if qa.get('passed') is not True or qa.get('render_sha256')!=hashes:
        raise ValueError('Package changed since rendering; rerender before review.')
    return hashes


PROMPT_FILE=ROOT/'prompts'/'blind-icp-review.md'
REVIEW_SCHEMA={
    'type':'object','additionalProperties':False,
    'properties':{
        'verdict':{'type':'string','enum':['accept','revise']},
        'immediate_reaction':{'type':'string'},
        'perceived_offer':{'type':'string'},
        'interchangeability':{'type':'string','enum':['specific','interchangeable']},
        'memorability':{'type':'string'},
        'brand_independent_clarity':{'type':'string','enum':['clear','unclear']},
        'plain_language_takeaway':{'type':'string'},
        **{name:{'type':'array','items':{'type':'string'}} for name in
           ['distinctive_details','credibility_concerns','visual_concerns','recommended_changes']},
    },
    'required':['verdict','immediate_reaction','perceived_offer','credibility_concerns',
                'visual_concerns','recommended_changes','interchangeability',
                'distinctive_details','memorability','brand_independent_clarity',
                'plain_language_takeaway'],
}


def _screenshots(output):
    images={};hashes={}
    for name in REVIEW_IMAGES:
        path=Path(output)/name
        if not path.is_file():
            raise ValueError(f'Missing neutral profile review image: {name}')
        if path.stat().st_size>8_000_000:
            raise ValueError(f'{name} exceeds the 8 MB review input limit')
        raw=path.read_bytes()
        try:
            with Image.open(io.BytesIO(raw)) as image:
                if image.format!='PNG' or min(image.size)<100:
                    raise ValueError('Review inputs must be readable PNG profile cards')
                image.verify()
        except (OSError,SyntaxError):
            raise ValueError(f'{name} is not a valid PNG') from None
        images[name]=raw
        hashes[name]=hashlib.sha256(raw).hexdigest()
    return images,hashes


def _validate_result(result):
    if not isinstance(result,dict) or set(result)!=set(REVIEW_SCHEMA['required']):
        raise KieError('Blind review returned an invalid result structure')
    if result['verdict'] not in ('accept','revise'):
        raise KieError('Blind review returned an invalid verdict')
    if result['interchangeability'] not in ('specific','interchangeable'):
        raise KieError('Blind review returned invalid interchangeability')
    if result['brand_independent_clarity'] not in ('clear','unclear'):
        raise KieError('Blind review returned invalid brand-independent clarity')
    for key in ('immediate_reaction','perceived_offer','memorability','plain_language_takeaway'):
        if not isinstance(result[key],str) or not result[key].strip():
            raise KieError(f'Blind review is missing {key}')
    for key in ('distinctive_details','credibility_concerns','visual_concerns','recommended_changes'):
        if not isinstance(result[key],list) or any(not isinstance(x,str) or not x.strip() for x in result[key]):
            raise KieError(f'Blind review returned invalid {key}')
    return result


def _response_metadata(response):
    """Keep recovery/billing identifiers, never provider messages or output text."""
    metadata={}
    response_id=response.get('id')
    if isinstance(response_id,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,200}',response_id):
        metadata['response_id']=response_id
    status=response.get('status')
    if status in ('completed','failed','incomplete','in_progress','queued','cancelled'):
        metadata['response_status']=status
    if type(response.get('code')) is int:
        metadata['response_code']=response['code']
    credits=response.get('credits_consumed')
    if type(credits) in (int,float) and math.isfinite(credits):
        metadata['credits_consumed']=credits
    usage_keys={'input_tokens','output_tokens','total_tokens','cached_tokens','reasoning_tokens',
                'input_tokens_details','output_tokens_details'}
    def numeric_usage(value):
        if not isinstance(value,dict):
            return {}
        return {key:(numeric_usage(item) if isinstance(item,dict) else item)
                for key,item in value.items() if key in usage_keys and
                (isinstance(item,dict) or (type(item) in (int,float) and math.isfinite(item)))}
    if isinstance(response.get('usage'),dict):
        metadata['usage']=numeric_usage(response['usage'])
    return metadata


def review_is_current(output, audience=None):
    """Whether the saved review belongs to these exact current screenshots."""
    try:
        report=json.loads((Path(output)/'blind-review.json').read_text())
        _validate_result({key:report.get(key) for key in REVIEW_SCHEMA['required']})
        _,hashes=_screenshots(output)
        prompt_hash=hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest()
        return (report.get('state')=='completed' and report.get('image_sha256')==hashes
                and report.get('package_sha256')==_package_hashes(output)
                and report.get('prompt_sha256')==prompt_hash
                and (audience is None or report.get('audience')==audience.strip()))
    except (OSError,ValueError,TypeError,AttributeError,KieError):
        return False


def review_passed(output, audience=None):
    """Require readable substance without brand familiarity, bound to current pixels."""
    if not review_is_current(output,audience):
        return False
    try:
        result=json.loads((Path(output)/'blind-review.json').read_text())
        _validate_result({key:result.get(key) for key in REVIEW_SCHEMA['required']})
        return (result.get('verdict')=='accept' and not result.get('visual_concerns')
                and not result.get('credibility_concerns')
                and result.get('interchangeability')=='specific'
                and result.get('brand_independent_clarity')=='clear'
                and bool(result.get('distinctive_details')))
    except (OSError,ValueError,KieError):
        return False


def review_package(output, audience, client=None):
    """Review exact desktop/mobile cards with no generator context.

    Save ``blind-review.json`` even for a revise verdict. Completed identical
    requests reuse the provider cache. Any ambiguous paid submission is retained
    for explicit inspection rather than automatically repeated. This function
    does not regenerate images or rewrite the profile to satisfy its reviewer.
    """
    if not isinstance(audience,str) or not audience.strip() or len(audience)>1800:
        raise ValueError('Provide a concise buyer persona of 1–1800 characters')
    audience=audience.strip(); output=Path(output)
    images,hashes=_screenshots(output)
    package_hashes=_package_hashes(output)
    prompt=PROMPT_FILE.read_text(encoding='utf-8').strip()
    prompt_hash=hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest()
    client=client or KieClient()
    payload={
        'model':client.chat_model,'stream':False,
        'input':[{'role':'system','content':prompt},
                 {'role':'user','content':[
                     {'type':'input_text','text':'Prospective buyer persona:\n'+audience+
                      '\n\nImage 1: desktop profile. Image 2: mobile profile.'},
                     *[{'type':'input_image','image_url':'data:image/png;base64,'+
                        base64.b64encode(images[name]).decode(),'detail':'high'} for name in REVIEW_IMAGES],
                 ]}],
        'reasoning':{'effort':'high'},
        'text':{'format':{'type':'json_schema','name':'profile_first_impression',
                          'strict':True,'schema':REVIEW_SCHEMA}},
    }
    fingerprint=_hash({'kind':'blind-review','account':client._account,'model':client.chat_model,
                       'audience':audience,'image_sha256':hashes,'prompt_sha256':prompt_hash,
                       'schema':REVIEW_SCHEMA,'effort':'high','package_sha256':package_hashes})
    cache=client.cache_dir/(fingerprint+'.json')
    with client._lock(fingerprint):
        record=json.loads(cache.read_text()) if cache.exists() else None
        if record:
            if record.get('state')!='success':
                raise SubmissionUnknown(f'Prior blind-review submission needs inspection ({cache.name}); no duplicate paid request was made.')
            result=_validate_result(record.get('result'))
        else:
            record={'kind':'blind-review','state':'submitting','created_at':time.time(),
                    'model':client.chat_model,'image_sha256':hashes,'prompt_sha256':prompt_hash,
                    'audience':audience}
            _write_json(cache,record)
            response_received=False
            try:
                response=client._request('POST',API_BASE+'/codex/v1/responses',payload)
                response_received=True
                record.update(_response_metadata(response))
                _write_json(cache,record)
                if response.get('status')!='completed':
                    raise KieError('Blind review did not complete; inspect the provider dashboard')
                parts=[part['text'] for item in response.get('output',[]) if item.get('type')=='message'
                       for part in item.get('content',[]) if part.get('type')=='output_text']
                result=_validate_result(json.loads(''.join(parts)))
            except (Exception,KeyboardInterrupt) as exc:
                record.update(state='submission_unknown',error_type=type(exc).__name__,
                              error_reason=('Response received; review result could not be validated.'
                                            if response_received else
                                            'Request did not return a response; provider outcome is unknown.'))
                _write_json(cache,record)
                raise SubmissionUnknown(f'Blind-review outcome is unknown ({cache.name}); inspect cache and provider dashboard before retrying.') from None
            record.update(state='success',result=result)
            _write_json(cache,record)
        report={**result,'package_sha256':package_hashes,'state':'completed','audience':audience,'model':client.chat_model,
                'image_sha256':hashes,'prompt_sha256':prompt_hash,'reviewed_at':record['created_at'],
                'response_id':record.get('response_id'),'usage':record.get('usage'),
                'credits_consumed':record.get('credits_consumed')}
        try:
            _,current=_screenshots(output)
            if _package_hashes(output)!=package_hashes:
                current={}
        except (OSError,ValueError):
            current={}
        if current!=hashes:
            report['state']='stale';_write_json(output/'blind-review.json',report)
            raise KieError('Profile images changed during review; the saved review cannot approve current output')
        _write_json(output/'blind-review.json',report)
        return report
