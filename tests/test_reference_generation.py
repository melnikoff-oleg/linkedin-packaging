"""Reference-slot generation must preserve geometry without borrowing fixture facts."""
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from tests.test_core import brief
from tests.test_evidence import rich_profile
from linkedin_pack import cli, core, evidence


def refplan(style='adrian-kul'):
    from linkedin_pack.reference_layout import registry
    p=brief();p.update(selected_style=style,layout_mode='reference-faithful',proof_points=[],proof_cards=[],
                      reference_content=copy.deepcopy(registry()[style][1]))
    if style=='adrian-kul':p['reference_content']={'brand':'TP','title':'A technology partner for growing teams'}
    return p


def alpha_png():
    img=Image.new('RGBA',(50,30),(0,0,0,0))
    for x in range(5,45):
        for y in range(8,22):img.putpixel((x,y),(0,0,0,255))
    out=io.BytesIO();img.save(out,format='PNG');return out.getvalue()


class ReferenceGenerationTests(unittest.TestCase):
    def test_schema_has_exact_slots_but_no_kal_identity_or_fixture_claims(self):
        schema=core.reference_brief_schema('laraacostar')
        self.assertEqual(schema['properties']['layout_mode']['enum'],['reference-faithful'])
        title=schema['properties']['reference_content']['properties']['title']
        self.assertEqual(title['minItems'],2);self.assertEqual(title['maxItems'],2)
        text=json.dumps(schema)
        for forbidden in ('Kal','Factor','ForeverCar','Double Good','7×'):
            self.assertNotIn(forbidden,text)
        self.assertEqual(schema['properties']['proof_cards']['maxItems'],0)

    def test_validation_rejects_reference_missing_slots_before_generation(self):
        p=refplan();del p['reference_content']
        with self.assertRaisesRegex(ValueError,'slots|reference_content'):
            core.validate_brief(p)

    def test_reference_visible_metrics_cannot_hide_outside_old_banner_fields(self):
        p=refplan('diandraescobar');p['headline']='Technology leader';p['banner_title']='Technology leader'
        p['reference_content']['cards'][0]['text']='Revenue grew 99%.'
        with self.assertRaisesRegex(ValueError,'metric'):
            evidence.validate_specificity(p,rich_profile())

    def test_reference_company_card_metrics_are_scoped_to_named_company(self):
        p=refplan('diandraescobar');p['headline']='Technology leader';p['banner_title']='Technology leader'
        p['reference_content']['title']=['Your','Technology','Partner']
        p['reference_content']['cards']=[{'company':'Other','role':'Former CTO','text':'~7× scale.'} for _ in range(5)]
        profile=rich_profile();profile['experience'].append({'companyName':'Other','companyId':'456','description':'Advised teams.'})
        with self.assertRaisesRegex(ValueError,'company source'):
            evidence.validate_specificity(p,profile)

    def test_hidden_legacy_banner_does_not_validate_reference_visible_generic_copy(self):
        p=refplan();p['headline']='Technology leader';p['banner_title']='Factor75: ~7× scale'
        with self.assertRaisesRegex(ValueError,'discarded'):
            evidence.validate_specificity(p,rich_profile())

    def test_reference_logo_enrichment_uses_slots_even_without_proof_cards(self):
        p=refplan('clarekitching');p['headline']='Factor75: ~7× scale';p['reference_content']['title']=['Factor75: daily outages','ended with a rebuild']
        p['reference_content']['support']=['An incremental rebuild','and ~7× scale']
        p['reference_content']['logos']=['123','','']
        with tempfile.TemporaryDirectory() as tmp, patch('linkedin_pack.evidence._download_logo',return_value=alpha_png()) as download:
            out=evidence.enrich_brief_assets(p,rich_profile(),Path(tmp))
            self.assertEqual(out['logo_assets'],{'123':'logos/123.png'})
        self.assertEqual(download.call_count,1)

    def test_opaque_reference_logo_does_not_become_a_plate(self):
        p=refplan('clarekitching');p['headline']='Factor75: ~7× scale';p['reference_content']['title']=['Factor75: daily outages','ended with a rebuild'];p['reference_content']['support']=['An incremental rebuild','and ~7× scale'];p['reference_content']['logos']=['123','','']
        out=io.BytesIO();Image.new('RGB',(40,40),'white').save(out,format='PNG')
        with tempfile.TemporaryDirectory() as tmp,patch('linkedin_pack.evidence._download_logo',return_value=out.getvalue()):
            result=evidence.enrich_brief_assets(p,rich_profile(),Path(tmp))
        self.assertEqual(result['reference_content']['logos'],['','',''])
        self.assertEqual(result['logo_assets'],{})
        self.assertTrue(result['logo_preparation']['omitted'])

    def test_explicit_style_generation_requests_reference_schema_in_one_call(self):
        p=refplan()
        class Client:
            calls=[]
            def generate_brief(self,context,references,**kwargs):
                self.calls.append((context,kwargs));return copy.deepcopy(p)
        client=Client()
        plan=cli._generate_reference_plan(client,{'name':'Test Person'},'',[],requested_style='adrian-kul')
        self.assertEqual(plan['layout_mode'],'reference-faithful');self.assertEqual(len(client.calls),1)
        context,request=client.calls[0]
        self.assertIn('reference_content',request['schema']['properties'])
        self.assertNotIn('Kal Walkden',json.dumps(context))
        self.assertNotIn('48 design px',request['system_prompt'])

if __name__=='__main__':unittest.main()

class ReferenceBoundaryTests(unittest.TestCase):
    def test_alias_logo_requires_product_role_and_never_renames_parent(self):
        import hashlib
        p=refplan('charlie-hills');p['headline']='Factor75: ~7× scale'
        p['reference_content']['companies']=[{'key':'123','name':'Child','role':'Former CTO','color':'#123456'} for _ in range(4)]
        profile=rich_profile();profile['experience'][0]['position']='Chief Technology Officer of Child'
        with tempfile.TemporaryDirectory() as tmp,patch('linkedin_pack.evidence._download_logo') as download:
            with self.assertRaisesRegex(ValueError,'parent|Logo company label'):
                evidence._collect_reference_logos(p,profile,Path(tmp))
        download.assert_not_called()

    def test_sourced_product_logo_alias_is_available_and_copied_without_parent(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);curated=root/'cache/curated';curated.mkdir(parents=True)
            raw=alpha_png();(curated/'product.png').write_bytes(raw)
            record={'company_id':'','company':'Product','profile_company_name':'Product','source_type':'official-brand-asset',
                    'source_url':'https://product.example/logo.png','source_page':'https://product.example/',
                    'sha256':hashlib.sha256(raw).hexdigest(),'relationship':'past role'}
            (curated/'product.json').write_text(json.dumps(record))
            profile={'experience':[{'companyId':'parent','companyName':'Parent','position':'CTO (Product)','description':'Built software.'}]}
            choices=evidence.reference_logo_options(profile,root/'cache')
            self.assertEqual([item['key'] for item in choices],['product'])
            p=refplan('clarekitching');p['reference_content']['logos']=['product','','']
            with patch('linkedin_pack.evidence._download_logo') as download:
                assets=evidence._collect_reference_logos(p,profile,root/'out',root/'cache')
            self.assertEqual(assets,{'product':'logos/product.png'});download.assert_not_called()
            profile['experience'][0]['position']='CTO'
            self.assertEqual(evidence.reference_logo_options(profile,root/'cache'),[])

    def test_automatic_selection_fills_slots_after_selecting_style(self):
        p=refplan()
        class Client:
            calls=[]
            def generate_brief(self,context,references,**kwargs):
                self.calls.append((copy.deepcopy(context),kwargs))
                if len(self.calls)==1:
                    draft=brief();draft['selected_style']='adrian-kul';return draft
                return copy.deepcopy(p)
        client=Client();out=cli._generate_reference_plan(client,{'name':'Test Person'},'',[])
        self.assertEqual(len(client.calls),2);self.assertEqual(out['layout_mode'],'reference-faithful')
        self.assertEqual(client.calls[1][0]['requested_style'],'adrian-kul')
        self.assertIn('reference_content',client.calls[1][1]['schema']['properties'])

class ReferencePaletteTests(unittest.TestCase):
    def test_explicit_website_palette_rejected_before_any_network_or_generation(self):
        import contextlib
        with patch('linkedin_pack.cli.load_keys') as keys,patch('linkedin_pack.cli.KieClient') as client,patch('linkedin_pack.cli.scrape_website') as scrape,contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(['create','--linkedin','https://www.linkedin.com/in/example/','--style','adrian-kul',
                           '--website','https://example.com','--use-website-colors'])
        self.assertEqual(code,2);keys.assert_not_called();client.assert_not_called();scrape.assert_not_called()

    def test_website_content_does_not_implicitly_recolor_new_reference_package(self):
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir();portrait=root/'portrait.png';portrait.write_bytes(b'portrait')
            (source/'profile.json').write_text(json.dumps({'url':'https://www.linkedin.com/in/example/','name':'Test Person'}))
            website={'source_url':'https://example.com','markdown':'A technology advisor.','branding':{'colors':{'background':'#ff0000','primary':'#ffffff'}}}
            with patch('linkedin_pack.cli.load_keys',return_value={'KIE_AI_API_KEY':'fixture','FIRECRAWL_API_KEY':'fixture'}),patch('linkedin_pack.cli.scrape_website',return_value=website),patch('linkedin_pack.cli.website_palette') as palette,patch('linkedin_pack.cli.KieClient') as client,patch('linkedin_pack.cli.render_package',return_value={'passed':True}) as render,patch('linkedin_pack.cli._run_independent_review',return_value=True),contextlib.redirect_stdout(io.StringIO()):
                draft=brief();draft['selected_style']='adrian-kul'
                client.return_value.generate_brief.side_effect=[draft,refplan()]
                code=cli.main(['create','--linkedin','https://www.linkedin.com/in/example/','--website','https://example.com',
                               '--reuse-portrait',str(portrait),'--output',str(root)])
            self.assertEqual(code,0);palette.assert_not_called()
            self.assertNotIn('brand_palette',render.call_args.args[0])
