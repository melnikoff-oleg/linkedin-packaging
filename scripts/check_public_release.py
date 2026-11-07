#!/usr/bin/env python3
"""Scan public files or the exact Git index without printing credential values.

This is a defensive release check, not a guarantee that every possible secret
format is detectable. Known-value checks include raw and encoded forms and ZIP
members. Credential source files stay outside the release tree.
"""
from __future__ import annotations

import argparse
import base64
import fnmatch
import gzip
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote, quote_plus

SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.cache', 'tmp', 'output', 'dist',
             'build', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
FORBIDDEN_DIRS = SKIP_DIRS | {'brands', 'test_account'}
MAX_BYTES = 150_000_000
KEY_NAME = re.compile(r'(?:API[_-]?KEY|ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|SECRET|PASSWORD|PRIVATE[_-]?KEY)', re.I)
ASSIGNMENT = re.compile(r'''["']?([A-Za-z_][A-Za-z_0-9-]*)["']?\s*[:=]\s*["']?([^\s"',;#}]+)''')
TOKEN_PATTERNS = (
    re.compile(rb'apify_api_[A-Za-z0-9_-]{20,}'),
    re.compile(rb'\bfc-[A-Za-z0-9_-]{24,}'),
    re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{40,}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
)


def placeholder(value):
    return (len(value) < 8 or value.lower().startswith(('your_', 'example_', 'test_', 'fake_', 'dummy_'))
            or value.lower() in {'placeholder', 'changeme', 'change_me', 'redacted', 'secret', 'api_key'})


def credential_values(text):
    """Collect every assignment; do not apply environment precedence."""
    return {match[2] for match in ASSIGNMENT.finditer(text)
            if KEY_NAME.search(match[1]) and not placeholder(match[2])}


def load_known_values(sources=(), environment=None):
    values = set()
    for source in sources:
        path = Path(source)
        if path.is_dir():
            files = set(path.glob('.env*')) | set(path.glob('api_keys*'))
        else:
            files = {path}
        for file in files:
            if file.is_file() and file.name != '.env.example':
                values.update(credential_values(file.read_text(encoding='utf-8', errors='replace')))
    environment = os.environ if environment is None else environment
    values.update(value for name, value in environment.items()
                  if KEY_NAME.search(name) and not placeholder(value))
    return values


def encoded_values(values):
    variants = set()
    for value in values:
        raw = value.encode('utf-8')
        variants.update((raw, quote(value, safe='').encode(), quote_plus(value, safe='').encode(),
                         base64.b64encode(raw), base64.urlsafe_b64encode(raw),
                         base64.b64encode(raw).rstrip(b'='), base64.urlsafe_b64encode(raw).rstrip(b'='),
                         ''.join(f'%{byte:02X}' for byte in raw).encode(),
                         ''.join(f'%{byte:02x}' for byte in raw).encode()))
    return {value for value in variants if len(value) >= 8}


def forbidden_path(name):
    if "!" in name:
        return any(forbidden_path(part) for part in name.split("!"))
    path = Path(name)
    if any(part in FORBIDDEN_DIRS or part.endswith('.egg-info') for part in path.parts):
        return True
    filename = path.name.lower()
    return (filename.startswith('.env') and filename != '.env.example'
            or filename.startswith('api_keys')
            or any(fnmatch.fnmatch(filename, pattern) for pattern in
                   ('*.pem', '*.key', '*.p12', '*.pfx', '*credentials*.json', 'secrets.*',
                    '*.secret', '*.bak', '*.backup', '*.old', '*.orig', '*.swp', '*.swo', '*~', '*.log', '*.pyc')))


def scan_blob(name, content, variants, *, depth=0):
    issues = []
    if forbidden_path(name):
        issues.append((name, 'private or generated path'))
    if any(value in content for value in variants):
        issues.append((name, 'known credential or encoded variant'))
    if any(pattern.search(content) for pattern in TOKEN_PATTERNS):
        issues.append((name, 'credential token/private-key pattern'))
    if credential_values(content.decode('utf-8', errors='replace')):
        # Source expressions are not credentials. Only literal-looking values
        # of 20+ characters receive this independent heuristic warning.
        if any(len(value) >= 20 and re.fullmatch(r'[A-Za-z0-9_+/=.-]+', value)
               for value in credential_values(content.decode('utf-8', errors='replace'))):
            issues.append((name, 'long credential assignment'))
    if len(content) > MAX_BYTES:
        return issues + [(name, 'file too large to complete release scan')]
    if content.startswith(b'PK\x03\x04'):
        if depth >= 3:
            return issues + [(name, 'archive nesting exceeds scan limit')]
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                members = archive.infolist()
                if sum(item.file_size for item in members) > MAX_BYTES:
                    return issues + [(name, 'expanded archive exceeds scan limit')]
                for item in members:
                    if not item.is_dir():
                        issues.extend(scan_blob(name + '!' + item.filename, archive.read(item), variants, depth=depth+1))
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile):
            issues.append((name, 'archive could not be scanned'))
    elif content.startswith(b'\x1f\x8b'):
        if depth >= 3:
            return issues + [(name, 'archive nesting exceeds scan limit')]
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as archive:
                expanded = archive.read(MAX_BYTES + 1)
            issues.extend(scan_blob(name + '!expanded', expanded, variants, depth=depth+1))
        except (OSError, EOFError, ValueError):
            issues.append((name, 'compressed data could not be scanned'))
    return issues


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def candidate_files(root, staged=False):
    if staged:
        # ls-files covers the entire index, including unchanged already tracked
        # files. Reading :path inspects exactly what a commit would contain.
        for raw_name in git(root, 'ls-files', '--cached', '-z').split(b'\0'):
            if raw_name:
                name = os.fsdecode(raw_name)
                yield name, git(root, 'show', ':' + name)
        return
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS or part.endswith('.egg-info') for part in relative.parts):
            continue
        if path.name.startswith('.env') and path.name != '.env.example' or path.name.startswith('api_keys'):
            continue  # Local ignored configuration is not a release candidate.
        if path.is_symlink():
            yield relative.as_posix(), b''
        elif path.is_file():
            yield relative.as_posix(), path.read_bytes()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--staged', action='store_true', help='Scan the exact complete Git index, not working files.')
    parser.add_argument('--credentials', action='append', default=[], metavar='PATH',
                        help='Local file or directory containing known keys. May be repeated; values are never printed.')
    args = parser.parse_args(argv)
    try:
        values = load_known_values(args.credentials)
        variants = encoded_values(values)
        issues = []
        count = 0
        for name, content in candidate_files(args.root.resolve(), args.staged):
            count += 1
            issues.extend(scan_blob(name, content, variants))
            if not args.staged and (args.root / name).is_symlink():
                issues.append((name, 'symbolic link requires explicit release review'))
        if count == 0:
            issues.append(('.', 'no release files found'))
        print(json.dumps({'files_scanned': count, 'known_credentials': len(values),
                          'findings': len(set(issues)), 'mode': 'git-index' if args.staged else 'working-release-files'}))
        for name, reason in sorted(set(issues)):
            # Even a malicious filename cannot echo known secret bytes.
            safe_name = name
            for value in variants:
                safe_name = safe_name.replace(value.decode('utf-8', errors='replace'), '[redacted]')
            print(safe_name + ': ' + reason)
        return 1 if issues else 0
    except (OSError, ValueError, subprocess.CalledProcessError):
        print('Release scan could not complete. Check the paths and Git index; no secret values were printed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
