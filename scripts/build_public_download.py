#!/usr/bin/env python3
"""Build a credential-checked public download from the exact staged Git tree.

The ZIP is deterministic for a given tree and Python/zlib version. It contains
one linkedin-packaging/ folder and preserves executable setup scripts. Nothing
is read from untracked working files. Run after staging the intended release.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

try:
    from .check_public_release import encoded_values, forbidden_path, load_known_values, scan_blob
except ImportError:  # Direct `python scripts/build_public_download.py` execution.
    from check_public_release import encoded_values, forbidden_path, load_known_values, scan_blob

TOP_FOLDER = 'linkedin-packaging'
REQUIRED = {
    '.env.example', '.gitignore', 'README.md', 'AGENTS.md', 'CLAUDE.md', 'LICENSE',
    'THIRD_PARTY.md', 'pyproject.toml', 'setup.sh', 'setup.ps1', 'package.sh',
    'linkedin_pack/__main__.py', 'linkedin_pack/cli.py', 'linkedin_pack/serve.py',
    'docs/agent-workflow.md',
}
FONT_LICENSES = {
    'Inter.ttf': 'Inter.OFL.txt',
    'Manrope.ttf': 'Manrope.OFL.txt',
    'DMSerifDisplay.ttf': 'DMSerifDisplay.OFL.txt',
    'DMSerifDisplay-Italic.ttf': 'DMSerifDisplay.OFL.txt',
    'CormorantGaramond.ttf': 'CormorantGaramond.OFL.txt',
}
MAX_ARCHIVE_BYTES = 100_000_000
MAX_EXPANDED_BYTES = 150_000_000
EMBEDDED_FONT = re.compile(rb'data:(?:font/|application/(?:x-font|font))[^,;\s]+;base64,[A-Za-z0-9+/]{80,}', re.I)
ARCHIVE_SUFFIXES = ('.zip', '.tar', '.tar.gz', '.tgz', '.gz', '.7z', '.rar')


class ReleaseError(ValueError):
    def __init__(self, issues):
        self.issues = sorted(set(issues))
        super().__init__('Public download checks failed.')


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def index_snapshot(root):
    """Capture blob IDs and modes so concurrent working-file edits cannot leak."""
    raw = git(root, 'ls-files', '--stage', '-z')
    entries = []
    issues = []
    for entry in filter(None, raw.split(b'\0')):
        header, raw_name = entry.split(b'\t', 1)
        mode, object_id, stage = header.decode('ascii').split()
        name = raw_name.decode('utf-8')
        path = PurePosixPath(name)
        if (path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
                or path.as_posix() != name or not name or any(ord(c) < 32 for c in name)):
            issues.append((name, 'unsafe archive path'))
        if stage != '0':
            issues.append((name, 'unmerged Git index'))
        if mode not in {'100644', '100755'}:
            issues.append((name, 'only regular files may be released'))
        entries.append((name, mode, object_id))
    if not entries:
        issues.append(('.', 'empty Git index'))
    if issues:
        raise ReleaseError(issues)
    return raw, sorted(entries)


def content_issues(name, content, paths, variants):
    issues = scan_blob(name, content, variants)
    path = PurePosixPath(name)
    if forbidden_path(name):
        issues.append((name, 'private or generated path'))
    if name.lower().endswith(ARCHIVE_SUFFIXES):
        issues.append((name, 'nested archives are not public source files'))
    if path.suffix.lower() in {'.woff', '.woff2', '.ttf', '.otf', '.eot'}:
        license_name = FONT_LICENSES.get(path.name) if path.parent.as_posix() == 'assets/fonts' else None
        if not license_name or 'assets/fonts/' + license_name not in paths:
            issues.append((name, 'font is outside the bundled OFL allowlist'))
    if EMBEDDED_FONT.search(content):
        issues.append((name, 'embedded font bytes require separate license review'))
    if path.parts[0] == 'examples' and path.suffix == '.html' and name != 'examples/index.html':
        issues.append((name, 'only the public gallery HTML is distributable'))
    if path.parts[0] in {'examples', 'references'} and (path.name in {'raw.json', 'profile.json', 'supplements.json'} or 'source' in path.parts or 'reviews' in path.parts):
        issues.append((name, 'raw profile/research records are excluded'))
    if re.search(rb'/Users/[A-Za-z0-9._-]+/', content):
        issues.append((name, 'private machine path'))
    return issues


def build_bytes(root, *, credentials=(), environment=None):
    root = Path(root).resolve()
    known = load_known_values(credentials, environment)
    variants = encoded_values(known)
    snapshot, entries = index_snapshot(root)
    source_tree = git(root, 'write-tree').decode().strip()
    paths = {name for name, _, _ in entries}
    issues = [(name, 'required agent release file is not staged') for name in sorted(REQUIRED - paths)]
    files = []
    expanded = 0
    for name, mode, object_id in entries:
        content = git(root, 'cat-file', 'blob', object_id)
        expanded += len(content)
        issues.extend(content_issues(name, content, paths, variants))
        files.append((name, mode, content))
    if expanded > MAX_EXPANDED_BYTES:
        issues.append(('.', 'source tree exceeds public archive size budget'))
    if git(root, 'ls-files', '--stage', '-z') != snapshot:
        issues.append(('.', 'Git index changed during the build; stage and retry'))
    if issues:
        raise ReleaseError(issues)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, mode, content in files:
            info = zipfile.ZipInfo(f'{TOP_FOLDER}/{name}', date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | (0o755 if mode == '100755' else 0o644)) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compresslevel=9)
    data = buffer.getvalue()
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ReleaseError([('.', 'compressed ZIP exceeds public static-file size budget')])
    # Independently scan the final compressed artifact and every nested member.
    archive_issues = scan_blob('public-download.zip', data, variants)
    if archive_issues:
        raise ReleaseError(archive_issues)
    try:
        base_commit = git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
        committed_tree = git(root, 'rev-parse', 'HEAD^{tree}').decode().strip()
    except subprocess.CalledProcessError:
        base_commit, committed_tree = None, None
    manifest = {
        'schema_version': 1,
        'top_folder': TOP_FOLDER,
        'sha256': hashlib.sha256(data).hexdigest(),
        'bytes': len(data),
        'expanded_bytes': expanded,
        'file_count': len(files),
        'source_tree': source_tree,
        'source_commit': base_commit if committed_tree == source_tree else None,
        'base_commit': base_commit,
        'credential_scan': 'passed',
    }
    return data, manifest


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.', delete=False) as temp:
        temp.write(content)
        temporary = Path(temp.name)
    try:
        os.chmod(temporary, 0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True, help='Destination ZIP file; manifest is written beside it.')
    parser.add_argument('--credentials', action='append', default=[], metavar='PATH', help='Private key file or containing folder; repeat as needed. Values are never printed.')
    args = parser.parse_args(argv)
    try:
        data, manifest = build_bytes(args.root, credentials=args.credentials)
        atomic_write(args.output, data)
        atomic_write(args.output.with_suffix('.json'), (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
        print(json.dumps(manifest, sort_keys=True))
        return 0
    except ReleaseError as error:
        variants = encoded_values(load_known_values(args.credentials))
        print(json.dumps({'status': 'failed', 'findings': len(error.issues)}))
        for name, reason in error.issues:
            for value in variants:
                name = name.replace(value.decode('utf-8', errors='replace'), '[redacted]')
            print(name + ': ' + reason)
        return 1
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError):
        print('Public download build could not complete. Check the staged tree and destination; no credential values were printed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
