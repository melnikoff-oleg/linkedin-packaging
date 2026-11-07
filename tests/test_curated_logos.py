import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
from linkedin_pack.evidence import collect_company_logos
from tests.test_evidence import rich_profile


class CuratedLogoTests(unittest.TestCase):
    def setUp(self):
        patcher=patch('linkedin_pack.evidence._download_logo',side_effect=AssertionError('No network expected for curated assets'))
        patcher.start();self.addCleanup(patcher.stop)

    def prepare(self, root):
        folder=root/'cache/curated';folder.mkdir(parents=True)
        image=Image.new('RGBA',(160,50),(0,0,0,0))
        ImageDraw.Draw(image).rectangle((15,10,145,40),fill='black')
        raw=io.BytesIO();image.save(raw,format='PNG');raw=raw.getvalue()
        (folder/'123.png').write_bytes(raw)
        record={'company_id':'123','profile_company_name':'Factor75','company':'Factor75',
                'source_type':'official-brand-asset','source_url':'https://example.com/official.svg',
                'source_page':'https://example.com/brand','sha256':hashlib.sha256(raw).hexdigest()}
        (folder/'123.json').write_text(json.dumps(record))
        return folder,record,raw

    def test_verified_curated_transparent_asset_precedes_social_avatar(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,record,raw=self.prepare(root)
            with patch('linkedin_pack.evidence._download_logo') as download:
                assets=collect_company_logos(rich_profile(),['123'],root/'output',cache_dir=root/'cache')
            download.assert_not_called()
            self.assertEqual(assets,{'123':'logos/123.png'})
            self.assertEqual((root/'output/logos/123.png').read_bytes(),raw)
            self.assertEqual(json.loads((root/'output/logos/provenance.json').read_text())['123']['source_type'],'official-brand-asset')

    def test_curated_identity_mismatch_cannot_replace_another_company(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,record,raw=self.prepare(root)
            record['profile_company_name']='Other Company';(folder/'123.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'identity'):
                collect_company_logos(rich_profile(),['123'],root/'output',cache_dir=root/'cache')

    def test_changed_curated_image_requires_new_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,record,raw=self.prepare(root)
            (folder/'123.png').write_bytes(raw+b'changed')
            with self.assertRaisesRegex(ValueError,'hash'):
                collect_company_logos(rich_profile(),['123'],root/'output',cache_dir=root/'cache')

    def test_opaque_curated_backplate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,record,raw=self.prepare(root)
            Image.new('RGB',(160,50),'white').save(folder/'123.png')
            record['sha256']=hashlib.sha256((folder/'123.png').read_bytes()).hexdigest()
            (folder/'123.json').write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'transparen'):
                collect_company_logos(rich_profile(),['123'],root/'output',cache_dir=root/'cache')

    def test_curated_asset_works_when_profile_has_no_social_logo(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.prepare(root)
            profile=rich_profile();profile['experience'][0].pop('companyLogo')
            assets=collect_company_logos(profile,['123'],root/'output',cache_dir=root/'cache')
            self.assertEqual(assets,{'123':'logos/123.png'})
