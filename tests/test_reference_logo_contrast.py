"""Exact opt-in preserves multitone logo details without changing source pixels."""
import base64
import copy
import hashlib
import io
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image, ImageDraw
from linkedin_pack.reference_layout import reference_banner_html, registry


class LogoElements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.logos = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('class') == 'company-logo':
            self.logos.append((tag, attrs))


class InternalLogoContrastTests(unittest.TestCase):
    def fixture(self, root, opt_in=None, opaque=False):
        (root / 'logos').mkdir()
        image = Image.new('RGBA', (24, 26), (255, 255, 255, 255) if opaque else (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((4, 3, 19, 22), fill=(140, 21, 21, 255))
        draw.rectangle((9, 7, 14, 18), fill=(222, 238, 228, 255))
        draw.rectangle((11, 9, 12, 16), fill=(0, 65, 30, 255))
        path = root / 'logos/multitone.png'
        image.save(path)
        raw = path.read_bytes()
        record = {'sha256': hashlib.sha256(raw).hexdigest(), 'company': 'Multitone Company'}
        if opt_in is not None:
            record['preserve_internal_contrast'] = opt_in
        (root / 'logos/provenance.json').write_text(json.dumps({'multitone': record}))
        content = copy.deepcopy(registry()['clarekitching'][1])
        content['logos'] = ['multitone', '', '']
        brief = {'selected_style': 'clarekitching', 'layout_mode': 'reference-faithful',
                 'reference_content': content, 'logo_assets': {'multitone': 'logos/multitone.png'}}
        return brief, image, raw

    def test_explicit_opt_in_preserves_all_internal_pixels_and_same_crop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            brief, source, original_bytes = self.fixture(root, True)
            rendered = reference_banner_html(brief, 'clarekitching', asset_root=root)
            [(tag, attrs)] = LogoElements(rendered).logos
            self.assertEqual(tag, 'img')
            self.assertEqual(attrs['data-preserve-internal-contrast'], 'true')
            self.assertEqual(attrs['data-logo-key'], 'multitone')
            self.assertEqual(attrs['style'], 'width:155.0px;height:32.0px;object-fit:contain')
            self.assertNotIn('mask:', attrs['style'])
            with Image.open(io.BytesIO(base64.b64decode(attrs['src'].split(',', 1)[1]))) as decoded:
                expected = source.crop(source.getchannel('A').getbbox())
                self.assertEqual(decoded.size, expected.size)
                self.assertEqual(decoded.convert('RGBA').tobytes(), expected.tobytes())
                self.assertEqual(len(decoded.getcolors()), 3)
            self.assertEqual((root / 'logos/multitone.png').read_bytes(), original_bytes)

    def test_default_and_truthy_non_booleans_keep_the_existing_alpha_mask(self):
        for opt_in in (None, False, 1, 'true', ['true']):
            with self.subTest(opt_in=opt_in), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                brief, source, _ = self.fixture(root, opt_in)
                [(tag, attrs)] = LogoElements(reference_banner_html(brief, 'clarekitching', asset_root=root)).logos
                self.assertEqual(tag, 'span')
                self.assertNotIn('data-preserve-internal-contrast', attrs)
                self.assertIn('width:155.0px;height:32.0px;background:#ffffff;mask:', attrs['style'])
                uri = re.search(r'mask:url\((data:image/png;base64,[^)]+)\)', attrs['style']).group(1)
                with Image.open(io.BytesIO(base64.b64decode(uri.split(',', 1)[1]))) as decoded:
                    expected = source.crop(source.getchannel('A').getbbox())
                    self.assertEqual(decoded.convert('RGBA').tobytes(), expected.tobytes())

    def test_opt_in_cannot_bypass_asset_hash_or_transparency_checks(self):
        for failure in ('hash', 'opaque'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                brief, _, _ = self.fixture(root, True, opaque=failure == 'opaque')
                if failure == 'hash':
                    path = root / 'logos/multitone.png'
                    path.write_bytes(path.read_bytes() + b'changed')
                with self.assertRaisesRegex(ValueError, 'hash mismatch' if failure == 'hash' else 'transparent'):
                    reference_banner_html(brief, 'clarekitching', asset_root=root)


if __name__ == '__main__':
    unittest.main()
