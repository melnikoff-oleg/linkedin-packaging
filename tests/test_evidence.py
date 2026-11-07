import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from tests.test_core import brief
from linkedin_pack.evidence import (specificity_inventory, validate_specificity,
    collect_company_logos, enrich_brief_assets, copy_brief_logos)


def rich_profile():
    return {'url':'https://www.linkedin.com/in/example/', 'experience':[
        {'companyId':'123','companyName':'Factor75','position':'Chief Technology Officer',
         'companyLinkedinUrl':'https://www.linkedin.com/company/factor75/',
         'description':'Eliminated daily peak outages with an incremental rebuild, enabling ~7x scale in under nine months.',
         'endDate':{'text':'May 2021'},
         'companyLogo':{'url':'https://media.licdn.com/logo.png'}}]}


def specific_plan():
    plan=brief()
    plan['proof_points']=[]
    plan['banner_title']='~7× scale.\nNo full rewrite.'
    plan['headline']='Fractional CTO | Factor75: daily outages to ~7× scale in under nine months'
    plan['proof_cards']=[{'company_id':'123','company':'Factor75','role':'Former CTO',
        'value':'~7× scale','detail':'Daily peak outages eliminated; incremental rebuild.',
        'source':'https://www.linkedin.com/in/example/ · experience, Factor75'}]
    return plan


def png():
    out=io.BytesIO();Image.new('RGB',(50,30),'orange').save(out,format='PNG');return out.getvalue()


class EvidenceTests(unittest.TestCase):
    def test_inventory_keeps_company_metric_and_source_relationship_together(self):
        evidence=specificity_inventory(rich_profile())
        self.assertEqual(evidence[0]['company_id'],'123')
        self.assertEqual(evidence[0]['relationship'],'past role')
        self.assertIn('7x',evidence[0]['metric_tokens'])
        self.assertIn('experience[0]',evidence[0]['source'])

    def test_rich_source_rejects_generic_copy_even_when_it_mentions_tenure(self):
        plan=brief();plan['headline']='Fractional CTO | Align product and engineering | 25+ years'
        with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
            validate_specificity(plan,rich_profile())

    def test_exact_company_case_metric_passes(self):
        self.assertEqual(validate_specificity(specific_plan(),rich_profile())['status'],'passed')

    def test_number_from_different_company_cannot_substitute_for_support(self):
        plan=specific_plan();plan['proof_cards'][0]['value']='~99× scale'
        plan['headline']='Fractional CTO at Factor75';plan['banner_title']='~99× scale'
        with self.assertRaisesRegex(ValueError,'metric'):
            validate_specificity(plan,rich_profile())

    def test_source_distinctive_story_can_pass_without_a_number(self):
        profile=rich_profile();profile['experience'][0]['description']='Transformed a spreadsheet prototype into a profitable SaaS platform and supported acquisition.'
        plan=specific_plan();plan['proof_cards'][0]['value']='Spreadsheet prototype → SaaS'
        plan['proof_cards'][0]['detail']='Profitable platform, then acquisition.'
        plan['banner_title']='Spreadsheet to SaaS';plan['headline']='Fractional CTO | Factor75: spreadsheet prototype to profitable SaaS platform'
        self.assertEqual(validate_specificity(plan,profile)['status'],'passed')

    def test_source_without_case_evidence_allows_honest_modest_positioning(self):
        self.assertEqual(validate_specificity(brief(),{'about':'I advise founders.','experience':[]})['status'],'limited_source')

    def test_sparse_source_does_not_allow_fabricated_visible_metrics(self):
        plan=brief();plan['headline']='Fractional CTO | 99% revenue growth'
        with self.assertRaisesRegex(ValueError,'metric'):
            validate_specificity(plan,{'about':'I advise founders.','experience':[]})

    def test_sparse_company_source_does_not_allow_fabricated_card_metrics(self):
        profile=rich_profile();profile['experience'][0]['description']='Advised leadership teams.'
        plan=specific_plan();plan['headline']='Fractional CTO';plan['banner_title']='Technology leadership'
        plan['proof_cards'][0]['value']='99% revenue growth'
        with self.assertRaisesRegex(ValueError,'metric'):
            validate_specificity(plan,profile)

    def test_hidden_legacy_proof_cannot_validate_generic_visible_cards(self):
        for detail in ('Aligning product and engineering.',''):
            with self.subTest(detail=detail):
                plan=brief();plan['proof_cards']=[dict(specific_plan()['proof_cards'][0],value='Technology leadership',detail=detail)]
                plan['proof_points']=['Factor75: ~7× scale']
                with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
                    validate_specificity(plan,rich_profile())

    def test_legacy_hidden_proof_does_not_count_in_styles_that_hide_it(self):
        plan=brief();plan['proof_points']=['Factor75: ~7× scale']
        with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
            validate_specificity(plan,rich_profile())

    def test_explicit_empty_cards_never_validate_hidden_legacy_proof(self):
        for style in ('diandraescobar','charlie-hills'):
            with self.subTest(style=style):
                plan=brief();plan['selected_style']=style;plan['proof_cards']=[]
                plan['proof_points']=['Factor75: ~7× scale']
                with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
                    validate_specificity(plan,rich_profile())

    def test_modern_empty_card_matt_keeps_its_visible_subtitle_evidence(self):
        plan=brief();plan.update(selected_style='mattgray1',proof_cards=[],proof_points=[])
        plan['banner_subtitle']='Factor75: daily outages ended with an incremental rebuild.'
        self.assertEqual(validate_specificity(plan,rich_profile())['status'],'passed')

    def test_legacy_hidden_subtitle_does_not_count_in_matt_layout(self):
        plan=brief();plan['selected_style']='mattgray1'
        plan['banner_subtitle']='Factor75: ~7× scale'
        with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
            validate_specificity(plan,rich_profile())

    def test_company_in_another_field_does_not_validate_unrelated_case_metric(self):
        plan=brief();plan['proof_points']=[]
        plan['headline']='Fractional CTO | Former CTO at Factor75'
        plan['banner_title']='OtherCo: ~7× growth'
        with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
            validate_specificity(plan,rich_profile())

    def test_company_in_another_clause_does_not_validate_unrelated_case_metric(self):
        plan=brief();plan['proof_points']=[]
        plan['headline']='Former CTO at Factor75 | OtherCo: ~7× growth'
        with self.assertRaisesRegex(ValueError,'[Ss]pecific'):
            validate_specificity(plan,rich_profile())

    def test_specific_visible_case_can_support_nonmetric_named_card(self):
        plan=specific_plan();plan['proof_cards'][0]['value']='Named product award'
        plan['proof_cards'][0]['detail']='Industry award for a product.'
        self.assertEqual(validate_specificity(plan,rich_profile())['status'],'passed')

    def test_unknown_company_id_is_rejected_before_logo_network(self):
        plan=specific_plan();plan['proof_cards'][0]['company_id']='999'
        with tempfile.TemporaryDirectory() as tmp,patch('linkedin_pack.evidence._download_logo') as download:
            with self.assertRaisesRegex(ValueError,'company_id'):
                enrich_brief_assets(plan,rich_profile(),Path(tmp))
        download.assert_not_called()

    def test_selected_logos_are_cached_portable_and_provenanced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch('linkedin_pack.evidence._download_logo',return_value=png()) as download:
                first=enrich_brief_assets(specific_plan(),rich_profile(),root/'first',cache_dir=root/'cache')
                second=enrich_brief_assets(specific_plan(),rich_profile(),root/'second',cache_dir=root/'cache')
            self.assertEqual(download.call_count,1)
            self.assertEqual(first['logo_assets'],{'123':'logos/123.png'})
            self.assertEqual(second['logo_assets'],first['logo_assets'])
            self.assertTrue((root/'first/logos/123.png').is_file())
            provenance=json.loads((root/'first/logos/provenance.json').read_text())
            self.assertEqual(provenance['123']['company'],'Factor75')
            self.assertEqual(provenance['123']['relationship'],'past role')

    def test_offline_copy_rejects_traversal_and_copies_relative_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir();(source/'logos').mkdir()
            (source/'logos/123.png').write_bytes(png())
            plan=specific_plan();plan['logo_assets']={'123':'logos/123.png'}
            copy_brief_logos(plan,source,root/'out')
            self.assertTrue((root/'out/logos/123.png').is_file())
            plan['logo_assets']={'123':'../../secret.png'}
            with self.assertRaises(ValueError):copy_brief_logos(plan,source,root/'bad')

    def test_logo_url_cannot_target_local_network(self):
        from linkedin_pack.evidence import _logo_url
        for url in ('http://media.licdn.com/a.png','https://localhost/a.png','https://127.0.0.1/a.png','https://user:pass@media.licdn.com/a.png'):
            with self.assertRaises(ValueError):_logo_url(url)

    def test_only_selected_companies_are_fetched(self):
        profile=rich_profile();profile['experience'].append({'companyId':'456','companyName':'Other','companyLogo':{'url':'https://media.licdn.com/other.png'}})
        with tempfile.TemporaryDirectory() as tmp,patch('linkedin_pack.evidence._download_logo',return_value=png()) as download:
            collect_company_logos(profile,['123'],Path(tmp))
        self.assertEqual(download.call_count,1)

    def test_parent_company_logo_is_not_relabelled_as_product(self):
        profile=rich_profile();profile['experience'][0]['companyName']='Parent Group'
        profile['experience'][0]['position']='CTO of Factor75'
        with self.assertRaisesRegex(ValueError,'Logo company label'):
            validate_specificity(specific_plan(),profile)
        plan=specific_plan();plan['proof_cards'][0]['company_id']=''
        self.assertEqual(validate_specificity(plan,profile)['status'],'passed')
        with tempfile.TemporaryDirectory() as tmp,patch('linkedin_pack.evidence._download_logo') as download:
            result=enrich_brief_assets(plan,profile,Path(tmp))
        self.assertEqual(result['logo_assets'],{});download.assert_not_called()

    def test_supplemental_quoted_case_retains_its_company_and_source(self):
        plan=specific_plan();plan['proof_cards'][0]['value']='5 min → <5 sec'
        plan['proof_cards'][0]['source']='https://example.com/case · Factor75'
        plan['banner_title']='Quotes in <5 sec';plan['headline']='Fractional CTO | Factor75: quotes in <5 sec'
        supplements=[{'company_id':'123','company':'Factor75','role':'CTO','description':'Factor75 replaced a 5 minute quote process with quotes in <5 seconds.','source':'https://example.com/case'}]
        self.assertEqual(validate_specificity(plan,rich_profile(),supplemental_evidence=supplements)['status'],'passed')
        supplements[0]['company']='Other'
        with self.assertRaises(ValueError):validate_specificity(plan,rich_profile(),supplemental_evidence=supplements)

    def test_website_metric_is_scoped_to_named_section_not_another_case(self):
        plan=specific_plan();plan['proof_cards'][0]['value']='30% more releases'
        plan['proof_cards'][0]['source']='https://example.com · Factor75'
        plan['banner_title']='30% more releases';plan['headline']='Fractional CTO | Factor75: 30% more releases'
        website={'source_url':'https://example.com','markdown':'## Factor75\n30% more releases after reorganizing work.\n## Other\n99% more releases.'}
        self.assertEqual(validate_specificity(plan,rich_profile(),website=website)['status'],'passed')
        website['markdown']='## Factor75\nAn incremental rebuild eliminated outages.\n## Other\n30% more releases.'
        with self.assertRaises(ValueError):validate_specificity(plan,rich_profile(),website=website)

