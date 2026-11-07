"""An optional subject fit never moves the original reference frame or type."""
import copy
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from linkedin_pack.core import validate_brief
from linkedin_pack.reference_layout import registry, reference_banner_html
from linkedin_pack.reference_qa import measure_reference_design


def brief():
    content=copy.deepcopy(registry()['laraacostar'][1])
    content['logos']=['','','','']
    return {'name':'Example Person','audience':'Example audience','positioning':'Source-backed role',
        'evidence':[{'claim':'Source-backed role','source':'https://example.com/profile'}],
        'selected_style':'laraacostar','headline':'Example professional role',
        'banner_title':'Example professional role','banner_subtitle':'','proof_points':[],
        'proof_cards':[],'cta':'','portrait_prompt':'Local photo','rationale':'Subject fit',
        'layout_mode':'reference-faithful','reference_content':content}


class ReferencePhotoFramingTests(unittest.TestCase):
    def test_invalid_subject_fit_is_rejected(self):
        for value in ({'scale':0.49},{'scale':1.01},{'scale':True},{'scale':'0.8'},
                      {'scale':float('nan')},{'scale':float('inf')},{'scale':10**400},{'scale':0.8,'x':10},False):
            with self.subTest(value=value):
                b=brief();b['photo_framing']=value
                with self.assertRaisesRegex(ValueError,'photo_framing'):
                    validate_brief(b)

    def test_subject_fit_is_only_available_in_reference_photo_layouts(self):
        nonphoto=brief();nonphoto['selected_style']='adrian-kul'
        nonphoto['reference_content']=copy.deepcopy(registry()['adrian-kul'][1])
        evidence=brief();evidence['layout_mode']='evidence';del evidence['reference_content']
        for b in (nonphoto,evidence):
            b['photo_framing']={'scale':.8}
            with self.subTest(style=b['selected_style'],mode=b['layout_mode']):
                with self.assertRaisesRegex(ValueError,'photo_framing'):
                    validate_brief(b)

    def test_default_fit_is_byte_identical(self):
        plain=brief();explicit=copy.deepcopy(plain);explicit['photo_framing']={'scale':1}
        self.assertEqual(reference_banner_html(plain,'laraacostar'),reference_banner_html(explicit,'laraacostar'))

    def test_subject_scales_but_reference_regions_and_text_remain_fixed(self):
        with tempfile.TemporaryDirectory() as temp:
            photo=Path(temp)/'photo.png'
            Image.new('RGBA',(400,600),(40,40,40,255)).save(photo)
            b=brief()
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':1584,'height':396})
                states=[]
                for scale in (1,.72):
                    b['photo_framing']={'scale':scale};validate_brief(b)
                    page.set_content(reference_banner_html(b,'laraacostar',photo=photo))
                    page.evaluate('document.fonts.ready')
                    states.append((measure_reference_design(page,'laraacostar'),page.locator('[data-ref="photo"]>img').bounding_box()))
                browser.close()
            geometry=lambda state:[{key:row[key] for key in ('slot','x','y','width','height')} for row in state[0]['regions']]
            self.assertEqual(geometry(states[0]),geometry(states[1]))
            self.assertEqual(states[0][0]['text'],states[1][0]['text'])
            self.assertEqual(states[1][0]['status'],'passed')
            self.assertAlmostEqual(states[1][1]['width']/states[0][1]['width'],.72,places=5)
            self.assertAlmostEqual(states[1][1]['height']/states[0][1]['height'],.72,places=5)


if __name__=='__main__':unittest.main()
