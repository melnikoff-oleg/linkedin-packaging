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
import zipfile
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

UPLOADS = ('banner.png', 'portrait.png', 'headline.txt')
PREVIEWS = ('preview.png', 'preview-mobile.png', 'review-desktop.png', 'review-mobile.png')
SOURCES = ('brief.json', 'banner.html', 'preview.html', 'preview-mobile.html',
           'banner-photo-cutout.png', 'banner-photo.png', 'background.png', 'background.jpg')
ASSETS = frozenset((*UPLOADS, *PREVIEWS))
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
                        and child.name.lower() not in BLOCKED):
                    pending.append((child, depth + 1))
    def order(item):
        folder = item[1]
        newest = max((_local(folder, name).stat().st_mtime_ns for name in (*UPLOADS, *PREVIEWS) if _has(folder, name)), default=0)
        return (-newest, folder.as_posix())
    return dict(sorted(found.items(), key=order))


def package_info(identifier, folder, root):
    brief = _optional_json(folder, 'brief.json')
    qa = _optional_json(folder, 'qa.json')
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
    return {'id': identifier, 'name': str(brief.get('name') or folder.name),
            'style': str(brief.get('selected_style') or folder.name),
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
    if _optional_json(folder, 'qa.json').get('acceptance') in {'render_in_progress', 'render_failed'}:
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
                data = {'packages': [package_info(key, folder, self.server.root) for key, folder in packages.items()]}
                self._send(200, json.dumps(data).encode(), 'application/json; charset=utf-8')
                return
            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[1] in packages:
                kind, identifier, name = parts
                folder = packages[identifier]
                if kind == 'asset' and name in ASSETS:
                    if name in UPLOADS and _optional_json(folder, 'qa.json').get('acceptance') in {'render_in_progress', 'render_failed'}:
                        raise ValueError('The upload files are not complete.')
                    raw = _read(folder, name)
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


PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Your LinkedIn packaging</title><style>
*{box-sizing:border-box}body{margin:0;background:#020b18;color:#d0d6e0;font:16px/1.55 system-ui,-apple-system,sans-serif}main{max-width:1120px;margin:auto;padding:42px 24px 64px}h1,h2,p{margin:0}h1{font-size:clamp(28px,4vw,42px);letter-spacing:-.04em;line-height:1.15}h2{font-size:22px;letter-spacing:-.025em}.muted{color:#8a93a3}.intro{margin-top:12px;max-width:650px}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:#6091ff;margin-bottom:12px}.notice{margin-top:24px;padding:14px 18px;background:#07142a;border:1px solid #d0d6e01a;border-radius:12px}.package{margin-top:36px;padding:24px;background:linear-gradient(145deg,#07142a,#040e1e);border:1px solid #d0d6e01a;border-radius:20px}.row{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px}.status{font-size:13px;color:#a4aec0;margin-top:5px}.tabs{display:flex;gap:8px;flex-wrap:wrap}button,a.button{font:600 14px/1.4 system-ui;color:#d0d6e0;border:1px solid #d0d6e030;background:transparent;border-radius:999px;min-height:44px;padding:11px 17px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;text-align:center}button:hover,a.button:hover{border-color:#6894ff}button:focus-visible,a:focus-visible,textarea:focus-visible{outline:2px solid #85a8ff;outline-offset:3px}button[aria-pressed=true],a.primary{background:#2863f0;border-color:#2863f0;color:white}button:disabled,a.disabled{opacity:.45;pointer-events:none}.preview{display:flex;justify-content:center;margin-top:22px;min-height:120px}.preview img{max-width:100%;height:auto;border-radius:12px;border:1px solid #d0d6e020;object-fit:contain;align-self:flex-start}.preview img.mobile{max-width:min(390px,100%)}.headline{margin-top:20px;padding:18px;border:1px solid #d0d6e020;background:#020b18;border-radius:12px}.headline p{overflow-wrap:anywhere}.headline button{margin-top:12px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.assets{margin-top:14px;display:flex;gap:18px;flex-wrap:wrap}.assets a{color:#80a7ff;font-size:14px;min-height:44px;display:inline-flex;align-items:center}.feedback{margin-top:22px;border-top:1px solid #d0d6e01a;padding-top:20px}.feedback label{font-weight:600;display:block;margin-bottom:10px}textarea{width:100%;min-height:90px;background:#020b18;color:#d0d6e0;border:1px solid #d0d6e030;border-radius:10px;padding:12px;font:inherit;resize:vertical}.feedback .row{margin-top:10px}.small{font-size:13px}.empty{padding:42px 0;max-width:600px}.error{color:#ffc78a}footer{margin-top:24px;font-size:13px;color:#8a93a3}a{color:#80a7ff}@media(max-width:600px){main{padding:28px 20px 40px}.package{padding:16px;margin-top:26px}.actions a{flex:1 1 140px}.row{align-items:flex-start}.feedback .row{display:block}.feedback button{margin-top:10px}}
</style></head><body><main><p class="eyebrow">Local preview</p><h1>Your LinkedIn packaging</h1><p class="intro muted">Review the full profile, download your files, or send changes back to your AI agent.</p><div id="connection" class="notice" role="status">Loading your packages…</div><div id="packages"></div><footer>Only available on this computer. Nothing posts to LinkedIn.</footer></main><script>
const root=document.getElementById('packages'),connection=document.getElementById('connection'),cards=new Map();
const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node};
async function copy(text,button){try{await navigator.clipboard.writeText(text);button.textContent='Copied';setTimeout(()=>button.textContent=button.dataset.label,1800)}catch{connection.textContent='Copy failed. Select the text and copy it manually.'}}
function copyButton(label,getText){const b=el('button',label);b.type='button';b.dataset.label=label;b.addEventListener('click',()=>copy(getText(),b));return b}
function asset(p,name){return '/asset/'+p.id+'/'+name+'?v='+p.revision}
function makeCard(p){
 const card=el('section',undefined,'package');card.dataset.id=p.id;const head=el('div',undefined,'row'),titles=el('div'),name=el('h2'),revision=el('p',undefined,'small muted'),status=el('p',undefined,'status'),tabs=el('div',undefined,'tabs');titles.append(name,revision,status);head.append(titles,tabs);
 const preview=el('div',undefined,'preview'),image=el('img');image.alt='Assembled LinkedIn profile preview';preview.append(image);
 const headline=el('div',undefined,'headline'),headlineText=el('p');headline.append(headlineText,copyButton('Copy headline',()=>cards.get(p.id).data.headline));
 const actions=el('div',undefined,'actions'),uploads=el('a','Download upload files','button primary'),sources=el('a','Download editable sources','button');uploads.href='/download/'+p.id+'/uploads.zip';sources.href='/download/'+p.id+'/sources.zip';actions.append(uploads,sources);
 const sourceNote=el('p',undefined,'small muted');
 const assets=el('div',undefined,'assets');for(const [file,label] of [['banner.png','Banner PNG'],['portrait.png','Portrait PNG'],['headline.txt','Headline TXT']]){const a=el('a',label);a.href='/asset/'+p.id+'/'+file;a.download=file;assets.append(a)}
 const feedback=el('div',undefined,'feedback'),label=el('label','Want a change?'),text=el('textarea');text.id='feedback-'+p.id;label.htmlFor=text.id;text.placeholder='Make the headline more specific. Use a warmer background…';const feedbackRow=el('div',undefined,'row'),hint=el('p','Paste the feedback into the same agent chat. Your preview updates here after it rerenders.', 'small muted');
 const feedbackButton=copyButton('Copy feedback',()=>{const d=cards.get(p.id).data;return 'Please revise my LinkedIn package '+d.folder+' ('+d.style+').\nChanges: '+(text.value.trim()||'[describe what to change]')+'\nKeep approved facts and identity intact. Reuse unchanged assets, save as a new revision, rerender it, visually check desktop and mobile, and give me the updated local preview plus upload and editable source files.'});feedbackRow.append(hint,feedbackButton);feedback.append(label,text,feedbackRow);
 card.append(head,preview,headline,actions,sourceNote,assets,feedback);
 const state={card,name,revision,status,tabs,image,headlineText,uploads,sources,sourceNote,data:p,mode:'desktop'};cards.set(p.id,state);
 for(const mode of ['desktop','mobile']){const button=el('button',mode==='desktop'?'Desktop':'Mobile');button.type='button';button.addEventListener('click',()=>{state.mode=mode;update(state,state.data)});tabs.append(button)}
 root.append(card);update(state,p);return state;
}
function update(state,p){state.data=p;state.name.textContent=p.name+' · '+p.style.replaceAll('-',' ');state.revision.textContent='Version: '+(p.folder==='.'?'current package':p.folder);state.status.textContent=p.status;state.headlineText.textContent=p.headline;const file=p[state.mode]||p.desktop||p.mobile;state.image.src=asset(p,file);state.image.className=state.mode==='mobile'?'mobile':'';[...state.tabs.children].forEach((button,i)=>{button.setAttribute('aria-pressed',String((i?'mobile':'desktop')===state.mode));button.disabled=!p[i?'mobile':'desktop']});state.uploads.classList.toggle('disabled',!p.downloads_ready);state.uploads.setAttribute('aria-disabled',String(!p.downloads_ready));state.card.querySelectorAll('.assets a').forEach(a=>{a.classList.toggle('disabled',!p.downloads_ready);a.style.pointerEvents=!p.downloads_ready?'none':'';a.setAttribute('aria-disabled',String(!p.downloads_ready));a.tabIndex=p.downloads_ready?0:-1});state.sources.classList.toggle('disabled',!p.downloads_ready||!p.source_available);state.sources.setAttribute('aria-disabled',String(!p.downloads_ready||!p.source_available));state.sourceNote.textContent=p.source_message||'';if(!p.downloads_ready){state.uploads.removeAttribute('href')}else{state.uploads.href='/download/'+p.id+'/uploads.zip'}if(!p.downloads_ready||!p.source_available){state.sources.removeAttribute('href')}else{state.sources.href='/download/'+p.id+'/sources.zip'};}
let inFlight=false;
async function refresh(){if(inFlight)return;inFlight=true;try{const response=await fetch('/api/packages',{cache:'no-store'});if(!response.ok)throw Error();const data=await response.json();const ids=new Set(data.packages.map(p=>p.id));for(const [id,state]of cards)if(!ids.has(id)){state.card.remove();cards.delete(id)}for(const [index,p] of data.packages.entries()){const old=cards.get(p.id);const state=old||makeCard(p);if(old&&(old.data.revision!==p.revision||old.data.status!==p.status||old.data.source_available!==p.source_available))update(old,p);if(root.children[index]!==state.card&&!state.card.contains(document.activeElement))root.insertBefore(state.card,root.children[index]||null)}connection.textContent=data.packages.length?'Changes refresh automatically. Check the draft before using it.':'No packages yet. Ask your agent to generate into the selected output folder; this page will update automatically.';connection.classList.toggle('error',false)}catch{connection.textContent='Preview connection lost. Ask your agent to restart the local preview.';connection.classList.add('error')}finally{inFlight=false}}
refresh();setInterval(refresh,2500);
</script></body></html>'''
