import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from linkedin_pack.providers.firecrawl import FirecrawlError, scrape_website


class Reply(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def response(data):
    return Reply(json.dumps(data).encode())


class FirecrawlTests(unittest.TestCase):
    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_scrapes_content_and_branding_in_single_request(self, opener):
        opener.return_value = response({'success': True, 'data': {
            'markdown': '# Acme', 'branding': {'colors': {'primary': '#123456'}},
            'metadata': {'title': 'Acme', 'statusCode': 200}}})
        result = scrape_website('https://example.com', 'private-key')
        req = opener.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.firecrawl.dev/v2/scrape')
        self.assertEqual(json.loads(req.data)['formats'], ['markdown', 'branding'])
        self.assertEqual(req.get_header('Authorization'), 'Bearer private-key')
        self.assertEqual(result['branding']['colors']['primary'], '#123456')
        self.assertEqual(result['source_url'], 'https://example.com')

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_cache_is_reused_but_not_for_another_website(self, opener):
        opener.side_effect = [response({'success': True, 'data': {'markdown': 'A'}}),
                              response({'success': True, 'data': {'markdown': 'B'}})]
        with tempfile.TemporaryDirectory() as td:
            scrape_website('https://example.com', 'key', td)
            cached = scrape_website('https://example.com', 'key', td)
            fresh = scrape_website('https://different.example.com', 'key', td)
            self.assertEqual(cached['markdown'], 'A')
            self.assertEqual(fresh['markdown'], 'B')
            self.assertEqual(opener.call_count, 2)
            self.assertNotIn('key', (Path(td) / 'website.json').read_text())
            self.assertEqual((Path(td) / 'website.md').read_text(), 'B\n')

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_rate_limit_error_does_not_leak_response_or_credentials(self, opener):
        opener.side_effect = HTTPError('https://api.firecrawl.dev/v2/scrape', 429, 'no', {},
                                      io.BytesIO(b'{"error":"private-key"}'))
        with self.assertRaises(FirecrawlError) as cm:
            scrape_website('https://example.com', 'private-key')
        self.assertIn('429', str(cm.exception))
        self.assertNotIn('private-key', str(cm.exception))

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_unusable_scrape_is_not_reported_as_success(self, opener):
        opener.return_value = response({'success': True, 'data': {'markdown': 'Blocked',
                                                                'metadata': {'statusCode': 403}}})
        with self.assertRaises(FirecrawlError):
            scrape_website('https://example.com', 'key')

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_missing_branding_is_explicit(self, opener):
        opener.return_value = response({'success': True, 'data': {'markdown': 'Hello'}})
        result = scrape_website('https://example.com', 'key')
        self.assertEqual(result['branding'], {})
        self.assertIn('branding_missing', result['warnings'])

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_rejects_invalid_urls_before_paid_request(self, opener):
        for url in ['file:///etc/passwd', 'http://localhost', 'http://127.0.0.1',
                    'https://user:secret@example.com', 'ftp://example.com']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                scrape_website(url, 'key')
        opener.assert_not_called()

    @patch('linkedin_pack.providers.firecrawl.urlopen')
    def test_false_success_and_empty_response_raise(self, opener):
        for data in [{'success': False, 'error': 'key'}, {'success': True, 'data': {}}]:
            opener.return_value = response(data)
            with self.assertRaises(FirecrawlError):
                scrape_website('https://example.com', 'key')


if __name__ == '__main__':
    unittest.main()
