"""Small Apify adapter for current public LinkedIn profile data.

The default actor deliberately disables email enrichment. Raw data and media remain
local; original image bytes are preserved rather than upscaled or recompressed.
"""
from __future__ import annotations
import hashlib
import json
import os
from contextlib import contextmanager
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ACTOR = 'harvestapi/linkedin-profile-scraper'
BASE_URL = 'https://api.apify.com/v2'


class ApifyError(RuntimeError):
    """Provider failure with a safe, credential-free explanation."""


def canonical_profile_url(url: str) -> str:
    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or '').lower()
    match = re.fullmatch(r'/in/([A-Za-z0-9][A-Za-z0-9_-]{0,99})/?', parsed.path)
    if parsed.scheme != 'https' or not (hostname == 'linkedin.com' or hostname.endswith('.linkedin.com')) or not match or parsed.username or parsed.port not in (None, 443):
        raise ValueError('Expected an HTTPS LinkedIn /in/<public-handle>/ URL')
    return f'https://www.linkedin.com/in/{match.group(1)}/'


def _image_url(value):
    if isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        sizes = [s for s in value.get('sizes', []) if isinstance(s, dict) and s.get('url')]
        if sizes:
            return max(sizes, key=lambda s: (s.get('width') or 0) * (s.get('height') or 0))['url']
        return value.get('url') or None
    return None


def normalize_profile(row: dict, *, fetched_at: str | None = None, actor: str = ACTOR) -> dict:
    if row.get('error') or row.get('succeeded') is False or row.get('status') in ('error', 'not_found'):
        raise ApifyError('The LinkedIn actor did not return a usable profile')
    original = row
    row = row.get('profile') or row
    slug = row.get('publicIdentifier') or row.get('identifier')
    url = row.get('linkedinUrl') or row.get('linkedinPublicUrl') or original.get('input_url')
    if not url and slug:
        url = f'https://www.linkedin.com/in/{slug}/'
    if not url:
        raise ApifyError('Actor response has no LinkedIn profile URL or public identifier')
    url = canonical_profile_url(url)
    portrait = _image_url(row.get('profilePicture')) or _image_url(row.get('photo')) or _image_url(row.get('picture_url'))
    banner = _image_url(row.get('coverPicture')) or _image_url(row.get('backgroundPicture')) or _image_url(row.get('background_url'))
    location = row.get('location') or ''
    if isinstance(location, dict):
        location = location.get('linkedinText') or location.get('short') or location.get('default') or ''
    return {
        'slug': url.rstrip('/').rsplit('/', 1)[-1], 'url': url,
        'name': row.get('fullName') or row.get('full_name') or ' '.join(str(row.get(k) or '') for k in ('firstName', 'lastName')).strip(),
        'headline': row.get('headline') or '', 'about': row.get('about') or row.get('summary') or '',
        'location': location, 'industry': row.get('industry'),
        'portrait_url': portrait, 'banner_url': banner,
        'follower_count': row.get('followerCount', row.get('followers')),
        'connection_count': row.get('connectionsCount', row.get('connections')),
        'experience': row.get('experience') or row.get('experiences') or row.get('position_groups') or [],
        'education': row.get('education') or row.get('educations') or [],
        'skills': row.get('skills') or [], 'current_position': row.get('currentPosition') or [],
        'source': {'provider': 'Apify', 'actor': actor, 'profile_url': url,
                   'fetched_at': fetched_at or datetime.now(timezone.utc).isoformat(),
                   'upstream_updated_at': row.get('last_updated')},
        'warnings': [key + '_missing' for key, value in [('portrait', portrait), ('banner', banner)] if not value],
    }


@contextmanager
def _cache_lock(path):
    if path is None:
        yield
        return
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ApifyError('Apify cache lock exists: another process is running or was interrupted. Inspect the run and lock before removing the stale lock.') from None
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


def _save_record(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    temporary.replace(path)


class ApifyClient:
    def __init__(self, api_key: str, *, actor: str = ACTOR, timeout: float = 300, max_charge_usd: float = 1.0):
        if not api_key:
            raise ValueError('Set APIFY_API_KEY before scraping')
        if actor != ACTOR:
            raise ValueError('This adapter currently supports only harvestapi/linkedin-profile-scraper')
        self.api_key, self.actor, self.timeout, self.max_charge_usd = api_key, actor, timeout, max_charge_usd

    def _request(self, path: str, *, payload=None):
        request = Request(BASE_URL + path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=min(self.timeout, 60)) as response:
                return json.load(response)
        except HTTPError as error:
            raise ApifyError(f'Apify HTTP {error.code}; check API key, credits, actor limits and connectivity') from None
        except (URLError, TimeoutError, json.JSONDecodeError):
            raise ApifyError('Apify request failed or timed out; use the saved run to resume without starting another paid job') from None

    def scrape(self, urls: list[str], *, cache_dir: Path | str | None = None) -> list[dict]:
        """Return raw actor rows. Persist a run ID before polling to avoid rebilling.

        Cached rows are intentionally reused until their cache file is removed.
        A failed run must be inspected/removed explicitly before rerunning.
        """
        canonical = list(dict.fromkeys(canonical_profile_url(url) for url in urls))
        if not canonical:
            return []
        payload = {'queries': canonical, 'profileScraperMode': 'Profile details no email ($4 per 1k)'}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
        cache = Path(cache_dir) if cache_dir else None
        result_file = cache / f'{digest}.items.json' if cache else None
        run_file = cache / f'{digest}.run.json' if cache else None
        if cache:
            cache.mkdir(parents=True, exist_ok=True)
        with _cache_lock(cache / f'{digest}.lock' if cache else None):
            if result_file and result_file.exists():
                return json.loads(result_file.read_text())
            if run_file and run_file.exists():
                run = json.loads(run_file.read_text())
                if run.get('submission_state') in ('submitting', 'unknown'):
                    raise ApifyError('Prior Apify submission outcome is unknown; inspect the dashboard and saved run marker before any new paid submission.')
            else:
                if run_file:
                    _save_record(run_file, {'submission_state': 'submitting'})
                try:
                    run = self._request(f'/acts/{self.actor.replace("/", "~")}/runs?timeout={int(self.timeout)}&memory=256&maxTotalChargeUsd={self.max_charge_usd}', payload=payload)['data']
                    if not isinstance(run, dict) or not run.get('id') or not run.get('status'):
                        raise ApifyError('Missing run ID or status')
                except (Exception, KeyboardInterrupt):
                    if run_file:
                        _save_record(run_file, {'submission_state': 'unknown'})
                    raise ApifyError('Apify submission outcome is unknown; inspect the provider dashboard before retrying. No automatic resubmission is allowed.') from None
                if run_file:
                    _save_record(run_file, run)
            deadline = time.monotonic() + self.timeout
            while run['status'] not in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
                if time.monotonic() >= deadline:
                    raise ApifyError(f'Apify run {run["id"]} is still running; retry with the same cache directory to resume')
                time.sleep(2)
                run = self._request(f'/actor-runs/{run["id"]}')['data']
                if run_file:
                    _save_record(run_file, run)
            if run['status'] != 'SUCCEEDED':
                raise ApifyError(f'Apify run {run["id"]} ended with {run["status"]}; inspect it in the Apify console')
            rows = self._request(f'/datasets/{run["defaultDatasetId"]}/items?clean=true&format=json&limit=100000')
            if not isinstance(rows, list):
                raise ApifyError('Apify returned an invalid dataset response')
            if result_file:
                _save_record(result_file, rows)
            return rows

    def collect(self, urls: list[str], output_root: Path | str) -> list[dict]:
        root = Path(output_root)
        rows = self.scrape(urls, cache_dir=root / '_collection')
        profiles = []
        for row in rows:
            profile = normalize_profile(row, actor=self.actor)
            profiles.append(save_profile(row, root / profile['slug'], profile=profile))
        return profiles


def download_media(url: str, target_stem: Path) -> dict:
    """Save original LinkedIn CDN bytes plus hash/type provenance."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not ((parsed.hostname or '').endswith('.licdn.com')):
        raise ApifyError('Refusing media URL outside the HTTPS LinkedIn CDN')
    try:
        with urlopen(Request(url, headers={'User-Agent': 'LinkedIn-Package/1.0'}), timeout=60) as response:
            mime = response.headers.get_content_type()
            extension = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}.get(mime)
            if not extension:
                raise ApifyError(f'Expected a supported image response, received {mime}')
            data = response.read(20 * 1024 * 1024 + 1)
            if len(data) > 20 * 1024 * 1024:
                raise ApifyError('Source image exceeds 20 MB')
    except (HTTPError, URLError, TimeoutError):
        raise ApifyError('LinkedIn image download failed; CDN URLs may have expired, so refresh the profile') from None
    target = target_stem.with_suffix(extension)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'file': target.name, 'url': url, 'mime_type': mime, 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(), 'downloaded_at': datetime.now(timezone.utc).isoformat()}


def save_profile(row: dict, output_dir: Path | str, *, profile: dict | None = None) -> dict:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    profile = profile or normalize_profile(row)
    (directory / 'raw.json').write_text(json.dumps(row, ensure_ascii=False, indent=2))
    (directory / 'headline.txt').write_text(profile['headline'] + '\n')
    media = {}
    for kind in ('banner', 'portrait'):
        if profile[kind + '_url']:
            media[kind] = download_media(profile[kind + '_url'], directory / kind)
            profile[kind + '_file'] = media[kind]['file']
    profile['media'] = media
    (directory / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2))
    return profile
