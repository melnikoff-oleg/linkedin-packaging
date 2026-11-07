import hashlib
import http.client
import io
import json
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from linkedin_pack.cli import build_parser
from linkedin_pack.serve import ReviewServer, archive, discover, package_info, source_files


def package(folder, name='Test person'):
    folder.mkdir(parents=True, exist_ok=True)
    for filename in ('banner.png', 'portrait.png', 'preview.png', 'preview-mobile.png'):
        (folder / filename).write_bytes(b'PNG fixture '+filename.encode())
    (folder/'headline.txt').write_text('A specific headline')
    (folder/'brief.json').write_text(json.dumps({'name':name, 'selected_style':'clarekitching'}))
    (folder/'banner.html').write_text('<html><style>@font-face{src:url(data:font/ttf;base64,AAAA)}</style><img src="portrait.png"></html>')
    (folder/'preview.html').write_text('<img src="banner.png"><img src="portrait.png">')
    (folder/'qa.json').write_text(json.dumps({'passed':True,'acceptance':'awaiting_blind_combined_profile_review'}))
    return folder


class LocalPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.folder=package(self.root/'output'/'alex')
        self.server=ReviewServer(self.root/'output',0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.port=self.server.server_port
        self.identifier=next(iter(discover(self.root/'output')))

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.temp.cleanup()

    def request(self,path,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.port)
        connection.request('GET',path,headers=headers or {})
        response=connection.getresponse()
        result=response.status,dict(response.getheaders()),response.read()
        connection.close()
        return result

    def test_cli_and_bind_are_loopback_only(self):
        args=build_parser().parse_args(['serve','--output','output','--port','0'])
        self.assertEqual(args.port,0)
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        self.assertGreater(self.port,0)
        status,_,_=self.request('/',{'Host':f'attacker.example:{self.port}'})
        self.assertEqual(status,403)
        status,headers,raw=self.request('/',{'Host':f'localhost:{self.port}'})
        self.assertEqual(status,200)
        self.assertIn(b'Your LinkedIn packaging',raw)
        self.assertEqual(headers['Cross-Origin-Resource-Policy'],'same-origin')
        self.assertNotIn('Access-Control-Allow-Origin',headers)

    def test_files_are_allowlisted_not_a_static_root(self):
        (self.folder/'.env').write_text('KIE_AI_API_KEY=private-value')
        (self.folder/'source').mkdir()
        (self.folder/'source'/'profile.json').write_text('{"secret":true}')
        for path in ('/.env','/brief.json','/api/../.env',
                     f'/asset/{self.identifier}/.env',
                     f'/asset/{self.identifier}/%2e%2e%2f.env',
                     f'/asset/{self.identifier}/source/profile.json'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0],404)
        status,headers,body=self.request(f'/asset/{self.identifier}/headline.txt')
        self.assertEqual(status,200)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(body,b'A specific headline')
        self.assertIn('attachment',headers['Content-Disposition'])

    def test_descendant_symlinks_never_export_or_discover(self):
        secret=self.root/'private.png';secret.write_bytes(b'secret')
        (self.folder/'portrait.png').unlink()
        (self.folder/'portrait.png').symlink_to(secret)
        self.assertFalse(discover(self.root/'output'))
        self.assertEqual(self.request(f'/asset/{self.identifier}/portrait.png')[0],404)
        with self.assertRaises(ValueError):
            archive(self.folder,'uploads')
        outside=package(self.root/'outside')
        (self.root/'output'/'linked').symlink_to(outside,target_is_directory=True)
        self.assertFalse(discover(self.root/'output'))

    def test_upload_archive_is_tightly_scoped(self):
        (self.folder/'.env').write_text('private')
        (self.folder/'api_keys.md').write_text('private')
        (self.folder/'raw.json').write_text('private')
        status,headers,raw=self.request(f'/download/{self.identifier}/uploads.zip')
        self.assertEqual(status,200)
        self.assertEqual(headers['Content-Type'],'application/zip')
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            self.assertEqual(set(bundle.namelist()),{'banner.png','portrait.png','headline.txt','preview.png','preview-mobile.png'})

    def test_editable_archive_follows_local_dependencies_and_omits_private_files(self):
        (self.folder/'assets').mkdir();(self.folder/'assets'/'type.ttf').write_bytes(b'font')
        (self.folder/'assets'/'style.css').write_text('@font-face {src:url("type.ttf")}')
        (self.folder/'banner.html').write_text('<link rel="stylesheet" href="assets/style.css"><img src="banner-photo-cutout.png">')
        (self.folder/'banner-photo-cutout.png').write_bytes(b'cutout')
        (self.folder/'background.png').write_bytes(b'background')
        (self.folder/'assets'/'unneeded.json').write_text('{"private":true}')
        (self.folder/'logs.txt').write_text('private')
        with zipfile.ZipFile(io.BytesIO(archive(self.folder,'sources'))) as bundle:
            names=set(bundle.namelist())
            self.assertTrue({'brief.json','banner.html','preview.html','banner-photo-cutout.png','background.png',
                             'assets/style.css','assets/type.ttf','EDITING.txt'} <= names)
            self.assertNotIn('logs.txt',names);self.assertNotIn('assets/unneeded.json',names)
            extracted=self.root/'extracted';bundle.extractall(extracted)
        # Every relative dependency is still resolvable after extraction.
        self.assertEqual(source_files(extracted)['assets/type.ttf'],b'font')

    def test_source_archive_includes_declared_logo_and_company_font_dependencies(self):
        logo=self.folder/'logos';logo.mkdir();(logo/'firm.png').write_bytes(b'logo')
        (logo/'provenance.json').write_text('{"firm":{"source":"https://example.org"}}')
        brand=self.folder/'company-brand';(brand/'fonts').mkdir(parents=True)
        font=b'\x00\x01\x00\x00font';(brand/'fonts'/'face.ttf').write_bytes(font)
        (brand/'brand.css').write_text('.banner{color:#ffffff}')
        (brand/'provenance.json').write_text('{"source":"https://example.org"}')
        manifest={'schema_version':1,'id':'example','name':'Example','website':'https://example.org',
                  'palette':{'ink':'#000000'},'fonts':[{'family':'Example','path':'fonts/face.ttf','sha256':hashlib.sha256(font).hexdigest(),'weight':'400','style':'normal','source_url':'https://example.org/font.ttf'}],
                  'typography':{'display_family':'Example','body_family':'Example'},'stylesheet':'brand.css','provenance':'provenance.json'}
        (brand/'brand.json').write_text(json.dumps(manifest));(brand/'unneeded.txt').write_text('private')
        (self.folder/'brief.json').write_text(json.dumps({'logo_assets':{'firm':'logos/firm.png'},'company_brand':{'manifest':'company-brand/brand.json'}}))
        names=set(source_files(self.folder))
        self.assertTrue({'logos/firm.png','logos/provenance.json','company-brand/brand.json','company-brand/fonts/face.ttf','company-brand/brand.css','company-brand/provenance.json'}<=names)
        self.assertNotIn('company-brand/unneeded.txt',names)

    def test_source_resources_cannot_escape_or_smuggle_credentials(self):
        for url in ('file:///tmp/private.png','https://example.org/font.ttf','../private.png',
                    '.env','assets/%2e%2e/private.png','assets/credentials.css'):
            with self.subTest(url=url):
                (self.folder/'banner.html').write_text(f'<img src="{url}">')
                with self.assertRaises(ValueError):source_files(self.folder)
        (self.folder/'assets').symlink_to(self.root,target_is_directory=True)
        (self.root/'face.ttf').write_bytes(b'font')
        (self.folder/'banner.html').write_text('<style>@font-face{src:url(assets/face.ttf)}</style>')
        with self.assertRaises(ValueError):source_files(self.folder)

    def test_revision_refresh_and_draft_status_are_current(self):
        a=json.loads(self.request('/api/packages')[2])['packages'][0]
        self.assertIn('Draft',a['status'])
        (self.folder/'headline.txt').write_text('Revised for a different audience')
        b=json.loads(self.request('/api/packages')[2])['packages'][0]
        self.assertNotEqual(a['revision'],b['revision'])
        self.assertEqual(b['headline'],'Revised for a different audience')
        (self.folder/'qa.json').write_text('{"passed":false,"acceptance":"render_in_progress"}')
        c=json.loads(self.request('/api/packages')[2])['packages'][0]
        self.assertTrue(c['updating'])
        self.assertEqual(self.request(f'/download/{self.identifier}/uploads.zip')[0],409)
        with patch('linkedin_pack.review.review_passed',return_value=True):
            (self.folder/'qa.json').write_text('{"passed":true}')
            self.assertIn('AI review passed',package_info(self.identifier,self.folder,self.root/'output')['status'])

    def test_sources_require_photo_inputs_but_not_generated_svg_backgrounds(self):
        (self.folder/'brief.json').write_text('{"selected_style":"laraacostar"}')
        self.assertFalse(package_info(self.identifier,self.folder,self.root/'output')['source_available'])
        with self.assertRaises(ValueError):source_files(self.folder)
        (self.folder/'banner-photo-cutout.png').write_bytes(b'cutout')
        self.assertTrue(package_info(self.identifier,self.folder,self.root/'output')['source_available'])
        (self.folder/'banner.html').write_text('<svg class="rfc-l-texture"><path d="M0 0"/></svg><img class="rf-matt-landscape" src="">')
        self.assertIn('banner.html',source_files(self.folder))
        (self.folder/'banner.html').write_text('<img class="rf-matt-landscape" src="data:image/png;base64,AAAA">')
        with self.assertRaises(ValueError):source_files(self.folder)
        (self.folder/'background.png').write_bytes(b'background')
        self.assertIn('background.png',source_files(self.folder))

    def test_new_revisions_sort_first_without_losing_old_versions(self):
        newer=package(self.root/'output'/'v02')
        found=list(discover(self.root/'output').values())
        self.assertEqual(found,[newer,self.folder])
        (self.folder/'headline.txt').write_text('Newest saved revision')
        self.assertEqual(list(discover(self.root/'output').values()),[self.folder,newer])

    def test_individual_uploads_are_blocked_while_rendering(self):
        (self.folder/'qa.json').write_text('{"acceptance":"render_in_progress"}')
        for name in ('banner.png','portrait.png','headline.txt'):
            self.assertEqual(self.request(f'/asset/{self.identifier}/{name}')[0],409)
        self.assertEqual(self.request(f'/asset/{self.identifier}/preview.png')[0],200)

    def test_failed_render_does_not_leave_preview_busy(self):
        from linkedin_pack.render import render_package
        def fail(*args,**kwargs):
            (self.folder/'qa.json').write_text('{"acceptance":"render_in_progress"}')
            raise ValueError('bad input')
        with patch('linkedin_pack.render._render_package',side_effect=fail):
            with self.assertRaises(ValueError):render_package({},'unused',self.folder)
        self.assertEqual(json.loads((self.folder/'qa.json').read_text())['acceptance'],'render_failed')
        state = package_info(self.identifier,self.folder,self.root/'output')
        self.assertFalse(state['updating'])
        self.assertFalse(state['downloads_ready'])
        self.assertFalse(state['source_available'])
        self.assertEqual(self.request(f'/download/{self.identifier}/uploads.zip')[0],409)
        self.assertEqual(self.request(f'/asset/{self.identifier}/portrait.png')[0],409)

    def test_user_text_is_data_not_executable_markup(self):
        (self.folder/'brief.json').write_text(json.dumps({'name':'</script><script>alert(1)</script>'}))
        body=json.loads(self.request('/api/packages')[2])['packages'][0]
        self.assertEqual(body['name'],'</script><script>alert(1)</script>')
        page=self.request('/')[2]
        self.assertNotIn(b'</script><script>alert(1)</script>',page)
        self.assertNotIn(b'innerHTML',page)

    def test_empty_directory_has_honest_waiting_state(self):
        for item in self.folder.iterdir():item.unlink()
        self.assertEqual(json.loads(self.request('/api/packages')[2])['packages'],[])


if __name__=='__main__':unittest.main()
