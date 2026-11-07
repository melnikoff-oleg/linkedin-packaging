"""A different filename, size or color treatment must not disguise a reused shot."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

from linkedin_pack.visual_assets import validate_photo_pair, banner_photo_prompt, BANNER_PHOTO_STYLES, has_transparent_background, banner_cutout_prompt


def patterned_photo(path, alternate=False, transparent=False):
    image=Image.new('RGB',(256,256),'#203d42')
    draw=ImageDraw.Draw(image)
    draw.ellipse((65,22,177,143),fill='#ba9872')
    draw.polygon([(23,256),(54,152),(184,147),(235,256)],fill='#171920')
    if alternate:
        draw.rectangle((0,0,125,256),fill='#c7a472')
        draw.ellipse((143,91,242,208),fill='#442c33')
    else:
        draw.line((85,80,151,81),fill='#121212',width=8)
        draw.line((0,198,256,240),fill='#306c62',width=7)
    if transparent:
        image=image.convert('RGBA')
        alpha=Image.new('L',image.size,0)
        ImageDraw.Draw(alpha).rectangle((35,10,220,255),fill=255)
        image.putalpha(alpha)
    image.save(path)


class VisualAssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.profile=self.root/'profile.png';patterned_photo(self.profile)

    def test_same_file_and_identical_copy_are_rejected(self):
        copy=self.root/'copy.png';copy.write_bytes(self.profile.read_bytes())
        for candidate in [self.profile,copy]:
            with self.assertRaisesRegex(ValueError,'same photograph'):
                validate_photo_pair(self.profile,candidate)

    def test_resized_reencoded_photo_is_rejected(self):
        copy=self.root/'resized.jpg'
        Image.open(self.profile).resize((800,800),Image.Resampling.LANCZOS).save(copy,quality=90)
        with self.assertRaisesRegex(ValueError,'same photograph'):
            validate_photo_pair(self.profile,copy)

    def test_grayscale_restyle_is_rejected(self):
        copy=self.root/'monochrome.png'
        ImageOps.grayscale(Image.open(self.profile)).save(copy)
        with self.assertRaisesRegex(ValueError,'same photograph'):
            validate_photo_pair(self.profile,copy)

    def test_distinct_frame_has_explicit_roles_and_review_requirement(self):
        other=self.root/'other.png';patterned_photo(other,alternate=True)
        result=validate_photo_pair(self.profile,other)
        self.assertEqual(result['profile_portrait']['role'],'profile_portrait')
        self.assertEqual(result['banner_photo']['role'],'banner_photo')
        self.assertNotEqual(result['profile_portrait']['sha256'],result['banner_photo']['sha256'])
        self.assertEqual(result['combined_profile_review'],'required')

    def test_flat_backgrounds_are_not_a_photographic_match(self):
        first=self.root/'white.png';second=self.root/'gray.png'
        Image.new('RGB',(64,64),'white').save(first)
        Image.new('RGB',(64,64),'#888888').save(second)
        # A correlation of two flat frames is undefined, not proof of reuse.
        self.assertEqual(validate_photo_pair(first,second)['combined_profile_review'],'required')

    def test_banner_prompt_changes_composition_not_just_color(self):
        for style in BANNER_PHOTO_STYLES:
            prompt=banner_photo_prompt(style)
            self.assertIn('distinct photograph',prompt)
            self.assertIn('waist',prompt)
            self.assertIn('not a recolor',prompt)
            self.assertNotIn('Kal',prompt)

    def test_cutout_requires_substantial_real_alpha_and_opaque_subject(self):
        cutout=self.root/'cutout.png';patterned_photo(cutout,alternate=True,transparent=True)
        self.assertTrue(has_transparent_background(cutout))
        self.assertFalse(has_transparent_background(self.profile))
        fake=Image.open(self.profile).convert('RGBA');fake.putpixel((0,0),(0,0,0,0))
        fake.save(self.root/'one-transparent-pixel.png')
        self.assertFalse(has_transparent_background(self.root/'one-transparent-pixel.png'))
        Image.new('RGBA',(128,128),(0,0,0,0)).save(self.root/'empty.png')
        self.assertFalse(has_transparent_background(self.root/'empty.png'))

    def test_cutout_prompt_preserves_existing_frame(self):
        prompt=banner_cutout_prompt()
        self.assertIn('Remove only the background',prompt)
        self.assertIn('EXACTLY',prompt)
        self.assertIn('not a checkerboard',prompt)

    def test_near_opaque_254_subject_is_a_usable_cutout(self):
        cutout=self.root/'near-opaque.png'
        image=Image.new('RGBA',(128,128),(0,0,0,0))
        ImageDraw.Draw(image).rectangle((25,12,105,127),fill=(160,120,85,254))
        image.save(cutout)
        self.assertTrue(has_transparent_background(cutout))

    def test_translucent_subject_and_opaque_token_do_not_pass(self):
        for filename,subject_alpha in [('translucent.png',128),('almost.png',249)]:
            image=Image.new('RGBA',(128,128),(0,0,0,0))
            ImageDraw.Draw(image).rectangle((25,12,105,127),fill=(160,120,85,subject_alpha))
            image.putpixel((64,64),(160,120,85,255))
            image.save(self.root/filename)
            self.assertFalse(has_transparent_background(self.root/filename))
        Image.new('RGBA',(128,128),(160,120,85,254)).save(self.root/'uniform.png')
        self.assertFalse(has_transparent_background(self.root/'uniform.png'))
