"""Blind review must see only finished profile pixels and a buyer persona."""
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from linkedin_pack.providers.kie import KieClient, KieError, SubmissionUnknown
from linkedin_pack.review import review_package, review_is_current, review_passed, PACKAGE_FILES


def response(verdict='accept', concerns=None, *, interchangeability='specific', distinctive_details=None,
             brand_independent_clarity='clear', plain_language_takeaway=None):
    result={'verdict':verdict,'immediate_reaction':'Clear and approachable.',
            'perceived_offer':'Technology leadership for growing businesses.',
            'credibility_concerns':[], 'visual_concerns':concerns or [],
            'recommended_changes':[], 'interchangeability':interchangeability,
            'distinctive_details':(['At ExampleCo, replaced a third-party quote engine and cut quotes below five seconds.']
                                   if distinctive_details is None else distinctive_details),
            'memorability':'The leader who replaced ExampleCo’s slow quote engine.',
            'brand_independent_clarity':brand_independent_clarity,
            'plain_language_takeaway':('He speeds up slow customer pricing systems so people can buy faster.'
                                      if plain_language_takeaway is None else plain_language_takeaway)}
    return {'status':'completed','id':'r1','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(result)}]}]}


class BlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.output=self.root/'package';self.output.mkdir()
        Image.new('RGB',(792,500),'#efe9db').save(self.output/'review-desktop.png')
        Image.new('RGB',(390,600),'#e0e8ee').save(self.output/'review-mobile.png')
        for name in ('banner.png','portrait.png','headline.txt'):
            (self.output/name).write_bytes(b'fixture')
        self.bind_render()
        self.client=KieClient('test-review-key',self.root/'cache')
        self.persona='A founder of a growing B2B software company considering a fractional CTO.'

    def bind_render(self):
        hashes={name:hashlib.sha256((self.output/name).read_bytes()).hexdigest() for name in PACKAGE_FILES}
        (self.output/'qa.json').write_text(json.dumps({'passed':True,'render_sha256':hashes}))

    def test_deliverable_edit_requires_rerender_before_review(self):
        with patch.object(self.client,'_request',return_value=response()):
            review_package(self.output,self.persona,self.client)
        (self.output/'portrait.png').write_bytes(b'changed')
        self.assertFalse(review_passed(self.output,self.persona))
        with patch.object(self.client,'_request') as request,self.assertRaises(ValueError):
            review_package(self.output,self.persona,self.client)
        request.assert_not_called()

    def test_request_contains_only_persona_and_two_neutral_images(self):
        for filename in ['brief.json','portrait-prompt.txt','evidence-ledger.json','logo-provenance.json']:
            (self.output/filename).write_text('DO_NOT_SEND_PROCESS_SENTINEL')
        with patch.object(self.client,'_request',return_value=response()) as req:
            report=review_package(self.output,self.persona,self.client)
        payload=req.call_args.args[2]
        self.assertNotIn('DO_NOT_SEND_PROCESS_SENTINEL',json.dumps(payload))
        self.assertNotIn(str(self.output),json.dumps(payload))
        content=payload['input'][1]['content']
        self.assertEqual([item['type'] for item in content],['input_text','input_image','input_image'])
        self.assertTrue(all(item['image_url'].startswith('data:image/png;base64,') for item in content[1:]))
        self.assertEqual(report['verdict'],'accept')
        self.assertTrue(review_passed(self.output,self.persona))

    def test_unchanged_review_reuses_paid_result(self):
        with patch.object(self.client,'_request',return_value=response()) as req:
            first=review_package(self.output,self.persona,self.client)
            second=review_package(self.output,self.persona,self.client)
        self.assertEqual(req.call_count,1)
        self.assertEqual(first['image_sha256'],second['image_sha256'])

    def test_changed_pixels_invalidate_approval_and_receive_new_review(self):
        with patch.object(self.client,'_request',return_value=response()):
            review_package(self.output,self.persona,self.client)
        Image.new('RGB',(390,600),'#662244').save(self.output/'review-mobile.png')
        self.assertFalse(review_is_current(self.output,self.persona))
        self.assertFalse(review_passed(self.output,self.persona))
        self.bind_render()
        with patch.object(self.client,'_request',return_value=response('revise',['The message is hard to read.'])) as req:
            result=review_package(self.output,self.persona,self.client)
        self.assertEqual(req.call_count,1)
        self.assertEqual(result['verdict'],'revise')
        self.assertFalse(review_passed(self.output,self.persona))

    def test_missing_neutral_image_fails_before_network(self):
        (self.output/'review-mobile.png').unlink()
        with patch.object(self.client,'_request') as req,self.assertRaises(ValueError):
            review_package(self.output,self.persona,self.client)
        req.assert_not_called()

    def test_ambiguous_request_is_not_automatically_rebilled(self):
        with patch.object(self.client,'_request',side_effect=TimeoutError),self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        with patch.object(self.client,'_request') as req,self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        req.assert_not_called()
        self.assertFalse(review_passed(self.output,self.persona))

    def test_incomplete_or_malformed_review_does_not_approve(self):
        with patch.object(self.client,'_request',return_value={'status':'completed','output':[]}),self.assertRaises(KieError):
            review_package(self.output,self.persona,self.client)
        self.assertFalse(review_passed(self.output,self.persona))

    def test_malformed_completed_response_retains_recovery_metadata(self):
        reply={'status':'completed','id':'resp_recoverable','code':200,'output':[],
               'usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30,
                        'output_tokens_details':{'reasoning_tokens':7},
                        'unexpected_text':'PRIVATE_PROVIDER_TEXT'},
               'credits_consumed':0.03,'msg':'PRIVATE_PROVIDER_TEXT'}
        with patch.object(self.client,'_request',return_value=reply),self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        record=json.loads(next(self.client.cache_dir.glob('*.json')).read_text())
        self.assertEqual(record['state'],'submission_unknown')
        self.assertEqual(record['response_id'],'resp_recoverable')
        self.assertEqual(record['response_status'],'completed')
        self.assertEqual(record['response_code'],200)
        self.assertEqual(record['usage']['total_tokens'],30)
        self.assertEqual(record['usage']['output_tokens_details']['reasoning_tokens'],7)
        self.assertEqual(record['credits_consumed'],0.03)
        self.assertEqual(record['error_type'],'JSONDecodeError')
        self.assertEqual(record['error_reason'],'Response received; review result could not be validated.')
        self.assertNotIn('PRIVATE_PROVIDER_TEXT',json.dumps(record))
        self.assertFalse(review_passed(self.output,self.persona))

    def test_connection_failure_retains_type_without_exception_text(self):
        with patch.object(self.client,'_request',side_effect=TimeoutError('PRIVATE_REQUEST_TEXT')),self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        record=json.loads(next(self.client.cache_dir.glob('*.json')).read_text())
        self.assertEqual(record['state'],'submission_unknown')
        self.assertEqual(record['error_type'],'TimeoutError')
        self.assertEqual(record['error_reason'],'Request did not return a response; provider outcome is unknown.')
        self.assertNotIn('PRIVATE_REQUEST_TEXT',json.dumps(record))
        with patch.object(self.client,'_request') as req,self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        req.assert_not_called()

    def test_image_change_during_request_cannot_receive_fresh_approval(self):
        def mutate(*args):
            Image.new('RGB',(390,600),'black').save(self.output/'review-mobile.png')
            return response()
        with patch.object(self.client,'_request',side_effect=mutate),self.assertRaises(KieError):
            review_package(self.output,self.persona,self.client)
        self.assertFalse(review_passed(self.output,self.persona))

    def test_concerns_prevent_ready_even_if_model_says_accept(self):
        with patch.object(self.client,'_request',return_value=response('accept',['An image looks unnatural.'])):
            review_package(self.output,self.persona,self.client)
        self.assertFalse(review_passed(self.output,self.persona))

    def test_interchangeable_profile_cannot_pass_even_with_accept_verdict(self):
        with patch.object(self.client,'_request',return_value=response(interchangeability='interchangeable')):
            report=review_package(self.output,self.persona,self.client)
        self.assertEqual(report['verdict'],'accept')
        self.assertFalse(review_passed(self.output,self.persona))

    def test_no_distinctive_details_cannot_pass_even_with_specific_verdict(self):
        with patch.object(self.client,'_request',return_value=response(distinctive_details=[])):
            review_package(self.output,self.persona,self.client)
        self.assertFalse(review_passed(self.output,self.persona))

    def test_specific_but_brand_dependent_profile_cannot_pass_accept_verdict(self):
        with patch.object(self.client,'_request',return_value=response(brand_independent_clarity='unclear')):
            report=review_package(self.output,self.persona,self.client)
        self.assertEqual(report['verdict'],'accept')
        self.assertFalse(review_passed(self.output,self.persona))

    def test_empty_plain_language_takeaway_cannot_approve(self):
        with patch.object(self.client,'_request',return_value=response(plain_language_takeaway='')),self.assertRaises(SubmissionUnknown):
            review_package(self.output,self.persona,self.client)
        self.assertFalse(review_passed(self.output,self.persona))

    def test_previous_review_without_brand_clarity_is_not_current(self):
        with patch.object(self.client,'_request',return_value=response()):
            review_package(self.output,self.persona,self.client)
        path=self.output/'blind-review.json';report=json.loads(path.read_text())
        del report['brand_independent_clarity'];del report['plain_language_takeaway']
        path.write_text(json.dumps(report))
        self.assertFalse(review_is_current(self.output,self.persona))
        self.assertFalse(review_passed(self.output,self.persona))

    def test_distinctive_qualitative_story_does_not_require_invented_numbers(self):
        detail='At HelloFresh, founded HelloMint: a team mentoring idea that became an executive-sponsored global program.'
        with patch.object(self.client,'_request',return_value=response(distinctive_details=[detail])):
            report=review_package(self.output,self.persona,self.client)
        self.assertEqual(report['distinctive_details'],[detail])
        self.assertTrue(review_passed(self.output,self.persona))

    def test_previous_review_schema_is_not_current_or_accepted(self):
        with patch.object(self.client,'_request',return_value=response()):
            review_package(self.output,self.persona,self.client)
        path=self.output/'blind-review.json';report=json.loads(path.read_text())
        for key in ('interchangeability','distinctive_details','memorability'):
            del report[key]
        path.write_text(json.dumps(report))
        self.assertFalse(review_is_current(self.output,self.persona))
        self.assertFalse(review_passed(self.output,self.persona))

    def test_incomplete_saved_record_cannot_count_as_approval(self):
        with patch.object(self.client,'_request',return_value=response()):
            review_package(self.output,self.persona,self.client)
        path=self.output/'blind-review.json';report=json.loads(path.read_text())
        del report['visual_concerns'];path.write_text(json.dumps(report))
        self.assertFalse(review_passed(self.output,self.persona))
