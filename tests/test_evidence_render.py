import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from tests.test_core import brief
from linkedin_pack.render import banner_html, text_regions_overlap, measure_design_details, audit_design_details, font_css


class EvidenceRenderTests(unittest.TestCase):
    def plan(self):
        plan=brief()
        plan['proof_points']=[]
        plan['proof_cards']=[dict(company_id='123',company='Example Co',role='Former engineering lead',
                                  value='~30% more releases',detail='Shorter planning cycles',source='Source experience')]
        plan['logo_assets']={'123':'logos/123.png'}
        return plan

    def test_case_evidence_and_original_logo_are_actually_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'logos').mkdir()
            mark=Image.new('RGBA',(40,40),(0,0,0,0))
            ImageDraw.Draw(mark).ellipse((5,5,35,35),fill='navy')
            mark.save(root/'logos/123.png')
            pagefile=root/'banner.html';pagefile.write_text(banner_html(self.plan(),'clarekitching',asset_root=root))
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':1584,'height':396})
                page.goto(pagefile.as_uri())
                card=page.locator('.proof-card')
                self.assertEqual(card.count(),1)
                self.assertTrue(card.is_visible())
                self.assertIn('Example Co',card.inner_text())
                self.assertIn('~30% more releases',card.inner_text())
                self.assertTrue(card.locator('img').is_visible())
                browser.close()

    def test_logo_cannot_read_outside_the_package(self):
        plan=self.plan();plan['logo_assets']={'123':'../../secret.png'}
        with self.assertRaises(ValueError):banner_html(plan,'clarekitching',asset_root=Path('/tmp'))

    def test_subtitle_and_case_row_collision_is_a_failure(self):
        subtitle=dict(x=535,y=160,width=1000,height=110)
        card=dict(x=535,y=225,width=320,height=150)
        self.assertTrue(text_regions_overlap(subtitle,card))
        self.assertFalse(text_regions_overlap(dict(subtitle,height=50),card))


class DesignDetailAuditTests(unittest.TestCase):
    def measure(self, css, body, evidence=True, canvas=True):
        with sync_playwright() as p:
            browser=p.chromium.launch()
            page=browser.new_page(viewport={'width':1584,'height':396})
            page.set_content(f'<style>{font_css()} body{{margin:0}}.banner{{width:1584px;height:396px;position:relative;font-family:Inter}}{css}</style><main class="{"banner" if canvas else "unframed"} {"evidence-layout" if evidence else ""}">{body}</main>')
            page.evaluate('document.fonts.ready')
            report=measure_design_details(page)
            browser.close()
        return audit_design_details(report)

    def test_serif_highlight_cannot_cover_previous_line_descenders(self):
        # The former Clare treatment fit inside h1 but the second inline span's
        # background painted over the first line's descender. Check ink/paint,
        # not only line-group rectangles or text overflowing the canvas.
        report=self.measure('h1{position:absolute;left:535px;top:28px;margin:0;font:59px/1.02 DMSerifDisplay;letter-spacing:-1px}.line:last-child{background:pink;font-style:italic;padding:0 7px}',
                            '<h1><span class="line">Price quotes.</span><br><span class="line">From minutes to five seconds.</span></h1>')
        self.assertTrue(any('headline ink/background overlap' in failure.lower() for failure in report['failures']))
        self.assertGreater(report['title_lines'][0]['ink']['height'],0)

    def test_separate_highlight_line_with_real_clearance_passes(self):
        report=self.measure('h1{position:absolute;left:535px;top:40px;margin:0;font:60px/1.1 DMSerifDisplay;letter-spacing:-.5px}.line{display:block;width:max-content}.line+.line{margin-top:18px}.line:last-child{background:pink;font-style:italic;padding:4px 10px}',
                            '<h1><span class="line">Price quotes.</span><span class="line">From minutes to five seconds.</span></h1>')
        self.assertEqual(report['failures'],[])
        self.assertGreaterEqual(report['title_line_gaps'][0]['clearance'],12)

    def test_tiny_support_copy_and_cramped_card_edge_are_rejected(self):
        report=self.measure('.proof-card{position:absolute;left:535px;top:10px;padding:8px;background:white}.card-detail{font-size:36px}',
                            '<section class="proof-card"><div class="card-detail">Former leadership role</div></section>')
        self.assertTrue(any('text below minimum' in failure.lower() for failure in report['failures']))
        self.assertTrue(any('card edge clearance' in failure.lower() for failure in report['failures']))
        self.assertAlmostEqual(report['text'][0]['mobile_font_px'],36*390/1584,places=2)

    def test_legacy_renderer_cannot_bypass_strict_typography_audit(self):
        report=self.measure('p{font-size:12px}', '<p>Old layout</p>', evidence=False)
        self.assertEqual(report['status'],'failed')
        self.assertTrue(any('Text below minimum' in failure for failure in report['failures']))

    def test_missing_banner_canvas_cannot_skip_the_audit(self):
        report=self.measure('p{font-size:48px}', '<p>No banner canvas</p>', evidence=False,canvas=False)
        self.assertEqual(report['status'],'failed')
        self.assertTrue(any('Missing banner canvas' in failure for failure in report['failures']))

    def test_copy_and_proof_need_separation_only_when_columns_overlap(self):
        css='.content{position:absolute;left:535px;top:60px;width:600px;font-size:48px}.subtitle{line-height:1.2;white-space:pre-line}.proof-grid{position:absolute;left:535px;top:180px;font-size:48px}'
        body='<div class="content"><div class="subtitle">Business\noutcome</div></div><div class="proof-grid">Supporting evidence</div>'
        report=self.measure(css,body)
        self.assertTrue(any('content/proof separation' in failure.lower() for failure in report['failures']))
        self.assertAlmostEqual(report['content_proof_gap']['clearance'],4.8,places=1)
        separate=self.measure(css+'.proof-grid{left:1200px;width:300px}',body)
        self.assertFalse(any('content/proof separation' in failure.lower() for failure in separate['failures']))
        self.assertFalse(separate['content_proof_gap']['columns_overlap'])

    def test_horizontal_metric_groups_measure_each_child_font_and_allow_support_caption(self):
        css='h1{position:absolute;left:535px;top:40px;margin:0;display:grid;grid-template-columns:360px 360px;gap:40px;font:60px/1.1 Inter}.line{display:grid;gap:12px;width:max-content}.metric{font-size:90px}.metric-caption{font-size:48px}'
        body='<h1><span class="line"><span class="metric">~30%</span><span class="metric-caption">more releases</span></span><span class="line"><span class="metric">~25%</span><span class="metric-caption">less testing effort</span></span></h1>'
        report=self.measure(css,body)
        self.assertEqual(report['failures'],[])
        self.assertEqual(report['title_line_gaps'][0]['axis'],'horizontal')
        self.assertGreaterEqual(report['title_line_gaps'][0]['clearance'],24)
        self.assertEqual([p['font_size'] for p in report['title_lines'][0]['glyph_parts']],[90,48])
        caption=next(item for item in report['text'] if item['text']=='more releases')
        self.assertEqual(caption['kind'],'support')
        self.assertGreater(report['title_lines'][0]['ink']['height'],90)
        too_small=self.measure(css+'.metric{font-size:54px}',body)
        self.assertTrue(any('54px < 56px' in failure for failure in too_small['failures']))

    def test_horizontal_metric_groups_need_24px_optical_clearance(self):
        report=self.measure('h1{position:absolute;left:535px;top:40px;margin:0;display:grid;grid-template-columns:max-content max-content;gap:8px;font:60px/1.1 Inter}.line{display:grid;gap:12px}.metric{font-size:90px}.metric-caption{font-size:48px}',
                            '<h1><span class="line"><span class="metric">~30%</span><span class="metric-caption">more releases</span></span><span class="line"><span class="metric">~25%</span><span class="metric-caption">less testing</span></span></h1>')
        self.assertTrue(any('Headline column clearance below 24px' in failure for failure in report['failures']))

    def test_multiline_role_glyph_overlap_is_rejected_inside_one_group(self):
        css='.company-role{position:absolute;left:535px;top:60px;font-size:48px;line-height:.7}'
        body='<div class="company-role">Founding<br>CTO</div>'
        cramped=self.measure(css,body)
        self.assertTrue(any('Text ink overlap' in failure for failure in cramped['failures']))
        safe=self.measure(css+'.company-role{line-height:1.15}',body)
        self.assertEqual(safe['failures'],[])

    def test_interlocking_content_columns_use_child_bounds_not_empty_parent_area(self):
        css='.content{position:absolute;left:540px;top:48px;width:996px}h1{width:600px;height:230px;font:60px/1.15 Inter;margin:0}.subtitle{position:absolute;left:660px;top:0;width:336px;font:48px/1.15 Inter;white-space:pre-line}.proof-grid{position:absolute;left:1200px;top:182px;width:336px;height:174px;font-size:48px}'
        body='<div class="content"><h1>~30%</h1><div class="subtitle">Online\nfundraising</div></div><div class="proof-grid">Former VP</div>'
        safe=self.measure(css,body)
        self.assertEqual(safe['failures'],[])
        self.assertAlmostEqual(safe['content_proof_gap']['clearance'],23.6,places=1)
        self.assertFalse(safe['content_proof_gap']['pairs'][0]['columns_overlap'])
        self.assertTrue(safe['content_proof_gap']['pairs'][1]['columns_overlap'])
        overlap=self.measure(css,body.replace('Online\nfundraising','Online\nfundraising\nsoftware'))
        self.assertTrue(any('Content/proof separation' in failure for failure in overlap['failures']))

    def test_floating_logo_is_checked_against_mobile_portrait_and_banner_edges(self):
        css='.company-logo{position:absolute;left:64px;top:40px;width:160px;height:100px;background:teal}'
        body='<div class="company-logo" role="img" aria-label="Example mark"></div>'
        self.assertEqual(self.measure(css,body)['failures'],[])
        overlapping=self.measure(css+'.company-logo{top:160px}',body)
        self.assertTrue(any('Logo overlaps mobile portrait' in failure for failure in overlapping['failures']))
        outside=self.measure(css+'.company-logo{left:1500px}',body)
        self.assertTrue(any('Logo outside banner' in failure for failure in outside['failures']))
