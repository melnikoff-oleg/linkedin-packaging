import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import build_test_pack


class SampleRunnerTests(unittest.TestCase):
    def test_missing_style_is_a_failed_run(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build_test_pack,'ROOT',Path(folder)):
            self.assertEqual(build_test_pack.main(['--render-only','--style','clarekitching']),1)

    def test_failed_quality_check_is_a_failed_run(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build_test_pack,'ROOT',Path(folder)):
            target=Path(folder)/'test_account/results/clarekitching'
            target.mkdir(parents=True);(target/'portrait-master.png').write_bytes(b'fixture')
            with patch.object(build_test_pack,'render',return_value=False):
                self.assertEqual(build_test_pack.main(['--render-only','--style','clarekitching']),1)

    def test_generation_error_is_a_failed_run(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build_test_pack,'ROOT',Path(folder)):
            with patch.object(build_test_pack,'generate',side_effect=RuntimeError('test failure')):
                self.assertEqual(build_test_pack.main(['--style','clarekitching','--workers','1']),1)
