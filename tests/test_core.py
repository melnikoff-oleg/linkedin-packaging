import json
import tempfile
import unittest
from pathlib import Path

from linkedin_pack.core import load_keys, validate_brief, safe_slug, export_shareable


def brief():
    return dict(name="Test Person", audience="Founders", positioning="Clear positioning",
                evidence=[dict(claim="Founder", source="Profile")], selected_style="clarekitching",
                headline="Helping founders clarify their message", banner_title="Clarity for\nfounders.",
                banner_subtitle="Positioning with purpose", proof_points=["Founder"],
                cta="Start a conversation", portrait_prompt="Keep the same face", rationale="Aligned audience")


class CoreTests(unittest.TestCase):
    def test_headline_limit_is_enforced_not_silently_truncated(self):
        data = brief()
        data["headline"] = "x" * 221
        with self.assertRaisesRegex(ValueError, "headline"):
            validate_brief(data)

    def test_proof_requires_supporting_evidence(self):
        data = brief()
        data["evidence"] = []
        with self.assertRaisesRegex(ValueError, "evidence"):
            validate_brief(data)

    def test_proof_card_can_omit_subordinate_detail_but_not_its_visible_result(self):
        data=brief()
        data['proof_points']=[]
        data['proof_cards']=[dict(company_id='123',company='Example',role='Former CTO',
                                  value='Quotes in <5 sec',detail='',source='Profile experience')]
        self.assertIs(validate_brief(data),data)
        data['proof_cards'][0]['value']=' '
        with self.assertRaisesRegex(ValueError,'proof_cards value'):
            validate_brief(data)

    def test_modern_brief_cannot_hide_legacy_proof_points_even_with_no_cards(self):
        for cards in ([],[dict(company_id='123',company='Example',role='Former CTO',value='Named work',detail='',source='Profile')]):
            with self.subTest(cards=bool(cards)):
                data=brief();data['proof_cards']=cards
                with self.assertRaisesRegex(ValueError,'proof_points must be empty'):
                    validate_brief(data)
                data['proof_points']=[]
                self.assertIs(validate_brief(data),data)

    def test_safe_slug_rejects_path_traversal(self):
        for value in ["../secrets", "a/b", "", "/tmp", "test<"]:
            with self.assertRaises(ValueError):
                safe_slug(value)
        self.assertEqual(safe_slug("kal-walkden"), "kal-walkden")

    def test_key_loading_does_not_mutate_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".env").write_text("KIE_AI_API_KEY='local'\n")
            self.assertEqual(load_keys(root, env={})["KIE_AI_API_KEY"], "local")
            self.assertEqual(load_keys(root, env={"KIE_AI_API_KEY": "env"})["KIE_AI_API_KEY"], "env")

    def test_example_placeholders_do_not_shadow_existing_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'api_keys.md').write_text('KIE_AI_API_KEY=existing-key\n')
            (root/'.env').write_text('KIE_AI_API_KEY=your_kie_key\n')
            self.assertEqual(load_keys(root,env={})['KIE_AI_API_KEY'],'existing-key')

    def test_share_export_excludes_keys_and_caches_even_nested(self):
        import zipfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("Read me")
            (root / "api_keys.md").write_text("secret")
            (root / ".env").write_text("secret")
            (root / ".env.example").write_text("KEY=placeholder")
            (root / "references").mkdir()
            (root / "references" / "api_keys.md").write_text("secret")
            (root / "references" / "analysis.md").write_text("Reference analysis")
            out = export_shareable(root, root / "dist" / "share.zip")
            with zipfile.ZipFile(out) as z:
                names = z.namelist()
                self.assertIn("linkedin-package/README.md", names)
                self.assertIn("linkedin-package/.env.example", names)
                self.assertFalse(any(n.endswith("api_keys.md") or n.endswith("/.env") for n in names))


if __name__ == "__main__":
    unittest.main()
