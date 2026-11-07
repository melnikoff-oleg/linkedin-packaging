"""Offline reconstruction of the supplied original LinkedIn profile header.

Only original local media and a small allowlist of profile fields are used. The
result is a before-preview for the local gallery, never an edited deliverable.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path, PurePosixPath

from PIL import Image

from .providers.apify import canonical_profile_url
from .render import preview_html

CAPTURE_VERSION = 1
MAX_IMAGE_BYTES = 20 * 1024 * 1024
PREVIEWS = ('review-desktop.png', 'review-mobile.png')


class BeforeUnavailable(ValueError):
    """No truthful original-profile preview can be made from these inputs."""


def _text(profile, key, maximum, *, required=False):
    value = profile.get(key, '')
    if value is None:
        value = ''
    if not isinstance(value, str) or len(value) > maximum:
        raise BeforeUnavailable('Original profile fields must be plain text of a reasonable length.')
    value = value.strip()
    if required and not value:
        raise BeforeUnavailable('An original profile name is required for the before preview.')
    return value


def _source_file(directory, profile, kind, explicit):
    if explicit:
        path = Path(explicit).expanduser()
    else:
        value = profile.get(kind + '_file')
        if not value:
            return None
        if not isinstance(value, str) or '\\' in value or ':' in value:
            raise BeforeUnavailable('Original media must use safe local file names, not remote URLs.')
        relative = PurePosixPath(value)
        if relative.is_absolute() or any(part in {'.', '..'} for part in relative.parts):
            raise BeforeUnavailable('Original media paths must stay within the source profile folder.')
        path = directory
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise BeforeUnavailable('Original media cannot be a symlink.')
    if path.is_symlink():
        raise BeforeUnavailable('Original media cannot be a symlink.')
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise BeforeUnavailable('An original image exceeds the 20 MB preview limit.')
        raw = path.read_bytes()
        with Image.open(io.BytesIO(raw)) as image:
            mime = Image.MIME.get(image.format)
            if image.format not in {'PNG', 'JPEG', 'WEBP'} or image.width * image.height > 50_000_000:
                raise BeforeUnavailable('Use an original PNG, JPEG or WebP image within the preview size limit.')
            image.verify()
        return raw, mime
    except (OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise BeforeUnavailable('An original image could not be decoded; supply a usable original image.') from None


def _uri(media):
    raw, mime = media
    return 'data:' + mime + ';base64,' + base64.b64encode(raw).decode('ascii')


def _rasterize(name, headline, location, banner, portrait):
    from playwright.sync_api import sync_playwright

    neutral = ('data:image/svg+xml;base64,' + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="1584" height="396"><rect width="1584" height="396" fill="#dce6e9"/></svg>'
    ).decode('ascii'))
    results = {}
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        try:
            context = browser.new_context(service_workers='block')
            # All input images are embedded. No page request may leave the computer.
            context.route('**/*', lambda route: route.abort())
            page = context.new_page()
            for mobile, filename in ((False, PREVIEWS[0]), (True, PREVIEWS[1])):
                page.set_viewport_size({'width': 390 if mobile else 848, 'height': 900})
                page.set_content(preview_html({'name': name, 'headline': headline},
                                             _uri(banner) if banner else neutral,
                                             _uri(portrait), location, mobile=mobile))
                page.locator('img').evaluate_all('els => Promise.all(els.map(img => img.decode()))')
                page.evaluate('document.fonts.ready')
                results[filename] = page.locator('.card').screenshot()
        finally:
            browser.close()
    return results


def capture_before(profile_path, output, *, portrait=None, banner=None):
    """Save a truthful original profile under ``output/before`` without APIs.

    Explicit media overrides must be originals, not the generated avatar/banner.
    Unavailable portrait raises BeforeUnavailable; an absent banner is disclosed.
    """
    source = Path(profile_path)
    try:
        if source.stat().st_size > 5 * 1024 * 1024:
            raise BeforeUnavailable('The normalized source profile exceeds the preview limit.')
        profile = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise BeforeUnavailable('Save a normalized original profile JSON before building its preview.') from None
    if not isinstance(profile, dict):
        raise BeforeUnavailable('The original profile must be a JSON object.')
    name = _text(profile, 'name', 200, required=True)
    headline = _text(profile, 'headline', 2000)
    location = _text(profile, 'location', 500)
    url = _text(profile, 'url', 500)
    source_url = canonical_profile_url(url) if url else ''
    original_portrait = _source_file(source.parent, profile, 'portrait', portrait)
    if original_portrait is None:
        raise BeforeUnavailable('Original profile photo unavailable. Supply its original local photo to add a before preview; the generated styles can still be reviewed.')
    original_banner = _source_file(source.parent, profile, 'banner', banner)
    note = 'Reconstructed from saved original profile assets.'
    if original_banner is None:
        note += ' Original banner unavailable; neutral cover shown.'
    if not headline:
        note += ' Original headline unavailable.'
    evidence = {'version': CAPTURE_VERSION, 'name': name, 'headline': headline,
                'location': location, 'source_url': source_url,
                'portrait': hashlib.sha256(original_portrait[0]).hexdigest(),
                'banner': hashlib.sha256(original_banner[0]).hexdigest() if original_banner else None}
    fingerprint = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
    target = Path(output) / 'before'
    if target.is_symlink() or any((target / name).is_symlink() for name in (*PREVIEWS, 'metadata.json')):
        raise BeforeUnavailable('The before-preview destination cannot contain symlinks.')
    try:
        saved = json.loads((target / 'metadata.json').read_text())
        if saved.get('source_fingerprint') == fingerprint and all(
                hashlib.sha256((target / name).read_bytes()).hexdigest() == saved.get('preview_sha256', {}).get(name)
                for name in PREVIEWS):
            return {**saved, 'cached': True}
    except (OSError, ValueError, AttributeError):
        pass
    try:
        previews = _rasterize(name, headline, location, original_banner, original_portrait)
    except Exception:
        raise BeforeUnavailable('The original-profile preview could not render. Check the local browser installation and source images; no provider requests were made.') from None
    metadata = {'name': name, 'source_url': source_url, 'note': note,
                'source_fingerprint': fingerprint,
                'preview_sha256': {key: hashlib.sha256(raw).hexdigest() for key, raw in previews.items()}}
    target.mkdir(parents=True, exist_ok=True)
    # Render both images successfully before replacing either preview; metadata is last.
    for filename, raw in (*previews.items(), ('metadata.json', (json.dumps(metadata, indent=2) + '\n').encode())):
        with tempfile.NamedTemporaryFile(dir=target, prefix='.before-', delete=False) as temporary:
            temporary.write(raw)
            pending = Path(temporary.name)
        try:
            os.chmod(pending, 0o600)
            pending.replace(target / filename)
        finally:
            pending.unlink(missing_ok=True)
    return {**metadata, 'cached': False}
