"""Contract tests written before the Apify adapter implementation."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from linkedin_pack.providers.apify import canonical_profile_url, normalize_profile, ApifyClient, ApifyError


class ProfileTests(unittest.TestCase):
    def test_urls_are_canonical_and_offsite_urls_rejected(self):
        self.assertEqual(canonical_profile_url('https://uk.linkedin.com/in/some-person/?x=1'), 'https://www.linkedin.com/in/some-person/')
        for url in ['https://linkedin.com.evil.test/in/x/', 'file:///etc/passwd', 'https://www.linkedin.com/company/test']:
            with self.assertRaises(ValueError): canonical_profile_url(url)

    def test_profile_paths_cannot_escape_destination(self):
        for handle in ['.', '..', '%2e%2e', '%2fetc', '%252fetc', 'test%5cpath']:
            with self.assertRaises(ValueError):
                canonical_profile_url('https://linkedin.com/in/' + handle + '/')

    def test_normalizes_harvest_fields_without_rewriting_headline(self):
        row={'publicIdentifier':'sample','linkedinUrl':'https://www.linkedin.com/in/sample', 'firstName':'A','lastName':'B','headline':'I build | 100% real','about':'Story','photo':'https://media.licdn.com/portrait.jpg','backgroundPicture':'https://media.licdn.com/banner.jpg','followerCount':123,'experience':[{'companyName':'Example'}],'education':[]}
        p=normalize_profile(row, fetched_at='2026-11-06T00:00:00Z')
        self.assertEqual(p['name'],'A B'); self.assertEqual(p['headline'],row['headline'])
        self.assertEqual(p['banner_url'],row['backgroundPicture']); self.assertEqual(p['portrait_url'],row['photo'])
        self.assertEqual(p['source']['fetched_at'],'2026-11-06T00:00:00Z')
        self.assertEqual(p['follower_count'],123)

    def test_missing_images_are_explicit(self):
        p=normalize_profile({'publicIdentifier':'sample','firstName':'A','lastName':'B','headline':'X'})
        self.assertIsNone(p['banner_url']); self.assertIsNone(p['portrait_url'])
        self.assertIn('banner_missing',p['warnings'])

    def test_actor_error_is_not_treated_as_profile(self):
        with self.assertRaises(ApifyError): normalize_profile({'error':'Not found','url':'https://linkedin.com/in/sample/'})

    def test_credentials_are_not_embedded_in_url(self):
        client=ApifyClient('secret-token')
        with patch.object(client,'_request',side_effect=[{'data':{'id':'run','status':'SUCCEEDED','defaultDatasetId':'dataset'}}, []]) as request:
            self.assertEqual(client.scrape(['https://linkedin.com/in/sample/']),[])
        for call in request.call_args_list: self.assertNotIn('secret-token',str(call.args))
        body=request.call_args_list[0].kwargs['payload']
        self.assertEqual(body['profileScraperMode'],'Profile details no email ($4 per 1k)')

    def test_failed_run_raises(self):
        client=ApifyClient('key')
        with patch.object(client,'_request',return_value={'data':{'id':'run','status':'FAILED','statusMessage':'upstream failed'}}):
            with self.assertRaises(ApifyError): client.scrape(['https://linkedin.com/in/sample/'])

    def test_cache_prevents_second_billable_run(self):
        client=ApifyClient('key')
        with TemporaryDirectory() as td:
            with patch.object(client,'_request',side_effect=[{'data':{'id':'run','status':'SUCCEEDED','defaultDatasetId':'dataset'}}, [{'publicIdentifier':'sample'}]]) as request:
                first=client.scrape(['https://linkedin.com/in/sample/'], cache_dir=Path(td))
                second=client.scrape(['https://linkedin.com/in/sample/'], cache_dir=Path(td))
                self.assertEqual(first,second); self.assertEqual(request.call_count,2)

    def test_unknown_submission_is_not_resubmitted(self):
        client = ApifyClient('key')
        with TemporaryDirectory() as td:
            with patch.object(client, '_request', side_effect=TimeoutError):
                with self.assertRaises(ApifyError):
                    client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
            with patch.object(client, '_request') as request:
                with self.assertRaisesRegex(ApifyError, 'unknown'):
                    client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
                request.assert_not_called()

    def test_concurrent_scrape_cannot_submit_twice(self):
        client = ApifyClient('key')
        with TemporaryDirectory() as td:
            def reply(path, **kwargs):
                if kwargs.get('payload'):
                    with self.assertRaisesRegex(ApifyError, 'lock'):
                        client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
                    return {'data': {'id': 'run', 'status': 'SUCCEEDED', 'defaultDatasetId': 'dataset'}}
                return []
            with patch.object(client, '_request', side_effect=reply) as request:
                client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
                self.assertEqual(request.call_count, 2)
            self.assertFalse(list(Path(td).glob('*.lock')))

    def test_known_run_resumes_after_poll_failure(self):
        client = ApifyClient('key')
        with TemporaryDirectory() as td:
            with patch('linkedin_pack.providers.apify.time.sleep'), patch.object(client, '_request', side_effect=[
                {'data': {'id': 'legacy-run', 'status': 'RUNNING', 'defaultDatasetId': 'dataset'}},
                ApifyError('poll failure'),
            ]):
                with self.assertRaises(ApifyError):
                    client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
            with patch('linkedin_pack.providers.apify.time.sleep'), patch.object(client, '_request', side_effect=[
                {'data': {'id': 'legacy-run', 'status': 'SUCCEEDED', 'defaultDatasetId': 'dataset'}}, [],
            ]) as request:
                self.assertEqual(client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td), [])
                self.assertTrue(all('payload' not in call.kwargs for call in request.call_args_list))

    def test_interrupted_submission_remains_unknown_and_unlocks(self):
        client = ApifyClient('key')
        with TemporaryDirectory() as td:
            with patch.object(client, '_request', side_effect=KeyboardInterrupt):
                with self.assertRaisesRegex(ApifyError, 'unknown'):
                    client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
            self.assertFalse(list(Path(td).glob('*.lock')))
            with patch.object(client, '_request') as request:
                with self.assertRaisesRegex(ApifyError, 'unknown'):
                    client.scrape(['https://linkedin.com/in/sample/'], cache_dir=td)
                request.assert_not_called()

if __name__=='__main__': unittest.main()
