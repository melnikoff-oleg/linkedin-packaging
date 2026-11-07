"""Optional website context and brand extraction through Firecrawl v2.

One request retrieves both Markdown and branding. No SDK or language-model key
is required. Provider and scraped-page failures stay distinct from useful data.
"""
from __future__ import annotations

import ipaddress
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class FirecrawlError(RuntimeError):
    """A Firecrawl request failed or did not return usable website content."""


def _validate_url(url: str) -> str:
    url = url.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Website must be a public http:// or https:// URL.')
    if parsed.username or parsed.password:
        raise ValueError('Website URL must not contain credentials.')
    host = parsed.hostname.lower().rstrip('.')
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise ValueError('Website must be publicly accessible.')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('Website must be publicly accessible.')
    return url


def _write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(path)


def scrape_website(
    url: str,
    api_key: str | None = None,
    output_dir: str | Path | None = None,
    *,
    force: bool = False,
    timeout: int = 90,
) -> dict:
    """Return source URL, timestamp, Markdown, branding, metadata and warnings.

    If output_dir is supplied, save website.json and website.md and reuse that
    cache for the exact same URL. Set force=True to explicitly refresh it.
    A missing branding object is reported, never replaced with invented tokens.
    Calls are not retried automatically: an ambiguous network failure can have
    already consumed credits. The caller may retry after reviewing the error.
    """
    url = _validate_url(url)
    destination = Path(output_dir) if output_dir is not None else None
    cache = destination / 'website.json' if destination else None
    if cache and cache.exists() and not force:
        try:
            cached = json.loads(cache.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            cached = {}
        if (isinstance(cached, dict) and cached.get('source_url') == url
                and (cached.get('markdown') or cached.get('branding'))):
            return cached
    key = api_key or os.environ.get('FIRECRAWL_API_KEY', '')
    if not key:
        raise FirecrawlError('Set FIRECRAWL_API_KEY to scrape website context.')
    payload = {'url': url, 'formats': ['markdown', 'branding'],
               'onlyMainContent': False, 'timeout': 60000}
    req = Request('https://api.firecrawl.dev/v2/scrape',
                  data=json.dumps(payload).encode(), method='POST',
                  headers={'Authorization': f'Bearer {key}',
                           'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as reply:
            raw = reply.read(20_000_001)
        if len(raw) > 20_000_000:
            raise FirecrawlError('Firecrawl response exceeds the 20 MB local limit.')
        result = json.loads(raw)
    except HTTPError as exc:
        remedies = {401: 'Check FIRECRAWL_API_KEY.', 402: 'Check the Firecrawl credit balance.',
                    403: 'Check API permissions and website accessibility.',
                    429: 'Rate limit reached; wait before retrying.'}
        raise FirecrawlError(f'Firecrawl HTTP {exc.code}. '
                             + remedies.get(exc.code, 'Review the provider dashboard before retrying.')) from None
    except (URLError, TimeoutError, OSError):
        raise FirecrawlError('Firecrawl connection failed. Check the provider dashboard before retrying.') from None
    except (ValueError, UnicodeError):
        raise FirecrawlError('Firecrawl returned invalid JSON.') from None
    if not isinstance(result, dict) or result.get('success') is not True:
        raise FirecrawlError('Firecrawl did not report success. Review the provider dashboard.')
    data = result.get('data')
    if not isinstance(data, dict):
        raise FirecrawlError('Firecrawl returned no website data.')
    metadata = data.get('metadata') if isinstance(data.get('metadata'), dict) else {}
    status = metadata.get('statusCode')
    if isinstance(status, int) and status >= 400:
        raise FirecrawlError(f'The website returned HTTP {status}; context was not accepted.')
    if metadata.get('error'):
        raise FirecrawlError('The website scrape returned an error; context was not accepted.')
    markdown = data.get('markdown') if isinstance(data.get('markdown'), str) else ''
    branding = data.get('branding') if isinstance(data.get('branding'), dict) else {}
    if not markdown.strip() and not branding:
        raise FirecrawlError('Firecrawl returned neither text nor branding.')
    normalized = {
        'source_url': url,
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'provider': 'firecrawl/v2/scrape',
        'markdown': markdown,
        'branding': branding,
        'metadata': metadata,
        'warnings': ([] if branding else ['branding_missing'])
                    + ([] if markdown.strip() else ['markdown_missing']),
    }
    if destination:
        destination.mkdir(parents=True, exist_ok=True)
        _write(cache, json.dumps(normalized, ensure_ascii=False, indent=2) + '\n')
        _write(destination / 'website.md', markdown.rstrip() + '\n')
    return normalized
