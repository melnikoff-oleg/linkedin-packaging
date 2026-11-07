"""Source-role aliases keep truthful reference copy scoped to its actual case."""
import unittest
from linkedin_pack.evidence import validate_specificity

from linkedin_pack.reference_layout import registry


def plan(headline, content=None):
    return {'layout_mode': 'reference-faithful', 'headline': headline,
            'reference_content': content or {'title': 'Technology leadership'},
            'proof_cards': []}


def profile():
    return {'experience': [
        {'companyName': 'Factor_', 'companyId': 'factor',
         'position': 'Chief Technology Officer [Factor 75 - Acquired by HelloFresh]',
         'description': 'An incremental rebuild eliminated daily outages and enabled ~7x scale.'},
        {'companyName': 'HelloFresh', 'companyId': 'parent',
         'position': 'Head of US Consumer Growth', 'description': 'Led engineering.'},
        {'companyName': 'Double Good', 'companyId': 'double',
         'position': 'VP Engineering', 'description': 'Improved release throughput ~30%.'},
        {'companyName': 'CUNA Mutual Group', 'companyId': 'cuna',
         'position': 'Chief Technology Officer (ForeverCar)',
         'description': '(CTO @ ForeverCar - Acquired by CUNA) An internal pricing engine delivered quotes in <5 seconds and improved conversion ~10x.'},
        {'companyName': 'Wood Mackenzie', 'companyId': 'wood',
         'position': 'VP of Product Engineering [Digital H2O]',
         'description': '(Digital H2O was acquired by Genscape) A spreadsheet prototype became a SaaS platform that reached profitability and acquisition.'},
    ]}


class ReferenceSpecificityTests(unittest.TestCase):
    def test_all_reference_shapes_accept_subject_scoped_evidence(self):
        source = {'experience': [{'companyName': 'Northstar', 'companyId': 'northstar',
                  'position': 'Engineering lead',
                  'description': 'Reduced release time by 35% using automated checks.'}]}
        def empty_slots(value):
            if isinstance(value, dict):
                return {key: empty_slots(item) for key, item in value.items()}
            if isinstance(value, list):
                return [empty_slots(item) for item in value]
            return '' if isinstance(value, str) else value
        for style, (_, content, _) in registry().items():
            with self.subTest(style=style):
                candidate = plan('Engineering lead at Northstar: 35% less release time.',
                                 empty_slots(content))
                candidate['selected_style'] = style
                result = validate_specificity(candidate, source)
                self.assertEqual(result['status'], 'passed')
                self.assertIn('northstar', result['retained_company_ids'])

    def test_source_punctuation_and_explicit_role_alias_both_identify_factor(self):
        for name in ('Factor', 'Factor75', 'Factor 75'):
            with self.subTest(name=name):
                self.assertEqual(validate_specificity(plan(f'{name}: ~7× scale'), profile())['status'], 'passed')

    def test_same_product_profile_and_supplement_metrics_can_share_one_clause(self):
        supplements = [{'company': 'ForeverCar', 'company_id': '', 'role': 'Former CTO',
                        'description': 'The quote engine fell from >5 minutes to <5 seconds.',
                        'source': 'https://example.com/forevercar'}]
        result = validate_specificity(plan('ForeverCar: >5 minutes to <5 seconds, ~10× conversion'),
                                      profile(), supplemental_evidence=supplements)
        self.assertEqual(result['status'], 'passed')

    def test_acquired_and_acquisition_preserve_the_same_named_story(self):
        self.assertEqual(validate_specificity(plan('Digital H2O: spreadsheet to acquired software'),
                                             profile())['status'], 'passed')

    def test_wrong_company_metric_still_rejected_in_headline_and_card(self):
        for content in (None, {'cards': [{'company': 'Factor', 'text': '~30% more releases'}]}):
            with self.subTest(content=content):
                candidate = plan('Factor: ~30% more releases' if content is None else 'Technology leader', content)
                with self.assertRaisesRegex(ValueError, 'company source'):
                    validate_specificity(candidate, profile())

    def test_acquirer_does_not_inherit_child_case_metrics(self):
        for name, metric in (('HelloFresh', '~7×'), ('CUNA Mutual Group', '~10×')):
            for content in (None, {'cards': [{'company': name, 'text': metric + ' growth'}]}):
                with self.subTest(name=name, content=content):
                    candidate = plan(name + ': ' + metric + ' growth' if content is None else 'Technology leader', content)
                    with self.assertRaises(ValueError):
                        validate_specificity(candidate, profile())

    def test_incidental_description_brand_and_substring_are_not_aliases(self):
        source = profile()
        source['experience'][0]['description'] += ' Discussed architecture with ClientCo.'
        for name in ('ClientCo', 'Factorial'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_specificity(plan(name + ': ~7× scale'), source)

    def test_bare_aliases_and_generic_copy_do_not_count_as_retained_case(self):
        with self.assertRaisesRegex(ValueError, 'discarded'):
            validate_specificity(plan('Former CTO at Factor and ForeverCar'), profile())

    def test_role_function_team_and_region_qualifiers_keep_employer_evidence(self):
        for qualifier in ('Platform', 'Infrastructure', 'Platform Team', 'Team',
                          'Region', 'EMEA', 'US Consumer Growth', 'Infrastructure - APAC', 'Core'):
            with self.subTest(qualifier=qualifier):
                source = {'experience': [{'companyName': 'Acme', 'companyId': 'acme',
                         'position': f'VP Engineering ({qualifier})',
                         'description': 'Increased request throughput ~7x.'}]}
                result = validate_specificity(plan('Acme: ~7× request throughput'), source)
                self.assertEqual(result['status'], 'passed')
                self.assertEqual(result['retained_company_ids'], ['acme'])

    def test_role_scope_qualifier_cannot_be_used_as_a_company_case(self):
        source = {'experience': [{'companyName': 'Acme', 'companyId': 'acme',
                  'position': 'VP Engineering (Platform)',
                  'description': 'Increased request throughput ~7x.'}]}
        for content in (None, {'cards': [{'company': 'Platform', 'text': '~7× request throughput'}]}):
            with self.subTest(content=content):
                candidate = plan('Platform: ~7× request throughput' if content is None else 'Technology leader', content)
                with self.assertRaises(ValueError):
                    validate_specificity(candidate, source)
