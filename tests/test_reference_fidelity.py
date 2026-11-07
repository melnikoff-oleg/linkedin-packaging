import copy
import hashlib
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from linkedin_pack.reference_qa import audit_reference_design,measure_reference_design
from linkedin_pack.reference_layout import registry,validate_reference_content
from linkedin_pack.reference_review import FILES,reference_review_passed,reference_buyer_review_passed


class ReferenceFidelityTests(unittest.TestCase):
    def report(self):
        box={'x':757,'y':43,'width':635,'height':130}
        return {'text':[{'font_size':13,'text':'Small original caption','ink':{'x':800,'y':210,'width':150,'height':12}}],
                'regions':[{'slot':'title',**box}], 'reference_regions':{'title':box}}

    def test_source_sized_secondary_text_does_not_trigger_unrelated_floor(self):
        self.assertEqual(audit_reference_design(self.report())['status'],'passed')

    def test_moving_or_resizing_original_region_fails(self):
        for key in ('x','y','width','height'):
            with self.subTest(key=key):
                r=self.report();r['regions'][0][key]+=20
                self.assertEqual(audit_reference_design(r)['status'],'failed')

    def test_missing_reference_slot_fails(self):
        r=self.report();r['regions']=[]
        self.assertEqual(audit_reference_design(r)['status'],'failed')

    def test_off_canvas_text_fails_even_with_matching_region(self):
        r=self.report();r['text'][0]['ink']['x']=1560
        self.assertEqual(audit_reference_design(r)['status'],'failed')

    def test_text_clipped_by_card_fails_inside_canvas(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch()
            page=browser.new_page(viewport={'width':1584,'height':396})
            page.set_content('''<style>body{margin:0}.banner{width:1584px;height:396px}
                .card{position:absolute;left:500px;top:100px;width:120px;height:40px;overflow:hidden;white-space:nowrap;font:20px Arial}</style>
                <div class="banner"><div class="card">WWWWWWWWWWWWWWWW</div></div>''')
            report=measure_reference_design(page,'diandraescobar')
            browser.close()
        self.assertTrue(any('Text clipped' in error for error in report['failures']),report['failures'])

    def test_clipping_respects_axis_and_tolerance(self):
        r=self.report()
        r['text'][0]['clipping_ancestors']=[{'element':'card','x':800,'y':200,'width':151,'height':5,'clip_x':True,'clip_y':False}]
        self.assertEqual(audit_reference_design(r)['status'],'passed')
        r['text'][0]['clipping_ancestors'][0]['clip_y']=True
        self.assertEqual(audit_reference_design(r)['status'],'failed')

    def test_no_silent_kal_fixture_fallback(self):
        for slug in registry():
            with self.subTest(slug=slug):
                with self.assertRaisesRegex(ValueError,'explicitly'):
                    validate_reference_content({'selected_style':slug,'layout_mode':'reference-faithful'})

    def test_extra_reference_slot_is_never_silently_discarded(self):
        for slug,(_,content,_) in registry().items():
            with self.subTest(slug=slug):
                b={'selected_style':slug,'layout_mode':'reference-faithful','reference_content':copy.deepcopy(content)}
                b['reference_content']['extra_unrendered_claim']='Unsupported proof'
                with self.assertRaises(ValueError):validate_reference_content(b)

    def test_all_ten_have_source_region_contract(self):
        self.assertEqual(len(registry()),10)
        for slug,(_,_,regions) in registry().items():
            self.assertTrue(regions,slug)
            self.assertIn('title',regions,slug)

    def test_visual_acceptance_cannot_override_failed_technical_qa(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'sample';folder.mkdir()
            reviews=root/'test_account/reviews';reviews.mkdir(parents=True)
            for name in FILES:(folder/name).write_bytes(name.encode())
            hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in FILES}
            (reviews/'reference-independent-test.json').write_text(json.dumps({'reviews':{'sample':{'verdict':'accept','findings':[],'sha256':hashes}}}))
            (folder/'qa.json').write_text(json.dumps({'passed':False,'failures':['Text overflow']}))
            with patch('linkedin_pack.reference_review.ROOT',root):
                self.assertFalse(reference_review_passed(folder))

    def test_buyer_acceptance_requires_current_images_and_no_required_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'sample';folder.mkdir()
            reviews=root/'test_account/reviews';reviews.mkdir(parents=True)
            names=('review-desktop.png','review-mobile.png')
            for name in names:(folder/name).write_bytes(name.encode())
            hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in names}
            item={'style':'sample','verdict':'accept','required_findings':[],'sha256':hashes}
            path=reviews/'reference-buyer-release-final.json'
            path.write_text(json.dumps({'reviews':[item]}))
            (reviews/'reference-buyer-release.json').write_text(json.dumps({'reviews':[item]}))
            with patch('linkedin_pack.reference_review.ROOT',root):
                self.assertTrue(reference_buyer_review_passed(folder))
                item['required_findings']=['Undefined outcome metric']
                path.write_text(json.dumps({'reviews':[item]}))
                self.assertFalse(reference_buyer_review_passed(folder))
                item['required_findings']=[]
                path.write_text(json.dumps({'reviews':[item]}))
                (folder/names[0]).write_bytes(b'changed pixels')
                self.assertFalse(reference_buyer_review_passed(folder))

if __name__=='__main__':unittest.main()
