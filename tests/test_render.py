import tempfile
import unittest
from pathlib import Path
from tests.test_core import brief
from linkedin_pack.render import banner_html, preview_html, check_images, mobile_portrait_overlap, render_package
from linkedin_pack.styles import STYLES


class RenderTests(unittest.TestCase):
    def test_photo_led_render_requires_a_separate_banner_shot(self):
        from PIL import Image
        data=brief();data['selected_style']='laraacostar'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'person.png';Image.new('RGB',(80,80),'navy').save(path)
            with self.assertRaisesRegex(ValueError,'separate banner'):
                render_package(data,path,Path(folder)/'out')
            with self.assertRaisesRegex(ValueError,'same photograph'):
                render_package(data,path,Path(folder)/'out',banner_photo_path=path)

    def test_nonphoto_banner_does_not_embed_avatar(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'person.png';Image.new('RGB',(80,80),'navy').save(path)
            result=banner_html(brief(),'charlie-hills',path)
            self.assertFalse('<img class="hero-portrait"' in result)

    def test_explicit_empty_cards_use_modern_readable_layout(self):
        data=brief();data.update(proof_cards=[],proof_points=[])
        result=banner_html(data,'clarekitching')
        self.assertTrue('banner evidence-layout' in result)
        self.assertFalse('<div class="proof-grid">' in result)

    def test_modern_brief_without_case_evidence_can_render_readably(self):
        from PIL import Image
        data=brief();data.update(proof_cards=[],proof_points=[],evidence=[],
                                banner_title='Clear technology.\nPractical direction.',
                                banner_subtitle='Part-time leadership')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);portrait=root/'portrait.png';Image.new('RGB',(80,80),'navy').save(portrait)
            report=render_package(data,portrait,root/'out')
            self.assertTrue(report['passed'],report['failures'])
            self.assertEqual(report['design_details']['status'],'passed')
            self.assertEqual(report['design_details']['cards'],[])
    def test_mobile_overlap_accounts_for_large_circular_crop(self):
        self.assertTrue(mobile_portrait_overlap(dict(x=445,y=240,width=300,height=70)))
        self.assertFalse(mobile_portrait_overlap(dict(x=535,y=240,width=300,height=70)))
        self.assertFalse(mobile_portrait_overlap(dict(x=155,y=66,width=900,height=50)))
    def test_user_copy_is_html_escaped(self):
        data=brief(); data['banner_title']='<script>alert(1)</script>'
        result=banner_html(data, 'clarekitching', None)
        self.assertNotIn('<script>alert(1)</script>', result)
        self.assertIn('&lt;script&gt;', result)

    def test_ten_distinct_reference_layouts(self):
        self.assertEqual(len(STYLES), 10)
        rendered=[banner_html(brief(), style, None) for style in STYLES]
        self.assertEqual(len(set(rendered)), 10)
        for html in rendered:
            self.assertIn('data-qa="essential"', html)
            self.assertNotIn('Forbes', html)

    def test_preview_has_no_fabricated_verification_or_followers(self):
        html=preview_html(brief(), 'banner.png', 'portrait.png', 'Chicago')
        self.assertNotIn('Verified', html)
        self.assertNotIn('followers', html)
        self.assertIn('Layout preview', html)

    def test_qa_rejects_bad_dimensions(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            for name in ('banner.png','portrait.png','preview.png'):
                Image.new('RGB',(20,20)).save(Path(d)/name)
            report=check_images(Path(d), brief())
            self.assertFalse(report['passed'])
            self.assertTrue(report['failures'])

    def test_website_palette_overrides_reference_surfaces(self):
        data=brief(); data['brand_palette']={'bg':'#ffffff','fg':'#111111','accent':'#1855aa'}
        for style in STYLES:
            result=banner_html(data,style,None)
            self.assertTrue('brand-override' in result)
            self.assertTrue('background:var(--bg)!important' in result)

    def test_palette_rejects_css_injection(self):
        data=brief();data['brand_palette']={'bg':'red;display:none'}
        with self.assertRaises(ValueError):banner_html(data,'clarekitching',None)

    def test_website_accent_must_remain_legible_as_mobile_text(self):
        from linkedin_pack.render import contrast
        data=brief();data['brand_palette']={'bg':'#ffffff','fg':'#111111','accent':'#888888'}
        self.assertGreaterEqual(contrast('#888888','#ffffff'),3)
        self.assertLess(contrast('#888888','#ffffff'),4.5)
        with self.assertRaisesRegex(ValueError,'accent contrast >=4.5'):
            banner_html(data,'clarekitching',None)

    def test_failed_rerender_invalidates_previous_ready_state(self):
        import json
        from PIL import Image
        data=brief();data['selected_style']='charlie-hills'
        data['brand_palette']={'bg':'invalid'}
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'out';output.mkdir()
            portrait=Path(folder)/'portrait.png';Image.new('RGB',(80,80),'navy').save(portrait)
            (output/'qa.json').write_text(json.dumps({'passed':True,'acceptance':'ready'}))
            (output/'blind-review.json').write_text('{}')
            with self.assertRaises(ValueError):
                render_package(data,portrait,output)
            self.assertFalse(json.loads((output/'qa.json').read_text())['passed'])
            self.assertFalse((output/'blind-review.json').exists())

    def test_evidence_headline_is_not_shrunk_below_readable_floor_to_force_fit(self):
        from unittest.mock import patch
        from PIL import Image
        data=brief();data['selected_style']='charlie-hills'
        source='''<style>body{margin:0}.banner{width:1584px;height:396px;position:relative}.content{position:absolute;left:535px;top:40px;width:160px}h1{font:60px/1.2 Arial;margin:0;white-space:nowrap}.line{display:block;width:max-content}</style><main class="banner"><div class="content"><h1 data-qa="essential"><span class="line">A deliberately overlong headline</span></h1></div></main>'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);portrait=root/'portrait.png';Image.new('RGB',(80,80),'navy').save(portrait)
            with patch('linkedin_pack.render.banner_html',return_value=source):
                report=render_package(data,portrait,root/'out')
            self.assertFalse(report['passed'])
            self.assertEqual(report['design_details']['text'][0]['font_size'],56)
            self.assertTrue(any('Text overflow' in failure for failure in report['failures']))

    def test_neutral_mobile_review_preserves_actual_css_display_size(self):
        from unittest.mock import patch
        from PIL import Image
        data=brief();data['selected_style']='charlie-hills'
        source='<style>body{margin:0}.banner{width:1584px;height:396px;background:navy}</style><main class="banner"></main>'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);portrait=root/'portrait.png';Image.new('RGB',(80,80),'navy').save(portrait)
            with patch('linkedin_pack.render.banner_html',return_value=source):
                render_package(data,portrait,root/'out')
            for name,width in [('review-mobile.png',390),('preview-mobile.png',780),('review-desktop.png',792)]:
                with self.subTest(image=name),Image.open(root/'out'/name) as image:
                    self.assertEqual(image.width,width)
