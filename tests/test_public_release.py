"""Synthetic tests for publication safeguards; never use real credentials."""
import base64
import io
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.check_public_release import encoded_values, load_known_values, scan_blob, candidate_files


class PublicReleaseTests(unittest.TestCase):
    def test_all_local_values_survive_precedence_and_placeholders_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = 'local-' + 'a' * 24
            second = 'local-' + 'b' * 24
            third = 'environment-' + 'c' * 24
            (root / 'api_keys.md').write_text('KIE_AI_API_KEY=' + first + '\n')
            (root / '.env').write_text('KIE_AI_API_KEY=' + second + '\nAPIFY_API_KEY=your_apify_token\n')
            (root / '.env.backup').write_text('KIE_AI_API_KEY=' + first + '\n')
            values = load_known_values([root], {'KIE_AI_API_KEY': third})
            self.assertEqual(values, {first, second, third})

    def test_known_credentials_are_found_raw_encoded_and_inside_archives(self):
        secret = 'synthetic-' + 'private' * 4
        variants = encoded_values({secret})
        self.assertTrue(scan_blob('capture.txt', secret.encode(), variants))
        self.assertTrue(scan_blob('capture.txt', base64.b64encode(secret.encode()), variants))
        self.assertTrue(scan_blob('capture.txt', ''.join('%%%02X' % ord(c) for c in secret).encode(), variants))
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('nested.txt', secret)
        self.assertTrue(any(name.endswith('!nested.txt') for name, _ in scan_blob('files.zip', data.getvalue(), variants)))

    def test_real_looking_tokens_and_private_paths_are_independently_flagged(self):
        token = ('apify_' + 'api_' + 'x' * 32).encode()
        self.assertTrue(scan_blob('capture.txt', token, set()))
        self.assertTrue(scan_blob('.env.backup', b'ignored-placeholder', set()))
        self.assertTrue(scan_blob('download.zip!.env', b'ignored-placeholder', set()))
        self.assertFalse(scan_blob('.env.example', b'KIE_AI_API_KEY=your_kie_key\n', set()))

    def test_index_scan_reads_staged_content_instead_of_changed_working_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
            path = root / 'sample.txt'
            path.write_text('staged-content')
            subprocess.run(['git', '-C', str(root), 'add', 'sample.txt'], check=True, capture_output=True)
            path.write_text('different-working-content')
            self.assertEqual(list(candidate_files(root, staged=True)), [('sample.txt', b'staged-content')])
