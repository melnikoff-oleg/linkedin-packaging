"""Kie image editing and structured copy, with durable paid-request recovery.

The caller owns visual review. No paid POST is automatically retried.
"""
from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import mimetypes
import os
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

DEFAULT_IMAGE_MODEL = 'gpt-image-2-6/sunburst-image-to-image'
DEFAULT_CHAT_MODEL = 'gpt-6.1-sol'
API_BASE = 'https://api.kie.ai'
UPLOAD_URL = 'https://kieai.redpandaai.co/api/file-base64-upload'


class KieError(RuntimeError):
    """A provider, input or persisted-task failure safe to show without secrets."""


class SubmissionUnknown(KieError):
    """The paid request may have been accepted; inspect the dashboard first."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _public_https(url):
    parsed = urlsplit(str(url))
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Image URLs must be public HTTPS URLs without credentials.')
    host = parsed.hostname.lower().rstrip('.')
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise ValueError('Image URLs must be publicly accessible.')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('Image URLs must be publicly accessible.')
    return str(url)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def _image_mime(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    raise ValueError('Image must be PNG, JPEG or WebP.')


class KieClient:
    def __init__(self, api_key=None, cache_dir='.cache/kie', *, image_model=DEFAULT_IMAGE_MODEL,
                 chat_model=DEFAULT_CHAT_MODEL, request_timeout=120, poll_interval=3):
        self.api_key = api_key or os.environ.get('KIE_AI_API_KEY', '')
        if not self.api_key:
            raise KieError('Set KIE_AI_API_KEY before calling Kie.')
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.image_model, self.chat_model = image_model, chat_model
        self.request_timeout, self.poll_interval = request_timeout, poll_interval
        self._account = hashlib.sha256(self.api_key.encode()).hexdigest()

    def _request(self, method, url, payload=None):
        # Never forward credentials to redirects or caller-controlled destinations.
        if not (url.startswith(API_BASE + '/') or url == UPLOAD_URL):
            raise ValueError('Unsupported Kie API endpoint.')
        req = Request(url, method=method,
                      data=json.dumps(payload).encode() if payload is not None else None,
                      headers={'Authorization': 'Bearer ' + self.api_key,
                               'Content-Type': 'application/json'})
        try:
            with build_opener(_NoRedirect).open(req, timeout=self.request_timeout) as reply:
                raw = reply.read(12_000_001)
            if len(raw) > 12_000_000:
                raise KieError('Kie response exceeds the local size limit.')
            value = json.loads(raw)
        except HTTPError as exc:
            raise KieError(f'Kie HTTP {exc.code}; inspect your provider dashboard before retrying.') from None
        except (URLError, TimeoutError, OSError):
            raise KieError('Kie connection failed; inspect the provider dashboard before retrying.') from None
        except (ValueError, UnicodeError):
            raise KieError('Kie returned invalid JSON.') from None
        if not isinstance(value, dict):
            raise KieError('Kie returned an unexpected response.')
        return value

    def _download(self, url):
        url = _public_https(url)
        # Downloads never carry the Kie API key.
        def fetch(download_url):
            with urlopen(Request(download_url, headers={'User-Agent': 'linkedin-package/1.0'}), timeout=120) as reply:
                return reply.read(30_000_001)

        try:
            data = fetch(url)
        except (HTTPError, URLError, TimeoutError, OSError):
            # Kie's official utility converts generated URLs into 20-minute
            # signed storage links. This recovers CDN/TLS failures without
            # creating or billing another generation task.
            # https://docs.kie.ai/common-api/download-url
            try:
                response = self._request('POST', API_BASE + '/api/v1/common/download-url', {'url': url})
                if response.get('code') != 200 or not isinstance(response.get('data'), str):
                    raise KieError('Kie did not return a temporary download link.')
                data = fetch(_public_https(response['data']))
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, KieError):
                raise KieError('Could not download the generated image; rerun to resume the same task.') from None
        if len(data) > 30_000_000:
            raise KieError('Generated image exceeds the 30 MB local limit.')
        _image_mime(data)
        return data

    @contextmanager
    def _lock(self, digest):
        path = self.cache_dir / (digest + '.lock')
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise KieError(f'Request is already running or was interrupted. Inspect {path.name} before removing its lock.') from None
        try:
            with os.fdopen(fd, 'w') as handle:
                handle.write(str(os.getpid()))
            yield
        finally:
            path.unlink(missing_ok=True)

    @staticmethod
    def _data(response):
        if response.get('code') != 200 or not isinstance(response.get('data'), dict):
            raise KieError(f'Kie rejected the request (code {response.get("code", "missing")}); inspect dashboard.')
        return response['data']

    def _upload(self, path, data):
        mime = _image_mime(data)
        suffix = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}[mime]
        digest = hashlib.sha256(data).hexdigest()
        response = self._request('POST', UPLOAD_URL, {
            'base64Data': 'data:' + mime + ';base64,' + base64.b64encode(data).decode(),
            'uploadPath': 'linkedin-package', 'fileName': digest + suffix,
        })
        result = self._data(response)
        return _public_https(result.get('downloadUrl', ''))

    def generate_headshot(self, source, prompt, output_path, *, resolution='2K', timeout=600,
                          aspect_ratio='1:1', background=None):
        """Edit the source identity, cache the paid task and download the final PNG.

        Resuming the same source bytes + prompt + parameters never creates a new
        task. Unknown submission states and failed tasks need human inspection.
        """
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
            raise ValueError('Image prompt must contain 1–20,000 characters.')
        if resolution not in ('1K', '2K', '4K'):
            raise ValueError('resolution must be 1K, 2K or 4K.')
        if aspect_ratio not in ('1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', 'auto'):
            raise ValueError('Unsupported aspect ratio.')
        if background is not None and (resolution != '1K' or background not in ('opaque', 'transparent', 'auto')):
            raise ValueError('background is supported only at 1K.')
        local_data = None
        if str(source).startswith(('https:', 'http:')):
            source_url = _public_https(source)
            source_id = source_url
        else:
            source = Path(source)
            if not source.is_file():
                raise ValueError('Source portrait does not exist.')
            if source.stat().st_size > 10_000_000:
                raise ValueError('Local source must be 10 MB or smaller for base64 upload.')
            local_data = source.read_bytes()
            _image_mime(local_data)
            source_id = hashlib.sha256(local_data).hexdigest()
            source_url = None
        settings = {'model': self.image_model, 'source': source_id, 'prompt': prompt,
                    'resolution': resolution, 'aspect_ratio': aspect_ratio, 'background': background}
        digest = _hash({'account': self._account, 'settings': settings})
        record_path, image_path = self.cache_dir / (digest + '.json'), self.cache_dir / (digest + '.png')
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock(digest):
            record = json.loads(record_path.read_text()) if record_path.exists() else {}
            if image_path.is_file() and record.get('state') == 'success':
                if image_path.resolve() != output_path.resolve():
                    shutil.copyfile(image_path, output_path)
                return output_path
            if record.get('state') in ('submitting', 'submission_unknown'):
                raise SubmissionUnknown(f'Prior submission outcome is unknown. Inspect Kie dashboard and {record_path.name}; no second task was created.')
            if record.get('state') == 'fail':
                raise KieError(f'Previously failed image task {record.get("task_id", "")}; no second task was created.')
            if not record.get('task_id'):
                if local_data is not None:
                    source_url = self._upload(source, local_data)
                inputs = {'prompt': prompt, 'input_urls': [source_url], 'aspect_ratio': aspect_ratio,
                          'resolution': resolution, 'output_format': 'png'}
                if background is not None:
                    inputs['background'] = background
                record = {'kind': 'image', 'state': 'submitting', 'settings': settings, 'created_at': time.time()}
                _write_json(record_path, record)
                try:
                    data = self._data(self._request('POST', API_BASE + '/api/v1/jobs/createTask', {'model': self.image_model, 'input': inputs}))
                    if not isinstance(data.get('taskId'), str) or not data['taskId']:
                        raise KieError('Kie response has no task ID.')
                except (Exception, KeyboardInterrupt):
                    record['state'] = 'submission_unknown'
                    _write_json(record_path, record)
                    raise SubmissionUnknown(f'Image submission outcome is unknown. Inspect Kie dashboard and {record_path.name}; do not blindly resubmit.') from None
                record.update(task_id=data['taskId'], state='waiting')
                _write_json(record_path, record)
            deadline, interval = time.monotonic() + timeout, self.poll_interval
            while record.get('state') != 'success':
                data = self._data(self._request('GET', API_BASE + '/api/v1/jobs/recordInfo?' + urlencode({'taskId': record['task_id']})))
                state = data.get('state')
                if state == 'success':
                    try:
                        result = json.loads(data['resultJson']) if isinstance(data.get('resultJson'), str) else data['resultJson']
                        result_url = _public_https(result['resultUrls'][0])
                    except (ValueError, KeyError, IndexError, TypeError):
                        raise KieError('Task completed without a usable image URL; inspect dashboard.') from None
                    record.update(state='success', result_url=result_url, credits_consumed=data.get('creditsConsumed'))
                    _write_json(record_path, record)
                    break
                if state == 'fail':
                    record.update(state='fail', fail_code=str(data.get('failCode', 'unknown'))[:120])
                    _write_json(record_path, record)
                    raise KieError(f'Image task failed; inspect task {record["task_id"]} in Kie dashboard.')
                if state not in ('waiting', 'queuing', 'generating'):
                    raise KieError('Unexpected Kie task state; rerun to query the same task.')
                record['state'] = state
                _write_json(record_path, record)
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'Image task {record["task_id"]} is still running. Rerun unchanged to resume.')
                time.sleep(min(interval, max(0, deadline - time.monotonic())))
                interval = min(15, interval * 1.5)
            image_path.write_bytes(self._download(record['result_url']))
            if image_path.resolve() != output_path.resolve():
                shutil.copyfile(image_path, output_path)
            return output_path

    def generate_brief(self, context, references, *, system_prompt, schema, timeout=None):
        """Return cached structured model output; same Kie key, no OpenAI key."""
        if not isinstance(schema, dict) or not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError('Provide a JSON schema and a nonempty system prompt.')
        payload = {'model': self.chat_model, 'stream': False,
                   'input': [{'role': 'system', 'content': system_prompt},
                             {'role': 'user', 'content': json.dumps({'context': context, 'references': references}, ensure_ascii=False)}],
                   'reasoning': {'effort': 'low'},
                   'text': {'format': {'type': 'json_schema', 'name': 'packaging_brief', 'strict': True, 'schema': schema}}}
        digest = _hash({'account': self._account, 'payload': payload})
        record_path = self.cache_dir / (digest + '.json')
        with self._lock(digest):
            if record_path.exists():
                record = json.loads(record_path.read_text())
                if record.get('state') == 'success':
                    return record['brief']
                raise SubmissionUnknown(f'Prior brief request needs review ({record_path.name}); no duplicate paid call was made.')
            record = {'kind': 'brief', 'state': 'submitting', 'model': self.chat_model, 'created_at': time.time()}
            _write_json(record_path, record)
            previous_timeout = self.request_timeout
            if timeout is not None:
                self.request_timeout = timeout
            try:
                response = self._request('POST', API_BASE + '/codex/v1/responses', payload)
                if response.get('status') != 'completed':
                    raise KieError('Brief generation did not complete; inspect provider dashboard.')
                parts = [p['text'] for item in response.get('output', []) if item.get('type') == 'message'
                         for p in item.get('content', []) if p.get('type') == 'output_text']
                brief = json.loads(''.join(parts))
                if not isinstance(brief, dict):
                    raise KieError('Generated brief must be a JSON object.')
                missing = set(schema.get('required', [])) - set(brief)
                if missing:
                    raise KieError('Generated brief is missing required fields.')
                record.update(state='success', brief=brief, response_id=response.get('id'), usage=response.get('usage'))
                _write_json(record_path, record)
                return brief
            except (Exception, KeyboardInterrupt) as exc:
                record['state'] = 'submission_unknown'
                _write_json(record_path, record)
                if isinstance(exc, KieError):
                    raise
                raise KieError('Brief request failed or returned invalid output; inspect cache and dashboard before retrying.') from None
            finally:
                self.request_timeout = previous_timeout


def generate_headshot(source, prompt, output_path, *, api_key=None, cache_dir='.cache/kie', **kwargs):
    return KieClient(api_key, cache_dir).generate_headshot(source, prompt, output_path, **kwargs)
