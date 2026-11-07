import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from linkedin_pack.before import BeforeUnavailable, capture_before, _rasterize
from linkedin_pack.cli import build_parser, main


def image_bytes(color='blue', size=(80, 80)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, 'PNG')
    return buffer.getvalue()


class BeforePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.output = self.root / 'person'
        self.profile = self.source / 'profile.json'
        self.profile.write_text(json.dumps({'name': 'Example Person', 'headline': 'Original headline',
            'location': 'Example City', 'url': 'https://www.linkedin.com/in/example/',
            'portrait_file': 'portrait.png', 'banner_file': 'banner.png',
            'about': 'PRIVATE RAW FIELD MUST NOT BE SAVED', 'portrait_url': 'https://example.invalid/no-fetch'}))
        (self.source / 'portrait.png').write_bytes(image_bytes())
        (self.source / 'banner.png').write_bytes(image_bytes('green', (320, 80)))
        self.rendered = {'review-desktop.png': image_bytes(size=(792, 460)),
                         'review-mobile.png': image_bytes(size=(390, 390))}

    def capture(self, **kwargs):
        return capture_before(self.profile, self.output, **kwargs)

    def test_writes_only_preview_contract_and_keeps_private_profile_fields_out(self):
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered) as render:
            result = self.capture()
        target = self.output / 'before'
        self.assertEqual(set(p.name for p in target.iterdir()), {'metadata.json', *self.rendered})
        self.assertFalse(result['cached'])
        self.assertEqual(result['name'], 'Example Person')
        self.assertEqual(render.call_args.args[3][0], (self.source / 'banner.png').read_bytes())
        self.assertEqual(render.call_args.args[4][0], (self.source / 'portrait.png').read_bytes())
        saved = (target / 'metadata.json').read_text()
        self.assertNotIn('PRIVATE', saved)
        self.assertNotIn(str(self.root), saved)
        self.assertNotIn('portrait_url', saved)

    def test_identical_inputs_reuse_capture_and_tampered_preview_is_repaired(self):
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered) as render:
            self.capture()
            original = (self.output / 'before' / 'review-desktop.png').stat().st_mtime_ns
            self.assertTrue(self.capture()['cached'])
            self.assertEqual(render.call_count, 1)
            self.assertEqual((self.output / 'before' / 'review-desktop.png').stat().st_mtime_ns, original)
            (self.output / 'before' / 'review-desktop.png').write_bytes(b'changed')
            self.assertFalse(self.capture()['cached'])
            self.assertEqual(render.call_count, 2)

    def test_missing_banner_is_explicitly_disclosed_and_neutral(self):
        (self.source / 'banner.png').unlink()
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered) as render:
            result = self.capture()
        self.assertIsNone(render.call_args.args[3])
        self.assertIn('Original banner unavailable; neutral cover shown.', result['note'])

    def test_missing_original_portrait_never_uses_generated_output_or_remote_url(self):
        (self.source / 'portrait.png').unlink()
        self.output.mkdir()
        (self.output / 'portrait.png').write_bytes(image_bytes('red'))
        with patch('linkedin_pack.before._rasterize') as render:
            with self.assertRaisesRegex(BeforeUnavailable, 'Original profile photo unavailable'):
                self.capture()
        render.assert_not_called()
        self.assertFalse((self.output / 'before').exists())

    def test_source_media_cannot_escape_or_use_remote_or_symlink_paths(self):
        data = json.loads(self.profile.read_text())
        for value in ('../outside.png', '/tmp/portrait.png', 'https://example.org/image.png', 'a\\b.png'):
            data['portrait_file'] = value
            self.profile.write_text(json.dumps(data))
            with self.subTest(value=value), self.assertRaises(BeforeUnavailable):
                self.capture()
        data['portrait_file'] = 'link.png'
        self.profile.write_text(json.dumps(data))
        (self.source / 'link.png').symlink_to(self.source / 'portrait.png')
        with self.assertRaisesRegex(BeforeUnavailable, 'symlink'):
            self.capture()

    def test_explicit_original_files_supported_without_changing_source(self):
        data = json.loads(self.profile.read_text())
        del data['portrait_file']
        self.profile.write_text(json.dumps(data))
        before = self.profile.read_bytes()
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered):
            self.capture(portrait=self.source / 'portrait.png')
        self.assertEqual(before, self.profile.read_bytes())

    def test_render_failure_does_not_replace_an_existing_before(self):
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered):
            self.capture()
        target = self.output / 'before'
        original = {p.name: p.read_bytes() for p in target.iterdir()}
        (self.source / 'portrait.png').write_bytes(image_bytes('red'))
        with patch('linkedin_pack.before._rasterize', side_effect=RuntimeError('private/path')):
            with self.assertRaisesRegex(BeforeUnavailable, 'could not render') as result:
                self.capture()
        self.assertNotIn('private/path', str(result.exception))
        self.assertEqual(original, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_destination_symlinks_are_rejected(self):
        self.output.mkdir()
        elsewhere = self.root / 'elsewhere'; elsewhere.mkdir()
        (self.output / 'before').symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(BeforeUnavailable, 'symlink'):
            self.capture()

    def test_cli_is_offline_and_accepts_separate_gallery_root(self):
        args = build_parser().parse_args(['create', '--linkedin', 'https://www.linkedin.com/in/example/',
                                        '--before-output', 'output/person', '--output', 'output/person/v01'])
        self.assertEqual(args.before_output, 'output/person')
        with patch('linkedin_pack.before._rasterize', return_value=self.rendered), patch('linkedin_pack.cli.load_keys') as keys:
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(['before', '--profile', str(self.profile), '--output', str(self.output)])
        self.assertEqual(result, 0)
        keys.assert_not_called()

    def test_create_captures_collected_originals_once_and_ignores_edited_override(self):
        from tests.test_core import brief
        generated_root = self.output / 'v01'
        shutil.copytree(self.source, generated_root / 'source')
        plan = self.root / 'brief.json'
        plan.write_text(json.dumps(brief()))
        edited = self.root / 'edited.png'
        edited.write_bytes(image_bytes('red'))
        with patch('linkedin_pack.before.capture_before', return_value={}) as capture, \
                patch('linkedin_pack.cli.load_keys', return_value={}), \
                patch('linkedin_pack.cli.render_package', return_value={'passed': True}), \
                patch('linkedin_pack.cli._run_independent_review', return_value=True), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = main(['create', '--linkedin', 'https://www.linkedin.com/in/example/',
                           '--brief', str(plan), '--reuse-portrait', str(edited),
                           '--output', str(generated_root), '--before-output', str(self.output)])
        self.assertEqual(result, 0)
        capture.assert_called_once_with(generated_root / 'source' / 'profile.json', str(self.output))

    def test_browser_reconstruction_escapes_text_and_preserves_native_widths(self):
        # Real offline browser test exercises data URIs and rejects remote requests.
        photo = (image_bytes(), 'image/png')
        rendered = _rasterize('<script>throw Error("bad")</script>', 'Original <b>text</b>', '', None, photo)
        for name, width in (('review-desktop.png', 792), ('review-mobile.png', 390)):
            with Image.open(io.BytesIO(rendered[name])) as result:
                self.assertEqual(result.width, width)
                self.assertGreater(result.height, 200)


if __name__ == '__main__':
    unittest.main()
