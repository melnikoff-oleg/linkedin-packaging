"""Account boundaries and exact-artifact release gates for multi-person examples."""
import hashlib
import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from linkedin_pack.core import export_shareable, write_json
from linkedin_pack.reference_review import FILES, reference_review_passed, reference_buyer_review_passed
from scripts import build_example_pack as examples


class AccountReviewTests(unittest.TestCase):
    def test_full_preview_replacement_and_missing_hash_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            for name in examples.OUTPUT_FILES:
                (output / name).write_bytes(name.encode())
            qa = {'example_output_sha256': {name: examples.sha(output / name) for name in examples.OUTPUT_FILES}}
            self.assertTrue(examples.output_hashes_current(output, qa))
            original = qa['example_output_sha256'].pop('preview.png')
            self.assertFalse(examples.output_hashes_current(output, qa))
            qa['example_output_sha256']['preview.png'] = original
            (output / 'preview.png').write_bytes(b'Unreviewed replacement preview')
            self.assertFalse(examples.output_hashes_current(output, qa))

    def test_same_style_in_another_account_cannot_supply_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / 'examples/person-a/results/clarekitching'
            b = root / 'examples/person-b/results/clarekitching'
            for output in (a, b):
                output.mkdir(parents=True)
                for filename in (*FILES, 'brief.json', 'banner.html'):
                    (output / filename).write_bytes(filename.encode())
                write_json(output / 'qa.json', {
                    'passed': True, 'failures': [],
                    'input_sha256': {name: examples.sha(output / name) for name in ('brief.json', 'banner.html')},
                })
            reviews_a = a.parents[1] / 'reviews'
            write_json(reviews_a / 'reference-independent-01.json', {'reviews': {
                a.name: {'verdict': 'accept', 'findings': [], 'sha256': {name: examples.sha(a / name) for name in FILES}},
            }})
            write_json(reviews_a / 'reference-buyer-release-01.json', {'reviews': [{
                'style': a.name, 'verdict': 'accept', 'required_findings': [],
                'sha256': {name: examples.sha(a / name) for name in examples.BUYER_FILES},
            }]})
            with patch('linkedin_pack.reference_review.ROOT', root):
                self.assertTrue(reference_review_passed(a, reviews_dir=reviews_a))
                self.assertTrue(reference_buyer_review_passed(a, reviews_dir=reviews_a))
                self.assertFalse(reference_review_passed(b, reviews_dir=b.parents[1] / 'reviews'))
                self.assertFalse(reference_buyer_review_passed(b, reviews_dir=b.parents[1] / 'reviews'))
                (a / 'review-mobile.png').write_bytes(b'new pixels')
                self.assertFalse(reference_review_passed(a, reviews_dir=reviews_a))
                self.assertFalse(reference_buyer_review_passed(a, reviews_dir=reviews_a))

    def test_source_change_revokes_acceptance_even_when_reviewed_pixels_match(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            output = folder / 'results/clarekitching'
            write_json(folder / 'account.json', {'name': 'Person A'})
            write_json(output / 'qa.json', {'account_source_sha256': {'source/profile.json': 'original'}})
            with patch.object(examples, 'reference_review_passed', return_value=True), \
                 patch.object(examples, 'reference_buyer_review_passed', return_value=True), \
                 patch.object(examples, 'current_source_hashes', return_value={'source/profile.json': 'changed'}):
                self.assertFalse(examples.accepted(folder, 'clarekitching'))


class ExampleInputTests(unittest.TestCase):
    def test_invisible_alpha_specks_do_not_shrink_the_rendered_subject(self):
        from linkedin_pack.render import data_uri
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'cutout.png'
            image = Image.new('RGBA', (100, 200))
            image.paste((30, 40, 50, 255), (20, 10, 80, 200))
            image.putpixel((0, 0), (255, 255, 255, 1))
            image.putpixel((99, 0), (255, 255, 255, 1))
            image.putpixel((10, 2), (123, 45, 67, 1))
            image.save(path)
            before = examples.sha(path)
            uri = data_uri(path, trim_alpha=True)
            with Image.open(io.BytesIO(base64.b64decode(uri.split(',', 1)[1]))) as trimmed:
                self.assertEqual(trimmed.size, (84, 200))
                self.assertEqual(trimmed.getpixel((2, 2)), (123, 45, 67, 1))
            self.assertEqual(before, examples.sha(path))

    def test_asset_cannot_escape_the_person_source_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'source').mkdir()
            (folder / 'other.png').write_bytes(b'image')
            with self.assertRaises(ValueError):
                examples.local_asset(folder, 'source/../other.png')

    def test_missing_curated_logo_never_triggers_a_download(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            brief = {'reference_content': {'logos': ['unavailable']}}
            with patch.object(examples, 'source_brief', return_value=brief), \
                 patch.object(examples, 'enrich_brief_assets') as enrich:
                with self.assertRaisesRegex(ValueError, 'Original local logo'):
                    examples.prepare_brief(folder, {}, 'clarekitching', folder / 'results/clarekitching')
                enrich.assert_not_called()

    def test_four_file_download_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for name in examples.DOWNLOADS:
                (folder / name).write_bytes(name.encode())
            examples.deterministic_zip(folder)
            first = examples.sha(folder / 'package.zip')
            examples.deterministic_zip(folder)
            self.assertEqual(first, examples.sha(folder / 'package.zip'))
            with zipfile.ZipFile(folder / 'package.zip') as archive:
                self.assertEqual(archive.namelist(), list(examples.DOWNLOADS))

    def test_shareable_export_includes_examples_and_omits_local_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(root / 'examples/person-a/account.json', {'name': 'Person A'})
            (root / 'examples/person-a/.env').write_text('SECRET=value')
            archive_path = root / 'export.zip'
            export_shareable(root, archive_path)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn('linkedin-package/examples/person-a/account.json', archive.namelist())
                self.assertNotIn('linkedin-package/examples/person-a/.env', archive.namelist())


if __name__ == '__main__':
    unittest.main()
