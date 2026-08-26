import unittest
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "spec-driven-qa-bundle"
sys.path.insert(0, str(ROOT))


class RoleDocsTest(unittest.TestCase):
    def test_role_docs_define_distinct_actions_and_boundaries(self):
        spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        reviewer = (ROOT / "spec-driven-qa-review/SKILL.md").read_text(encoding="utf-8")
        author = (ROOT / "spec-driven-qa-author-response/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("独立QA", reviewer)
        self.assertIn("handoff", reviewer)
        self.assertIn("Authorとして", author)
        self.assertIn("fixed-and-verified", author)
        self.assertNotEqual(reviewer, author)
        for term in ("分類", "Evidence", "状態遷移", "安全規則"):
            self.assertIn(term, spec)
        self.assertIn("../SPEC.md", reviewer)
        self.assertIn("../SPEC.md", author)

    def test_minimal_examples_are_complete_and_distinct(self):
        from shared_core.contract import validate_contract
        single = json.loads((ROOT / "examples/single-cycle.json").read_text(encoding="utf-8"))
        multi = json.loads((ROOT / "examples/multi-cycle.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_contract(single), [])
        self.assertEqual(validate_contract(multi), [])
        self.assertEqual(len(single["cycle"]), 4)
        self.assertEqual(len(multi["cycles"]), 2)

    def test_bundle_documentation_and_entrypoints_exist(self):
        for name in ("README.md", "INSTALL.md", "CHANGELOG.md", "MANIFEST.json", "evals/README.md"):
            self.assertTrue((ROOT / name).is_file(), name)
        schema_readme = (ROOT / "schemas/README.md").read_text(encoding="utf-8")
        self.assertIn("JSON Schema", schema_readme)
        self.assertTrue((ROOT.parent / "scripts/compat_cli.py").is_file())


if __name__ == "__main__":
    unittest.main()
