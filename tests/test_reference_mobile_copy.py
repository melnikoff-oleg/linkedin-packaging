"""The native mobile avatar must not cut the beginning of inset proof copy."""
import copy
import unittest

from playwright.sync_api import sync_playwright

from linkedin_pack.core import validate_brief
from linkedin_pack.evidence import _reference_logo_slots
from linkedin_pack.reference_layout import registry, reference_banner_html, MOBILE_SAFE_COPY_CSS
from linkedin_pack.reference_qa import measure_reference_design
from linkedin_pack.render import mobile_portrait_overlap


def brief(style):
    content=copy.deepcopy(registry()[style][1])
    for container,index in _reference_logo_slots(content):container[index]=''
    targets={
        'charlie-hills':'200+',
        'donnellychris':'A source-backed professional role',
        'jakezward':'ROLES / UCLA',
        'diandraescobar':'Readable career proof.',
    }
    if style=='charlie-hills':content.update(support_primary='200+',support_secondary=' accounts managed')
    if style=='donnellychris':content['support']=targets[style]
    if style=='jakezward':content['logos_label']=targets[style]
    if style=='diandraescobar':content['cards'][4]={'company':'','role':'SOURCE ROLE','text':targets[style]}
    return {'name':'Example Person','audience':'Example audience','positioning':'Source-backed role',
        'evidence':[{'claim':'Source-backed role','source':'https://example.com/profile'}],
        'selected_style':style,'headline':'Example professional role','banner_title':'Example professional role',
        'banner_subtitle':'','proof_points':[],'proof_cards':[],'cta':'','portrait_prompt':'Local photo',
        'rationale':'Native avatar-safe copy','layout_mode':'reference-faithful','reference_content':content},targets.get(style)


class ReferenceMobileCopyTests(unittest.TestCase):
    def test_opt_in_requires_a_boolean_and_supported_reference_style(self):
        for value in (0,1,'true',{},None):
            b,_=brief('charlie-hills');b['mobile_safe_copy']=value
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'mobile_safe_copy'):validate_brief(b)
        b,_=brief('adrian-kul');b['mobile_safe_copy']=True
        with self.assertRaisesRegex(ValueError,'mobile_safe_copy'):validate_brief(b)
        b,_=brief('charlie-hills');b['mobile_safe_copy']=True;b['layout_mode']='evidence';del b['reference_content']
        with self.assertRaisesRegex(ValueError,'mobile_safe_copy'):validate_brief(b)

    def test_default_output_remains_byte_identical(self):
        for style in MOBILE_SAFE_COPY_CSS:
            b,_=brief(style);baseline=reference_banner_html(b,style)
            b['mobile_safe_copy']=False
            self.assertEqual(baseline,reference_banner_html(b,style))

    def test_inset_copy_clears_avatar_without_changing_regions_or_type_sizes(self):
        with sync_playwright() as p:
            browser=p.chromium.launch();page=browser.new_page(viewport={'width':1584,'height':396})
            for style in MOBILE_SAFE_COPY_CSS:
                b,target=brief(style);states=[]
                for enabled in (False,True):
                    b['mobile_safe_copy']=enabled;validate_brief(b)
                    page.set_content(reference_banner_html(b,style));page.evaluate('document.fonts.ready')
                    states.append(measure_reference_design(page,style))
                geometry=lambda report:[{key:r[key] for key in ('slot','x','y','width','height')} for r in report['regions']]
                before=next(t for t in states[0]['text'] if t['text']==target)
                after=next(t for t in states[1]['text'] if t['text']==target)
                with self.subTest(style=style):
                    self.assertTrue(mobile_portrait_overlap(before['ink']))
                    self.assertFalse(mobile_portrait_overlap(after['ink']))
                    self.assertEqual(geometry(states[0]),geometry(states[1]))
                    self.assertEqual([(t['text'],t['font_size']) for t in states[0]['text']],[(t['text'],t['font_size']) for t in states[1]['text']])
                    self.assertEqual(states[1]['status'],'passed')
            browser.close()


if __name__=='__main__':unittest.main()
