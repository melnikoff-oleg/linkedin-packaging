import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from scripts import finalize_test_pack
from linkedin_pack.render import audit_design_details


class FinalizationTests(unittest.TestCase):
    def test_finalizer_refuses_missing_or_failed_design_qa_before_writing_gallery(self):
        reports=[
            None,
            {'passed':True,'failures':[]},
            {'passed':True,'failures':[], 'design_details':{'status':'failed','failures':['Unreadable text']}},
            {'passed':True,'failures':[], 'design_details':{'status':'passed','failures':['Glyph overlap']}},
            {'passed':False,'failures':['Overflow'], 'design_details':{'status':'passed','failures':[]}},
        ]
        for report in reports:
            with self.subTest(report=report),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);folder=root/'test_account/results/example';folder.mkdir(parents=True)
                if report is not None:(folder/'qa.json').write_text(json.dumps(report))
                with patch.object(finalize_test_pack,'ROOT',root),patch.object(finalize_test_pack,'STYLES',{'example':{'name':'Example'}}),patch.object(finalize_test_pack,'review_passed',return_value=True),patch.object(finalize_test_pack,'build_gallery') as gallery:
                    with self.assertRaisesRegex(SystemExit,'technical/design QA'):
                        finalize_test_pack.main()
                    gallery.assert_not_called()

    def test_finalizer_rejects_retina_mobile_input_as_native_review_evidence(self):
        design=audit_design_details({'status':'measured','text':[{'text':'Clear outcome','kind':'headline','font_size':60,'ink':{'x':540,'y':40,'width':400,'height':60}}],
                                     'title_lines':[],'cards':[],'logos':[],'content_proof':None})
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);folder=root/'test_account/results/example';folder.mkdir(parents=True)
            (folder/'qa.json').write_text(json.dumps({'passed':True,'failures':[],'design_details':design}))
            Image.new('RGB',(792,600),'white').save(folder/'review-desktop.png')
            Image.new('RGB',(780,600),'white').save(folder/'review-mobile.png')
            with patch.object(finalize_test_pack,'ROOT',root),patch.object(finalize_test_pack,'STYLES',{'example':{'name':'Example'}}),patch.object(finalize_test_pack,'review_passed',return_value=True),patch.object(finalize_test_pack,'build_gallery') as gallery:
                with self.assertRaisesRegex(SystemExit,'Native review image'):
                    finalize_test_pack.main()
                gallery.assert_not_called()
