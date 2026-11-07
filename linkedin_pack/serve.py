"""A loopback-only review UI with narrowly scoped package downloads.

This server neither generates images nor exposes a filesystem directory. The
agent owns generation/revisions; the browser reads finished local artifacts.
"""
from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import re
import unicodedata
import zipfile
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

from .styles import STYLES

UPLOADS = ('banner.png', 'portrait.png', 'headline.txt')
PREVIEWS = ('preview.png', 'preview-mobile.png', 'review-desktop.png', 'review-mobile.png')
SOURCES = ('brief.json', 'banner.html', 'preview.html', 'preview-mobile.html',
           'banner-photo-cutout.png', 'banner-photo.png', 'background.png', 'background.jpg')
ASSETS = frozenset((*UPLOADS, *PREVIEWS))
BEFORE_ASSETS = frozenset(('review-desktop.png', 'review-mobile.png'))
MAX_FILE = 64 * 1024 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024
BLOCKED = {'source', 'sources', 'raw', 'cache', 'credentials', 'secrets', 'node_modules'}
RESOURCE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.ttf', '.otf', '.woff', '.woff2', '.css'}


def _local(root: Path, relative: str) -> Path:
    """Resolve safe relative files without following any descendant symlink."""
    if not isinstance(relative, str) or not relative or '\\' in relative or '\x00' in relative:
        raise ValueError('Invalid package path.')
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in ('', '.', '..') or part.startswith('.')
                               or part.lower() in BLOCKED
                               or re.search(r'(?:api.?keys?|credentials|secrets?|password)', part, re.I)
                               for part in path.parts):
        raise ValueError('Private or unsafe package path.')
    result = root
    for part in path.parts:
        result = result / part
        if result.is_symlink():
            raise ValueError('Symlinks are not served or downloaded.')
    if not result.resolve().is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError('Package file is missing.')
    if result.stat().st_size > MAX_FILE:
        raise ValueError('Package file exceeds the download limit.')
    return result


def _read(root, name):
    return _local(root, name).read_bytes()


def _optional_json(root, name):
    try:
        value = json.loads(_read(root, name))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _has(root, name):
    try:
        _local(root, name)
        return True
    except (OSError, ValueError):
        return False


def _render_qa(root):
    """An existing partial QA write is an incomplete render, never permission."""
    path = root / 'qa.json'
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        qa = json.loads(_read(root, 'qa.json'))
        if not isinstance(qa, dict):
            raise ValueError('Invalid render state.')
        return qa
    except (OSError, ValueError):
        return {'passed': False, 'acceptance': 'render_failed'}


def _revision(folder):
    state = []
    for name in (*ASSETS, *SOURCES, 'qa.json', 'blind-review.json'):
        if _has(folder, name):
            stat = (folder / name).stat()
            state.append((name, stat.st_size, stat.st_mtime_ns))
    return hashlib.sha256(repr(sorted(state)).encode()).hexdigest()[:20]


def discover(root):
    """Recognize packages, not arbitrary files; never descend into captures."""
    found = {}
    pending = [(root, 0)]
    while pending:
        folder, depth = pending.pop()
        if all(_has(folder, name) for name in UPLOADS) and any(_has(folder, name) for name in PREVIEWS):
            relative = folder.relative_to(root).as_posix()
            identifier = hashlib.sha256(relative.encode()).hexdigest()[:20]
            found[identifier] = folder
        if depth < 4:
            for child in sorted(folder.iterdir(), reverse=True):
                if (child.is_dir() and not child.is_symlink() and not child.name.startswith('.')
                        and child.name.lower() not in BLOCKED | {'before'}):
                    pending.append((child, depth + 1))
    def order(item):
        folder = item[1]
        newest = max((_local(folder, name).stat().st_mtime_ns for name in (*UPLOADS, *PREVIEWS) if _has(folder, name)), default=0)
        return (-newest, folder.as_posix())
    return dict(sorted(found.items(), key=order))


def _linkedin_profile(value):
    """Canonical public profile URL, suitable for identity checks and links."""
    try:
        parsed = urlsplit(value) if isinstance(value, str) else None
        if not (parsed and parsed.scheme in {'http', 'https'}
                and parsed.hostname in {'linkedin.com', 'www.linkedin.com'}
                and not parsed.username and not parsed.password and parsed.port in {None, 80, 443}
                and re.fullmatch(r'/in/[A-Za-z0-9_%.-]+/?', parsed.path)):
            return ''
        slug = unquote(parsed.path.strip('/').split('/')[1]).casefold()
        if not slug or any(char in slug for char in '/\\?#\x00'):
            return ''
        return 'https://www.linkedin.com/in/' + quote(slug, safe='-_.') + '/'
    except ValueError:
        return ''


def _same_subject(brief, original):
    if not original:
        return True
    actual_url = _linkedin_profile(brief.get('profile_url'))
    original_url = _linkedin_profile(original.get('source_url'))
    if actual_url and original_url:
        return actual_url == original_url
    def normalized(value):
        return ' '.join(unicodedata.normalize('NFKC', value).casefold().split()) if isinstance(value, str) else ''
    actual_name, original_name = normalized(brief.get('name')), normalized(original.get('name'))
    return actual_name == original_name if actual_name and original_name else True


def before_info(root):
    """Expose only an optional saved original and its small display metadata."""
    images = {mode: name if _has(root, 'before/' + name) else None
              for mode, name in (('desktop', 'review-desktop.png'), ('mobile', 'review-mobile.png'))}
    if not any(images.values()):
        return None
    metadata = _optional_json(root, 'before/metadata.json')
    clean = {key: metadata[key][:limit] if isinstance(metadata.get(key), str) else ''
             for key, limit in (('name', 240), ('note', 800))}
    clean['source_url'] = _linkedin_profile(metadata.get('source_url'))
    state = []
    for name in (*BEFORE_ASSETS, 'metadata.json'):
        if _has(root, 'before/' + name):
            stat = _local(root, 'before/' + name).stat()
            state.append((name, stat.st_size, stat.st_mtime_ns))
    return {**images, **clean, 'revision': hashlib.sha256(repr(sorted(state)).encode()).hexdigest()[:20]}


def package_info(identifier, folder, root):
    brief = _optional_json(folder, 'brief.json')
    qa = _render_qa(folder)
    status = 'Draft · review before uploading'
    rendering = qa.get('acceptance') == 'render_in_progress'
    failed = qa.get('acceptance') == 'render_failed'
    if rendering:
        status = 'Updating preview…'
    elif failed:
        status = 'Render incomplete · ask your agent to retry'
    elif qa.get('passed') is False:
        status = 'Draft · changes need attention'
    elif qa.get('passed') is True:
        from .review import review_passed
        if review_passed(folder):
            status = 'AI review passed · check before uploading'
    desktop = next((name for name in ('review-desktop.png', 'preview.png') if _has(folder, name)), None)
    mobile = next((name for name in ('review-mobile.png', 'preview-mobile.png') if _has(folder, name)), None)
    sources_ready = False
    source_message = 'Ask your agent to save complete editable files.'
    try:
        source_files(folder)
        sources_ready = True
        source_message = ''
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    if failed:
        sources_ready = False
        source_message = 'Rendering did not finish. Ask your agent to rerender before downloading.'
    style = str(brief.get('selected_style') or folder.name)
    label, _, description = STYLES.get(style, {}).get('name', style.replace('-', ' ')).partition(' · ')
    return {'id': identifier, 'name': str(brief.get('name') or folder.name),
            'profile_url': _linkedin_profile(brief.get('profile_url')),
            'before_compatible': _same_subject(brief, before_info(root)),
            'style': style, 'style_name': label, 'style_description': description,
            'style_order': list(STYLES).index(style) if style in STYLES else len(STYLES),
            'folder': folder.relative_to(root).as_posix(), 'status': status, 'updating': rendering, 'downloads_ready': not (rendering or failed),
            'revision': _revision(folder), 'headline': _read(folder, 'headline.txt').decode('utf-8', errors='replace').strip(),
            'desktop': desktop, 'mobile': mobile,
            'source_available': sources_ready, 'source_message': source_message}


class _Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.background_supplied = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'img' and data.get('src') and re.search(r'landscape|texture', data.get('class', ''), re.I):
            self.background_supplied = True
        for attr in ('src', 'poster'):
            if data.get(attr):
                self.urls.append(data[attr])
        if tag == 'link' and data.get('href') and 'stylesheet' in data.get('rel', '').split():
            self.urls.append(data['href'])
        if data.get('srcset'):
            raise ValueError('Flatten srcset resources before exporting editable sources.')


def _dependencies(name, raw):
    if Path(name).suffix.lower() not in {'.html', '.css'}:
        return []
    text = raw.decode('utf-8')
    urls = []
    if name.endswith('.html'):
        parser = _Resources()
        parser.feed(text)
        urls.extend(parser.urls)
    # Rendered output uses ordinary url() tokens and data URIs; strip quotes.
    urls.extend(match.strip().strip('\"\'') for match in re.findall(r'url\(\s*([^)]*?)\s*\)', text, re.I))
    if re.search(r'@import\b', text, re.I):
        raise ValueError('Inline imported CSS before exporting editable sources.')
    result = []
    for value in urls:
        if value.startswith(('data:', '#')):
            continue
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or parsed.path.startswith('/'):
            raise ValueError('Editable sources need local relative resources, not remote or absolute URLs.')
        relative = unquote(parsed.path)
        if not relative:
            continue
        # Do not normalize parent traversal: even a currently benign ../ URL is
        # fragile after extraction and is rejected rather than silently copied.
        if '..' in PurePosixPath(relative).parts or '\\' in relative:
            raise ValueError('Editable resource paths must stay within their package.')
        dependency = str(PurePosixPath(name).parent / relative)
        if Path(dependency).suffix.lower() not in RESOURCE_EXTENSIONS:
            raise ValueError('Unsupported editable resource type.')
        result.append(dependency)
    return result


def source_files(folder):
    """Collect exact editable inputs and their local declared dependencies."""
    if not _has(folder, 'brief.json') or not _has(folder, 'banner.html'):
        raise ValueError('Editable files are missing. Ask your agent to save brief.json and banner.html.')
    files = {name: _read(folder, name) for name in (*UPLOADS, *PREVIEWS, *SOURCES) if _has(folder, name)}
    brief = json.loads(files['brief.json'])
    if not isinstance(brief, dict):
        raise ValueError('Invalid editable brief.')
    from .visual_assets import BANNER_PHOTO_STYLES
    if brief.get('selected_style') in BANNER_PHOTO_STYLES and not _has(folder, 'banner-photo-cutout.png'):
        raise ValueError('Save banner-photo-cutout.png beside the brief for an editable photo-led package.')
    resources = _Resources()
    resources.feed(files['banner.html'].decode('utf-8'))
    if resources.background_supplied and not any(_has(folder, name) for name in ('background.png', 'background.jpg')):
        raise ValueError('Save the supplied background image beside the editable brief.')
    logos = brief.get('logo_assets', {})
    if not isinstance(logos, dict):
        raise ValueError('Invalid logo inputs.')
    for key, name in logos.items():
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', key) or name != f'logos/{key}.png':
            raise ValueError('Invalid declared logo input.')
        files[name] = _read(folder, name)
    if brief.get('logo_assets'):
        files['logos/provenance.json'] = _read(folder, 'logos/provenance.json')
    if brief.get('company_brand'):
        from .company_brand import load_brand
        _, dependencies = load_brand(folder, brief['company_brand'])
        for path in dependencies:
            relative = path.relative_to(folder).as_posix()
            files[relative] = _read(folder, relative)
    pending = list(files)
    while pending:
        name = pending.pop()
        for dependency in _dependencies(name, files[name]):
            if dependency not in files:
                files[dependency] = _read(folder, dependency)
                pending.append(dependency)
        if sum(map(len, files.values())) > MAX_ARCHIVE:
            raise ValueError('Editable sources exceed the download limit.')
    files['EDITING.txt'] = (
        'Open banner.html to edit the banner. It preserves embedded fonts and photos.\n'
        'brief.json and included logo/brand assets are inputs for the original project renderer.\n'
        'Keep this folder together. Ask the same AI agent to revise and rerender it.\n'
        'The agent should retain banner-photo-cutout.png/background.png when those inputs are used.\n'
        'These are your local source files, not a license to redistribute third-party fonts or marks.\n'
        'Review facts, likeness and previews before uploading.\n').encode()
    return files


def archive(folder, kind):
    if _render_qa(folder).get('acceptance') in {'render_in_progress', 'render_failed'}:
        raise ValueError('The package render is incomplete. Ask your agent to finish it before downloading.')
    before = _revision(folder)
    if kind == 'uploads':
        files = {name: _read(folder, name) for name in (*UPLOADS, *PREVIEWS) if _has(folder, name)}
        if not all(name in files for name in UPLOADS):
            raise ValueError('Upload files are not complete yet.')
    elif kind == 'sources':
        files = source_files(folder)
    else:
        raise ValueError('Unknown download.')
    if sum(map(len, files.values())) > MAX_ARCHIVE:
        raise ValueError('Package exceeds the download limit.')
    if before != _revision(folder):
        raise ValueError('The package changed during download. Try again.')
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, raw in sorted(files.items()):
            bundle.writestr(name, raw)
    return result.getvalue()


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, root, port=8765):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError('Choose an existing output folder.')
        if not 0 <= port <= 65535:
            raise ValueError('Port must be between 0 and 65535.')
        super().__init__(('127.0.0.1', port), ReviewHandler)


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = 'LinkedInPreview'

    def log_message(self, *args):
        pass

    def _send(self, status, raw, content_type='text/plain; charset=utf-8', filename=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(raw)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        if self.headers.get('Host', '').lower() not in allowed:
            self._send(403, b'Only the local preview address is accepted.')
            return
        try:
            path = unquote(urlsplit(self.path).path)
            if path == '/':
                self._send(200, PAGE.encode(), 'text/html; charset=utf-8')
                return
            packages = discover(self.server.root)
            if path == '/api/packages':
                data = {'packages': [package_info(key, folder, self.server.root) for key, folder in packages.items()],
                        'before': before_info(self.server.root)}
                self._send(200, json.dumps(data).encode(), 'application/json; charset=utf-8')
                return
            if path.startswith('/before/') and path[8:] in BEFORE_ASSETS:
                raw = _read(self.server.root, 'before/' + path[8:])
                self._send(200, raw, 'image/png')
                return
            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[1] in packages:
                kind, identifier, name = parts
                folder = packages[identifier]
                if kind == 'asset' and name in ASSETS:
                    if name in UPLOADS and _render_qa(folder).get('acceptance') in {'render_in_progress', 'render_failed'}:
                        raise ValueError('The upload files are not complete.')
                    before = _revision(folder) if name in UPLOADS else None
                    raw = _read(folder, name)
                    if name in UPLOADS and (before != _revision(folder) or
                            _render_qa(folder).get('acceptance') in {'render_in_progress', 'render_failed'}):
                        raise ValueError('The upload files changed during download.')
                    self._send(200, raw, mimetypes.guess_type(name)[0] or 'application/octet-stream',
                               filename=name if name == 'headline.txt' else None)
                    return
                if kind == 'download' and name in {'uploads.zip', 'sources.zip'}:
                    self._send(200, archive(folder, name[:-4]), 'application/zip', f'linkedin-{identifier}-{name}')
                    return
            self._send(404, b'Not found.')
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # Keep paths, private file contents and low-level exceptions out of
            # browser responses. The agent can inspect its local project files.
            self._send(409, b'Package files are incomplete or changed. Ask your agent to check the output and retry.')


def serve(output, port=8765):
    with ReviewServer(output, port) as server:
        print(f'Open http://localhost:{server.server_port}/', flush=True)
        print('Local preview only. Keep this process running; Ctrl+C stops it.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


from .serve_page import PAGE
