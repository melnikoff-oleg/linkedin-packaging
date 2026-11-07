"""Distribution boundaries and exact-index reproducibility, using synthetic data."""
import base64
import io
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.build_public_download import REQUIRED, ReleaseError, build_bytes


class PublicDownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        for name in REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('KIE_AI_API_KEY=your_kie_key\n' if name == '.env.example' else 'public source\n')
        os.chmod(self.root / 'setup.sh', 0o755)
        self.git('add', '.')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True).stdout

    def test_repeatable_zip_reads_staged_bytes_and_preserves_executable(self):
        (self.root / 'README.md').write_text('working copy differs\n')
        (self.root / '.env').write_text('KIE_AI_API_KEY=private-local-value\n')
        first, manifest = build_bytes(self.root, environment={})
        second, again = build_bytes(self.root, environment={})
        self.assertEqual(first, second)
        self.assertEqual(manifest, again)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(archive.read('linkedin-packaging/README.md'), b'public source\n')
            self.assertNotIn('linkedin-packaging/.env', archive.namelist())
            self.assertTrue(all(name.startswith('linkedin-packaging/') for name in archive.namelist()))
            self.assertEqual((archive.getinfo('linkedin-packaging/setup.sh').external_attr >> 16) & 0o777, 0o755)
        self.assertEqual(manifest['file_count'], len(REQUIRED))
        self.assertIsNone(manifest['source_commit'])

    def test_force_staged_private_file_is_refused_instead_of_silently_omitted(self):
        (self.root / '.env').write_text('placeholder\n')
        self.git('add', '-f', '.env')
        with self.assertRaises(ReleaseError) as caught:
            build_bytes(self.root, environment={})
        self.assertTrue(any(path == '.env' for path, _ in caught.exception.issues))

    def test_known_encoded_credential_and_nested_archives_are_refused(self):
        secret = 'private-' + 'a' * 30
        (self.root / 'unexpected.txt').write_bytes(base64.b64encode(secret.encode()))
        self.git('add', 'unexpected.txt')
        with self.assertRaises(ReleaseError) as caught:
            build_bytes(self.root, environment={'KIE_AI_API_KEY': secret})
        self.assertTrue(any(reason == 'known credential or encoded variant' for _, reason in caught.exception.issues))
        self.git('rm', '--cached', 'unexpected.txt')
        with zipfile.ZipFile(self.root / 'nested.zip', 'w') as archive:
            archive.writestr('harmless.txt', 'public')
        self.git('add', 'nested.zip')
        with self.assertRaises(ReleaseError):
            build_bytes(self.root, environment={})

    def test_links_and_unlicensed_font_files_cannot_enter_the_download(self):
        (self.root / 'shortcut').symlink_to('README.md')
        self.git('add', 'shortcut')
        with self.assertRaises(ReleaseError):
            build_bytes(self.root, environment={})
        self.git('rm', '--cached', 'shortcut')
        (self.root / 'commercial.woff2').write_bytes(b'not-a-real-font')
        self.git('add', 'commercial.woff2')
        with self.assertRaises(ReleaseError) as caught:
            build_bytes(self.root, environment={})
        self.assertTrue(any('font' in reason for _, reason in caught.exception.issues))

    def test_missing_agent_instructions_block_incomplete_release(self):
        self.git('rm', '--cached', 'CLAUDE.md')
        with self.assertRaises(ReleaseError) as caught:
            build_bytes(self.root, environment={})
        self.assertIn(('CLAUDE.md', 'required agent release file is not staged'), caught.exception.issues)


if __name__ == '__main__':
    unittest.main()
