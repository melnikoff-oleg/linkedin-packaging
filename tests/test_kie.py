"""Provider contract and paid-request recovery tests (no network)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from linkedin_pack.providers.kie import KieClient, KieError, SubmissionUnknown, DEFAULT_IMAGE_MODEL

PNG = b'\x89PNG\r\n\x1a\n' + b'fixture'


class KieTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.client = KieClient('test-secret-key', cache_dir=self.root / 'cache')
        self.source = self.root / 'source.png'
        self.source.write_bytes(PNG)

    def test_missing_key_fails_before_network(self):
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(KieError):
            KieClient()

    def test_two_k_payload_and_completed_task_are_reused_across_outputs(self):
        responses = [
            {'code': 200, 'data': {'downloadUrl': 'https://cdn.example/input.png'}},
            {'code': 200, 'data': {'taskId': 't1'}},
            {'code': 200, 'data': {'state': 'success', 'resultJson': json.dumps({'resultUrls': ['https://cdn.example/out.png']}), 'creditsConsumed': 10}},
        ]
        with patch.object(self.client, '_request', side_effect=responses) as req, patch.object(self.client, '_download', return_value=PNG):
            first = self.client.generate_headshot(self.source, 'Keep this exact face.', self.root / 'out.png')
            second = self.client.generate_headshot(self.source, 'Keep this exact face.', self.root / 'second.png')
        self.assertEqual(first.read_bytes(), PNG)
        self.assertEqual(second.read_bytes(), PNG)
        self.assertEqual(req.call_count, 3)
        payload = req.call_args_list[1].args[2]
        self.assertEqual(payload['model'], DEFAULT_IMAGE_MODEL)
        self.assertEqual(payload['input']['resolution'], '2K')
        self.assertNotIn('background', payload['input'])
        self.assertEqual(payload['input']['aspect_ratio'], '1:1')
        self.assertNotIn('test-secret-key', ''.join(p.read_text() for p in (self.root / 'cache').glob('*.json')))

    def test_timeout_resumes_known_task_without_second_create(self):
        with patch.object(self.client, '_request', side_effect=[
            {'code': 200, 'data': {'taskId': 't1'}},
            {'code': 200, 'data': {'state': 'generating'}},
        ]) as req, self.assertRaises(TimeoutError):
            self.client.generate_headshot('https://cdn.example/input.png', 'Keep face', self.root / 'out.png', timeout=0)
        self.assertEqual(req.call_count, 2)
        with patch.object(self.client, '_request', return_value={'code': 200, 'data': {'state': 'success', 'resultJson': '{"resultUrls":["https://cdn.example/out.png"]}'}}) as req, patch.object(self.client, '_download', return_value=PNG):
            self.client.generate_headshot('https://cdn.example/input.png', 'Keep face', self.root / 'out.png')
        self.assertEqual(req.call_count, 1)
        self.assertEqual(req.call_args.args[0], 'GET')

    def test_ambiguous_submission_is_never_automatically_repeated(self):
        with patch.object(self.client, '_request', side_effect=TimeoutError), self.assertRaises(SubmissionUnknown):
            self.client.generate_headshot('https://cdn.example/in.png', 'Keep face', self.root / 'out.png')
        with patch.object(self.client, '_request') as req, self.assertRaises(SubmissionUnknown):
            self.client.generate_headshot('https://cdn.example/in.png', 'Keep face', self.root / 'out.png')
        req.assert_not_called()

    def test_failed_task_is_not_resubmitted(self):
        with patch.object(self.client, '_request', side_effect=[{'code': 200, 'data': {'taskId': 't1'}}, {'code': 200, 'data': {'state': 'fail', 'failCode': 'input', 'failMsg': 'invalid source'}}]), self.assertRaises(KieError):
            self.client.generate_headshot('https://cdn.example/in.png', 'Keep face', self.root / 'out.png')
        with patch.object(self.client, '_request') as req, self.assertRaises(KieError):
            self.client.generate_headshot('https://cdn.example/in.png', 'Keep face', self.root / 'out.png')
        req.assert_not_called()

    def test_invalid_inputs_fail_without_network(self):
        for source, prompt, resolution in [('http://cdn.example/in.png', 'face', '2K'), ('https://localhost/in.png', 'face', '2K'), ('https://cdn.example/in.png', '', '2K'), ('https://cdn.example/in.png', 'face', '9K')]:
            with self.subTest(source=source,prompt=prompt,resolution=resolution), patch.object(self.client, '_request') as req, self.assertRaises(ValueError):
                self.client.generate_headshot(source, prompt, self.root / 'out.png', resolution=resolution)
            req.assert_not_called()

    def test_brief_uses_responses_protocol_and_caches(self):
        response = {'status':'completed','output':[{'type':'reasoning','summary':[]},{'type':'message','content':[{'type':'output_text','text':'{"headline":"Founder"}'}]}], 'usage':{'output_tokens':10}}
        schema = {'type':'object','properties':{'headline':{'type':'string'}},'required':['headline'],'additionalProperties':False}
        with patch.object(self.client, '_request', return_value=response) as req:
            one = self.client.generate_brief({'name':'Kal'}, [], system_prompt='Use only facts.', schema=schema)
            two = self.client.generate_brief({'name':'Kal'}, [], system_prompt='Use only facts.', schema=schema)
        self.assertEqual(one, two)
        self.assertEqual(one['headline'], 'Founder')
        self.assertEqual(req.call_count, 1)
        payload = req.call_args.args[2]
        self.assertFalse(payload['stream'])
        self.assertEqual(payload['text']['format']['schema'], schema)

    def test_incomplete_brief_rejected(self):
        with patch.object(self.client, '_request', return_value={'status':'incomplete','output':[]}), self.assertRaises(KieError):
            self.client.generate_brief({}, [], system_prompt='facts', schema={'type':'object'})

    def test_finished_task_download_failure_can_resume_without_rebilling(self):
        with patch.object(self.client, '_request', side_effect=[
            {'code': 200, 'data': {'taskId': 't2'}},
            {'code': 200, 'data': {'state': 'success', 'resultJson': '{"resultUrls":["https://cdn.example/out.png"]}'}}
        ]), patch.object(self.client, '_download', side_effect=KieError('download failed')), self.assertRaises(KieError):
            self.client.generate_headshot('https://cdn.example/input.png', 'Keep face', self.root / 'out.png')
        with patch.object(self.client, '_request') as request, patch.object(self.client, '_download', return_value=PNG):
            self.client.generate_headshot('https://cdn.example/input.png', 'Keep face', self.root / 'out.png')
        request.assert_not_called()

    def test_transparency_is_only_valid_at_one_k(self):
        with patch.object(self.client, '_request') as request, self.assertRaises(ValueError):
            self.client.generate_headshot(self.source, 'face', self.root / 'out.png', background='transparent')
        request.assert_not_called()

    def test_missing_brief_fields_are_not_accepted_or_rebilled(self):
        schema = {'type': 'object', 'required': ['headline']}
        response = {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': '{}'}]}]}
        with patch.object(self.client, '_request', return_value=response), self.assertRaises(KieError):
            self.client.generate_brief({}, [], system_prompt='facts', schema=schema)
        with patch.object(self.client, '_request') as request, self.assertRaises(SubmissionUnknown):
            self.client.generate_brief({}, [], system_prompt='facts', schema=schema)
        request.assert_not_called()

    def test_download_recovers_through_official_temporary_link_without_auth_to_cdn(self):
        reply = MagicMock()
        reply.__enter__.return_value.read.return_value = PNG
        with patch('linkedin_pack.providers.kie.urlopen', side_effect=[URLError('reset'), reply]) as get, patch.object(
            self.client, '_request', return_value={'code': 200, 'data': 'https://storage.example/signed.png'}
        ) as request:
            data = self.client._download('https://tempfile.aiquickdraw.com/result.png')
        self.assertEqual(data, PNG)
        request.assert_called_once_with('POST', 'https://api.kie.ai/api/v1/common/download-url',
                                        {'url': 'https://tempfile.aiquickdraw.com/result.png'})
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.args[0].full_url, 'https://storage.example/signed.png')
        for call in get.call_args_list:
            self.assertNotIn('Authorization', dict(call.args[0].header_items()))

    def test_download_success_does_not_request_another_link(self):
        reply = MagicMock()
        reply.__enter__.return_value.read.return_value = PNG
        with patch('linkedin_pack.providers.kie.urlopen', return_value=reply), patch.object(self.client, '_request') as request:
            self.assertEqual(self.client._download('https://cdn.example/image.png'), PNG)
        request.assert_not_called()

    def test_download_recovery_is_bounded_and_rejects_malformed_link(self):
        with patch('linkedin_pack.providers.kie.urlopen', side_effect=URLError('reset')) as get, patch.object(
            self.client, '_request', return_value={'code': 200, 'data': {'unexpected': 'object'}}
        ) as request, self.assertRaises(KieError):
            self.client._download('https://cdn.example/image.png')
        self.assertEqual(get.call_count, 1)
        self.assertEqual(request.call_count, 1)


if __name__ == '__main__':
    unittest.main()
