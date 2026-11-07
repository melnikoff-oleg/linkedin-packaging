"""Reference-slot edge cases and backward-compatible fixture entry points."""
import copy
import hashlib
import html
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from linkedin_pack.reference_group_a import REFERENCE_CONTENT, render_diandraescobar
from scripts import build_reference_pack, build_test_pack


def context():
    return {'brief':{'name':'Kal Walkden','reference_content':copy.deepcopy(REFERENCE_CONTENT['diandraescobar'])},
            'esc':html.escape,'photo':'fixture-photo',
            'logo':lambda key,w,h,color=None:f'<img data-key="{key}" width="{w}" height="{h}">'}


class EmptyReferenceSlotTests(unittest.TestCase):
    def test_unavailable_diandra_card_keeps_an_empty_reserved_slot(self):
        ctx=context();ctx['brief']['reference_content']['cards'][2]={'company':'','role':'','text':''}
        body,css=render_diandraescobar(ctx)
        self.assertIn('class="a-diandra-card a-diandra-card-2" data-empty-proof-slot="true"',body)
        self.assertIn('visibility:hidden',body)
        self.assertEqual(body.count('class="a-diandra-card a-diandra-card-'),5)
        self.assertEqual(body.count('career result'),4)
        self.assertNotIn('>F</span><span><b></b>',body)

    def test_blank_company_does_not_silently_hide_supplied_case_text(self):
        ctx=context();ctx['brief']['reference_content']['cards'][0]={'company':'','role':'','text':'A source-backed working method'}
        body,_=render_diandraescobar(ctx)
        self.assertIn('A source-backed working method',body)
        self.assertNotIn('data-empty-proof-slot',body)

    def test_nonempty_fixture_html_and_css_remain_byte_identical(self):
        ctx=context()
        # Freeze the original input: later authorized copy revisions must not
        # invalidate this regression for the empty-slot rendering change.
        ctx['brief']['reference_content']={
            'brand':'W27','title':['Your','Fractional','CTO'],
            'support':'Former engineering leader at',
            'logos':['2839269','1167899','forevercar'],
            'cards':[
                {'company':'Factor','role':'Former CTO','text':'Daily peak outages ended\nwithout a full rewrite.'},
                {'company':'Double Good','role':'Former VP','text':'Release throughput up ~30%.'},
                {'company':'ForeverCar','role':'Former CTO','text':'From >5 minutes to <5 seconds\nfor vehicle-protection quotes.'},
                {'company':'Double Good','role':'Former VP','text':'AI-assisted QA workflows:\n~25% less testing effort.'},
                {'company':'Factor','role':'Former CTO','text':'~7× scale in under nine months.'},
            ],
        }
        body,css=render_diandraescobar(ctx)
        self.assertEqual(hashlib.sha256((body+'\n'+css).encode()).hexdigest(), '094252ce10d540661c878c64ea5a0fa75d97de52087bbbc44b55438f37d3af5b')


class ReferenceFixtureDelegationTests(unittest.TestCase):
    def test_old_render_entrypoint_uses_reference_helper(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(build_test_pack,'ROOT',Path(temp)),patch.object(build_test_pack,'make_brief') as old_brief,patch.object(build_test_pack,'render_package') as old_renderer,patch.object(build_reference_pack,'render_reference',create=True,return_value=True) as current:
            self.assertTrue(build_test_pack.render('clarekitching'))
            current.assert_called_once_with('clarekitching',root=Path(temp))
            old_brief.assert_not_called();old_renderer.assert_not_called()

    def test_reference_helper_prefers_current_photos_and_builds_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'test_account/results/mattgray1';folder.mkdir(parents=True)
            for name in ('portrait-reference.png','banner-photo-reference.png'):(folder/name).write_bytes(b'fixture')
            with patch.object(build_reference_pack,'prepare',return_value={'layout_mode':'reference-faithful'}) as prepare,patch.object(build_reference_pack,'render_package',return_value={'passed':True}) as render,patch.object(build_reference_pack,'comparisons') as comparisons:
                self.assertTrue(build_reference_pack.render_reference('mattgray1',root=root))
            prepare.assert_called_once_with('mattgray1',root=root)
            self.assertEqual(render.call_args.args[1],folder/'portrait-reference.png')
            self.assertEqual(render.call_args.kwargs['banner_photo_path'],folder/'banner-photo-reference.png')
            self.assertEqual(render.call_args.kwargs['background_path'],root/'test_account/source/mountain-background-reference.png')
            comparisons.assert_called_once_with('mattgray1',root=root)

if __name__=='__main__':unittest.main()
