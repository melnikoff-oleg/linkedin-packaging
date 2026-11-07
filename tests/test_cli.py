"""CLI flow tests use local fixtures and mock the paid providers/browser renderer."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from linkedin_pack.cli import main, website_palette, contrast_ratio
from tests.test_core import brief
from tests.test_visual_assets import patterned_photo
from linkedin_pack import cli


class CliTests(unittest.TestCase):
    def test_source_context_retains_older_named_case_evidence_and_company_ids(self):
        profile={'url':'https://www.linkedin.com/in/example/', 'experience':[
            {'companyName':f'Company {i}','companyId':str(i),'description':'Earlier role'} for i in range(20)]}
        profile['experience'][19]['description']='Reduced quote times to <5 seconds.'
        result=cli._profile_context(profile)
        self.assertEqual(len(result['experience']),20)
        self.assertEqual(result['experience'][19]['companyId'],'19')
        self.assertIn('5s',result['specific_case_evidence'][19]['metric_tokens'])

    def test_create_rejects_generic_brief_when_source_has_specific_case_before_paid_images(self):
        from tests.test_evidence import rich_profile
        source=self.out/'source';source.mkdir(parents=True)
        (source/'profile.json').write_text(json.dumps(rich_profile()))
        with patch('linkedin_pack.cli.load_keys',return_value={}),patch('linkedin_pack.cli.KieClient') as kie,patch('linkedin_pack.cli.render_package') as render:
            code=self.run_cli(['create','--linkedin','https://www.linkedin.com/in/example/',
                               '--brief',str(self.plan),'--reuse-portrait',str(self.portrait),'--output',str(self.out)])
        self.assertEqual(code,2);kie.assert_not_called();render.assert_not_called()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = self.root / 'plan.json'
        self.plan.write_text(json.dumps(brief()))
        self.portrait = self.root / 'portrait.png'
        self.portrait.write_bytes(b'portrait')
        self.out = self.root / 'result'
        # These tests isolate generation/rendering from the separately tested paid review.
        review_patch=patch('linkedin_pack.cli._run_independent_review',return_value=True)
        self.review=review_patch.start();self.addCleanup(review_patch.stop)

    def run_cli(self, args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(args)

    def test_offline_render_needs_no_keys_or_network(self):
        with patch('linkedin_pack.cli.render_package', return_value={'passed': True}) as render, patch('linkedin_pack.cli.load_keys') as keys:
            code = self.run_cli(['render', '--brief', str(self.plan), '--portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 0)
        keys.assert_not_called()
        self.review.assert_not_called()
        self.assertEqual(render.call_args.args[0]['headline'], brief()['headline'])

    def test_render_qa_failure_is_not_reported_as_success(self):
        with patch('linkedin_pack.cli.render_package', return_value={'passed': False, 'failures': ['Text overflow']}):
            code = self.run_cli(['render', '--brief', str(self.plan), '--portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 2)

    def test_create_reuses_local_source_and_prepared_assets_without_paid_generation(self):
        source = self.out / 'source'
        source.mkdir(parents=True)
        (source / 'profile.json').write_text(json.dumps({'url': 'https://www.linkedin.com/in/example/', 'name': 'Test Person', 'location': 'Somewhere'}))
        with patch('linkedin_pack.cli.load_keys', return_value={}), patch('linkedin_pack.cli.KieClient') as kie, patch('linkedin_pack.cli.ApifyClient') as apify, patch('linkedin_pack.cli.render_package', return_value={'passed': True}):
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--brief', str(self.plan), '--reuse-portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 0)
        kie.assert_not_called()
        apify.assert_not_called()

    def test_create_returns_failure_when_independent_review_declines(self):
        source=self.out/'source';source.mkdir(parents=True)
        (source/'profile.json').write_text(json.dumps({'url':'https://www.linkedin.com/in/example/','name':'Test Person'}))
        self.review.return_value=False
        with patch('linkedin_pack.cli.load_keys',return_value={}),patch('linkedin_pack.cli.KieClient') as kie,patch('linkedin_pack.cli.render_package',return_value={'passed':True}):
            code=self.run_cli(['create','--linkedin','https://www.linkedin.com/in/example/',
                               '--brief',str(self.plan),'--reuse-portrait',str(self.portrait),'--output',str(self.out)])
        self.assertEqual(code,2)
        kie.assert_not_called()
        self.assertEqual(json.loads((self.out/'run.json').read_text())['packages'][0]['acceptance'],'needs_revision')

    def test_create_does_not_pay_for_review_when_technical_checks_fail(self):
        source=self.out/'source';source.mkdir(parents=True)
        (source/'profile.json').write_text(json.dumps({'url':'https://www.linkedin.com/in/example/','name':'Test Person'}))
        with patch('linkedin_pack.cli.load_keys',return_value={}),patch('linkedin_pack.cli.render_package',return_value={'passed':False,'failures':['Overlap']}):
            code=self.run_cli(['create','--linkedin','https://www.linkedin.com/in/example/',
                               '--brief',str(self.plan),'--reuse-portrait',str(self.portrait),'--output',str(self.out)])
        self.assertEqual(code,2);self.review.assert_not_called()

    def test_invalid_brief_rejected_before_paid_portrait_call(self):
        bad = brief()
        bad['headline'] = 'x' * 221
        self.plan.write_text(json.dumps(bad))
        with patch('linkedin_pack.cli.KieClient') as kie:
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--brief', str(self.plan), '--portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 2)
        kie.assert_not_called()

    def test_explicit_website_failure_stops_instead_of_inventing_context(self):
        source = self.out / 'source'
        source.mkdir(parents=True)
        (source / 'profile.json').write_text(json.dumps({'url': 'https://www.linkedin.com/in/example/', 'name': 'Test Person'}))
        with patch('linkedin_pack.cli.load_keys', return_value={'FIRECRAWL_API_KEY': 'fixture'}), patch('linkedin_pack.cli.scrape_website', side_effect=RuntimeError('Website unavailable')), patch('linkedin_pack.cli.KieClient') as kie:
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--website', 'https://example.com', '--brief', str(self.plan), '--reuse-portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 2)
        kie.assert_not_called()

    def test_wrong_profile_in_output_folder_is_not_overwritten(self):
        source = self.out / 'source'
        source.mkdir(parents=True)
        (source / 'profile.json').write_text(json.dumps({'url': 'https://www.linkedin.com/in/someone-else/'}))
        with patch('linkedin_pack.cli.load_keys', return_value={}), patch('linkedin_pack.cli.ApifyClient') as apify:
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--brief', str(self.plan), '--reuse-portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 2)
        apify.assert_not_called()

    def test_styles_is_available_without_credentials(self):
        with patch('linkedin_pack.cli.load_keys') as keys:
            code = self.run_cli(['styles'])
        self.assertEqual(code, 0)
        keys.assert_not_called()

    def test_missing_input_portrait_is_detected_before_scraping(self):
        with patch('linkedin_pack.cli.ApifyClient') as apify:
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--portrait', str(self.root / 'missing.png')])
        self.assertEqual(code, 2)
        apify.assert_not_called()

    def test_generated_brief_and_identity_rules_reach_render(self):
        source = self.out / 'source'
        source.mkdir(parents=True)
        (source / 'profile.json').write_text(json.dumps({'url': 'https://www.linkedin.com/in/example/', 'name': 'Test Person', 'portrait_file': 'portrait.png'}))
        (source / 'portrait.png').write_bytes(b'portrait')
        with patch('linkedin_pack.cli.load_keys', return_value={'KIE_AI_API_KEY': 'fixture'}), patch('linkedin_pack.cli.KieClient') as cls, patch('linkedin_pack.cli.render_package', return_value={'passed': True}) as render:
            client = cls.return_value
            generated=brief()
            generated.update(layout_mode='reference-faithful',proof_points=[],proof_cards=[],reference_content={
                'brand':'TP','brand_suffix':'studio','title':['Clarity for founders','and their next chapter'],
                'support':['Positioning purpose','A clear point of view'],
                'support_accent':'A clear point of view','relationship':'','logos':['','','']})
            client.generate_brief.return_value = generated
            client.generate_headshot.return_value = self.portrait
            code = self.run_cli(['create', '--linkedin', 'https://www.linkedin.com/in/example/', '--style', 'clarekitching', '--output', str(self.out)])
        self.assertEqual(code, 0)
        self.assertIn('same person', client.generate_headshot.call_args.args[1])
        self.assertNotIn('Kal', client.generate_headshot.call_args.args[1])
        self.assertEqual(render.call_args.args[0]['selected_style'], 'clarekitching')
        self.assertEqual(render.call_args.args[0]['layout_mode'], 'reference-faithful')
        self.assertEqual(client.generate_brief.call_count,1)
        self.assertEqual(self.review.call_args.args[:2],(self.out,brief()['audience']))

    def test_brand_palette_uses_real_colors_and_repairs_unreadable_text(self):
        website = {'source_url': 'https://example.com', 'branding': {'colors': {
            'background': '#fff', 'textPrimary': '#eeeeee', 'primary': '#0000bb', 'accent': 'url(bad)'}}}
        palette, provenance = website_palette(website)
        self.assertEqual(palette['bg'], '#ffffff')
        self.assertEqual(palette['accent'], '#0000bb')
        self.assertGreaterEqual(contrast_ratio(palette['fg'], palette['bg']), 4.5)
        self.assertEqual(provenance['source_url'], 'https://example.com')
        self.assertNotIn('url(bad)', json.dumps(palette))

    def test_brand_palette_rejects_missing_valid_colors(self):
        with self.assertRaises(ValueError):
            website_palette({'branding': {'colors': {'primary': 'red;display:none'}}})

    def test_context_only_intake_uses_no_scraper_or_paid_calls_with_prepared_assets(self):
        with patch('linkedin_pack.cli.load_keys', return_value={}), patch('linkedin_pack.cli.ApifyClient') as apify, patch('linkedin_pack.cli.KieClient') as kie, patch('linkedin_pack.cli.render_package', return_value={'passed': True}):
            code = self.run_cli(['create', '--name', 'Test Person', '--context', 'I help founders clarify their message.',
                                 '--brief', str(self.plan), '--reuse-portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 0)
        apify.assert_not_called()
        kie.assert_not_called()
        saved = json.loads((self.out / 'source' / 'profile.json').read_text())
        self.assertEqual(saved['url'], 'user-provided context')
        self.assertEqual(saved['name'], 'Test Person')
        self.assertEqual(saved['experience'], [])

    def test_context_only_intake_rejects_missing_name_context_or_photo_before_network(self):
        combinations = [[], ['--name', 'Test'], ['--name', 'Test', '--context', 'Facts'],
                        ['--context', 'Facts', '--portrait', str(self.portrait)],
                        ['--name', 'Test', '--portrait', str(self.portrait)]]
        for args in combinations:
            with self.subTest(args=args), patch('linkedin_pack.cli.ApifyClient') as apify, patch('linkedin_pack.cli.KieClient') as kie:
                code = self.run_cli(['create'] + args)
            self.assertEqual(code, 2)
            apify.assert_not_called()
            kie.assert_not_called()

    def test_context_only_intake_refuses_another_person_existing_folder(self):
        source = self.out / 'source'
        source.mkdir(parents=True)
        (source / 'profile.json').write_text(json.dumps({'url': 'user-provided context', 'name': 'Other Person', 'about': 'Other facts'}))
        with patch('linkedin_pack.cli.ApifyClient') as apify, patch('linkedin_pack.cli.KieClient') as kie:
            code = self.run_cli(['create', '--name', 'Test Person', '--context', 'Facts', '--portrait', str(self.portrait), '--output', str(self.out)])
        self.assertEqual(code, 2)
        apify.assert_not_called()
        kie.assert_not_called()

    def test_same_supplied_avatar_and_banner_fail_before_any_paid_calls(self):
        with patch('linkedin_pack.cli.ApifyClient') as apify, patch('linkedin_pack.cli.KieClient') as kie:
            code=self.run_cli(['create','--linkedin','https://www.linkedin.com/in/example/',
                               '--reuse-portrait',str(self.portrait),'--banner-photo',str(self.portrait),
                               '--style','laraacostar','--output',str(self.out)])
        self.assertEqual(code,2)
        apify.assert_not_called();kie.assert_not_called()

    def test_banner_photo_is_separate_argument_in_offline_render(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        patterned_photo(self.portrait)
        banner=self.root/'banner-photo.png';patterned_photo(banner,alternate=True,transparent=True)
        with patch('linkedin_pack.cli.render_package',return_value={'passed':True}) as render:
            code=self.run_cli(['render','--brief',str(self.plan),'--portrait',str(self.portrait),
                               '--banner-photo',str(banner),'--output',str(self.out)])
        self.assertEqual(code,0)
        self.assertEqual(render.call_args.kwargs['banner_photo_path'],banner)

    def test_missing_separate_banner_in_offline_render_fails(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        with patch('linkedin_pack.cli.render_package') as render:
            code=self.run_cli(['render','--brief',str(self.plan),'--portrait',str(self.portrait),'--output',str(self.out)])
        self.assertEqual(code,2);render.assert_not_called()

    def test_create_uses_independent_photo_task_for_banner(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        patterned_photo(self.portrait)
        banner=self.root/'banner-photo.png';patterned_photo(banner,alternate=True)
        cutout=self.root/'banner-cutout.png';patterned_photo(cutout,alternate=True,transparent=True)
        source=self.out/'source';source.mkdir(parents=True)
        (source/'profile.json').write_text(json.dumps({'url':'https://www.linkedin.com/in/example/', 'name':'Test Person','portrait_file':'portrait.png'}))
        (source/'portrait.png').write_bytes(self.portrait.read_bytes())
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}), patch('linkedin_pack.cli.KieClient') as kie, patch('linkedin_pack.cli.render_package',return_value={'passed':True}) as render:
            kie.return_value.generate_headshot.side_effect=[self.portrait,banner,cutout]
            code=self.run_cli(['create','--linkedin','https://www.linkedin.com/in/example/',
                               '--brief',str(self.plan),'--output',str(self.out)])
        self.assertEqual(code,0)
        calls=kie.return_value.generate_headshot.call_args_list
        self.assertEqual(len(calls),3)
        self.assertEqual(calls[1].kwargs['aspect_ratio'],'3:4')
        self.assertIn('distinct photograph',calls[1].args[1])
        self.assertNotIn('55-60%',calls[1].args[1])
        self.assertEqual(calls[2].args[0],banner)
        self.assertEqual(calls[2].kwargs['resolution'],'1K')
        self.assertEqual(calls[2].kwargs['background'],'transparent')
        self.assertEqual(render.call_args.kwargs['banner_photo_path'],cutout)
        record=json.loads((self.out/'visual-assets.json').read_text())
        self.assertEqual(record['combined_profile_review'],'required')

    def test_offline_render_refuses_opaque_banner_photo(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        patterned_photo(self.portrait)
        banner=self.root/'opaque.png';patterned_photo(banner,alternate=True)
        with patch('linkedin_pack.cli.render_package') as render,patch('linkedin_pack.cli.KieClient') as kie:
            code=self.run_cli(['render','--brief',str(self.plan),'--portrait',str(self.portrait),
                               '--banner-photo',str(banner),'--output',str(self.out)])
        self.assertEqual(code,2);render.assert_not_called();kie.assert_not_called()

    def test_existing_cutout_and_avatar_skip_paid_image_edits(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        patterned_photo(self.portrait)
        banner=self.root/'cutout.png';patterned_photo(banner,alternate=True,transparent=True)
        with patch('linkedin_pack.cli.load_keys',return_value={}),patch('linkedin_pack.cli.KieClient') as kie,patch('linkedin_pack.cli.render_package',return_value={'passed':True}):
            code=self.run_cli(['create','--name','Test Person','--context','I help founders.',
                               '--brief',str(self.plan),'--reuse-portrait',str(self.portrait),
                               '--banner-photo',str(banner),'--output',str(self.out)])
        self.assertEqual(code,0);kie.assert_not_called()

    def test_failed_transparency_never_reaches_render_or_review(self):
        plan=brief();plan['selected_style']='laraacostar';self.plan.write_text(json.dumps(plan))
        patterned_photo(self.portrait)
        banner=self.root/'opaque.png';patterned_photo(banner,alternate=True)
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}),patch('linkedin_pack.cli.KieClient') as kie,patch('linkedin_pack.cli.render_package') as render:
            kie.return_value.generate_headshot.return_value=banner
            code=self.run_cli(['create','--name','Test Person','--context','I help founders.',
                               '--brief',str(self.plan),'--reuse-portrait',str(self.portrait),
                               '--banner-photo',str(banner),'--output',str(self.out)])
        self.assertEqual(code,2);render.assert_not_called();self.review.assert_not_called()
        self.assertEqual(kie.return_value.generate_headshot.call_count,1)


class ReviewCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)
        (self.output/'qa.json').write_text(json.dumps({'passed':True,'failures':[]}))
        self.persona='A founder buying fractional technology leadership.'
        self.accept={'verdict':'accept','immediate_reaction':'Clear and credible.','visual_concerns':[],
                     'credibility_concerns':[],'recommended_changes':[]}

    def run_cli(self,args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return main(args)

    def test_review_command_approves_only_current_images(self):
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}),patch('linkedin_pack.cli.KieClient'),patch('linkedin_pack.cli.review_package',return_value=self.accept) as review,patch('linkedin_pack.cli.review_passed',return_value=True):
            code=self.run_cli(['review','--output',str(self.output),'--audience',self.persona])
        self.assertEqual(code,0)
        self.assertEqual(review.call_args.args[:2],(self.output,self.persona))
        qa=json.loads((self.output/'qa.json').read_text())
        self.assertEqual(qa['acceptance'],'ready')
        self.assertEqual(qa['visual_review'],'passed')

    def test_revise_verdict_stops_without_regenerating(self):
        result={**self.accept,'verdict':'revise','visual_concerns':['The two portraits feel like a repeated pose.'],
                'recommended_changes':['Use a distinct environmental frame.']}
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}),patch('linkedin_pack.cli.KieClient') as client,patch('linkedin_pack.cli.review_package',return_value=result),patch('linkedin_pack.cli.review_passed',return_value=False):
            code=self.run_cli(['review','--output',str(self.output),'--audience',self.persona])
        self.assertEqual(code,2)
        client.return_value.generate_headshot.assert_not_called()
        self.assertEqual(json.loads((self.output/'qa.json').read_text())['acceptance'],'needs_revision')

    def test_stale_positive_review_cannot_mark_ready(self):
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}),patch('linkedin_pack.cli.KieClient'),patch('linkedin_pack.cli.review_package',return_value=self.accept),patch('linkedin_pack.cli.review_passed',return_value=False):
            code=self.run_cli(['review','--output',str(self.output),'--audience',self.persona])
        self.assertEqual(code,2)
        self.assertNotEqual(json.loads((self.output/'qa.json').read_text())['acceptance'],'ready')

    def test_failed_technical_checks_stop_before_paid_review(self):
        (self.output/'qa.json').write_text(json.dumps({'passed':False,'failures':['Overlap']}))
        with patch('linkedin_pack.cli.KieClient') as client,patch('linkedin_pack.cli.review_package') as review:
            code=self.run_cli(['review','--output',str(self.output),'--audience',self.persona])
        self.assertEqual(code,2)
        client.assert_not_called();review.assert_not_called()

    def test_review_connection_failure_invalidates_prior_ready_status(self):
        (self.output/'qa.json').write_text(json.dumps({'passed':True,'acceptance':'ready'}))
        with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture'}),patch('linkedin_pack.cli.KieClient'),patch('linkedin_pack.cli.review_package',side_effect=RuntimeError('review unavailable')):
            code=self.run_cli(['review','--output',str(self.output),'--audience',self.persona])
        self.assertEqual(code,2)
        self.assertEqual(json.loads((self.output/'qa.json').read_text())['acceptance'],'review_failed')


if __name__ == '__main__':
    unittest.main()
