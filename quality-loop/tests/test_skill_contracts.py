from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills"


class SkillContractTest(unittest.TestCase):
    def test_quality_review_has_only_reviewer_boundaries(self) -> None:
        text = (SKILL_ROOT / "quality-review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: quality-review", text)
        self.assertIn("undeclared-change-detected", text)
        self.assertIn("`verified`、`not-verified`、`unverified`", text)
        self.assertIn("Owner裁定を代行しない", text)
        self.assertIn("案件正本を直接編集せず", text)

    def test_quality_response_rejects_self_close_and_limits_role(self) -> None:
        text = (SKILL_ROOT / "quality-response" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: quality-response", text)
        self.assertIn("Role外操作として拒否", text)
        self.assertIn("`disagreed-with-evidence`", text)
        self.assertIn("Reviewerの`verify`", text)
        self.assertIn("案件正本`case.json`", text)
        self.assertIn("直接編集せず", text)

    def test_skill_evals_are_valid_and_have_safety_coverage(self) -> None:
        expected_names = {
            "quality-review": ["申告外の", "実機は利用できず"],
            "quality-response": ["実装許可はfalse", "closedへ変更"],
        }
        for skill_name, expected_terms in expected_names.items():
            path = SKILL_ROOT / skill_name / "evals" / "evals.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(skill_name, payload["skill_name"])
            self.assertEqual(2, len(payload["evals"]))
            prompts = "\n".join(item["prompt"] for item in payload["evals"])
            for term in expected_terms:
                self.assertIn(term, prompts)


if __name__ == "__main__":
    unittest.main()
