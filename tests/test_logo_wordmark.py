import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw
from linkedin_pack.render import banner_html
from tests.test_core import brief


class WordmarkIdentityTests(unittest.TestCase):
    def render(self, record=None, opaque_background=None):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'logos').mkdir()
            image=Image.new('RGBA',(160,50),opaque_background or (0,0,0,0))
            ImageDraw.Draw(image).rectangle((10,10,150,40),fill='black')
            path=root/'logos/123.png';image.save(path)
            if record is not None:
                record=dict(record)
                if record.get('sha256')=='current':record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
                (root/'logos/provenance.json').write_text(json.dumps({'123':record}))
            plan=brief();plan['logo_assets']={'123':'logos/123.png'}
            plan['proof_points']=[]
            plan['proof_cards']=[dict(company_id='123',company='Example Company',role='Former CTO',
                                      value='A concrete result',detail='',source='Source profile')]
            return banner_html(plan,'clarekitching',asset_root=root)

    def test_transparent_symbol_keeps_readable_company_identity(self):
        html=self.render()
        self.assertTrue('<div class="company-name">Example Company</div>' in html)
        self.assertTrue('--logo-w:64.00px;--logo-h:64.00px' in html)

    def test_verified_current_wordmark_can_replace_duplicate_text(self):
        html=self.render({'readable_wordmark':True,'sha256':'current'})
        self.assertFalse('<div class="company-name">Example Company</div>' in html)
        self.assertFalse('--logo-w:64.00px;--logo-h:64.00px' in html)

    def test_changed_wordmark_cannot_inherit_old_identity_attestation(self):
        html=self.render({'readable_wordmark':True,'sha256':'0'*64})
        self.assertTrue('<div class="company-name">Example Company</div>' in html)
        self.assertTrue('--logo-w:64.00px;--logo-h:64.00px' in html)

    def test_truthy_string_is_not_a_verified_readable_wordmark(self):
        html=self.render({'readable_wordmark':'true','sha256':'current'})
        self.assertTrue('<div class="company-name">Example Company</div>' in html)

    def test_display_crop_requires_current_wordmark_attestation(self):
        for sha,expected in [('current',True),('0'*64,False)]:
            with self.subTest(sha=sha):
                html=self.render({'readable_wordmark':True,'sha256':sha,
                                  'display_clip_right_fraction':.04})
                self.assertEqual('clip-path:inset(0 4.000000% 0 0)' in html,expected)

    def test_display_crop_cannot_erase_a_large_part_of_the_mark(self):
        for value in [-.01,.5,'0.04',True]:
            with self.subTest(value=value):
                html=self.render({'readable_wordmark':True,'sha256':'current',
                                  'display_clip_right_fraction':value})
                self.assertNotIn('clip-path:inset(',html)

    def test_opaque_backgrounds_are_omitted_instead_of_blended_into_plates(self):
        for color in ('navy','white'):
            with self.subTest(background=color):
                html=self.render({'readable_wordmark':True,'sha256':'current'},opaque_background=color)
                self.assertTrue('<div class="company-name">Example Company</div>' in html)
                self.assertFalse('<img class="company-logo' in html)
