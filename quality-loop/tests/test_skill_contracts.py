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
        self.assertIn("review-standalone", text)
        self.assertIn("standalone-review-input.schema.json", text)

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

    def test_status_guidance_keeps_results_tied_to_their_cycle(self) -> None:
        guidance = {
            "quality-qa": "references/results.md",
            "quality-review": "references/finding-guidelines.md",
            "quality-response": "references/response-guidelines.md",
            "blind-qa-cycle": "references/cloud_output_contract.md",
        }
        for skill_name, reference in guidance.items():
            with self.subTest(skill=skill_name):
                skill_text = (SKILL_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
                reference_text = (SKILL_ROOT / skill_name / reference).read_text(encoding="utf-8")
                combined = skill_text + "\n" + reference_text
                self.assertIn("対象", combined)
                self.assertIn("cycle", combined)
        qa_text = (SKILL_ROOT / "quality-qa" / "references/results.md").read_text(encoding="utf-8")
        for label in ("基準充足", "基準未達", "保留", "判定不能"):
            self.assertIn(label, qa_text)
        for value in ("UNVERIFIED", "NOT_RUN", "ERROR", "対象SHA", "--lang en"):
            self.assertIn(value, qa_text)

    def test_blind_cycle_display_is_record_based_and_mode_independent(self) -> None:
        skill_text = (SKILL_ROOT / "blind-qa-cycle" / "SKILL.md").read_text(encoding="utf-8")
        contract_text = (SKILL_ROOT / "blind-qa-cycle" / "references/cloud_output_contract.md").read_text(encoding="utf-8")
        combined = skill_text + "\n" + contract_text
        for stage in ("準備", "QA・確認", "修正", "判断待ち", "終了"):
            self.assertIn(stage, combined)
        for item in ("`00_plan.md`", "`00_invite.md`", "`STATUS.md`", "`03_machine.json`", "停止理由", "次担当", "次操作"):
            self.assertIn(item, combined)
        for language in ("`lang=ja`", "`lang=en`", "単独の`en`"):
            self.assertIn(language, skill_text)
        self.assertIn("操作モード、権限、保存記録を変えない", skill_text)
        self.assertIn("Reviewed SHA", contract_text)
        self.assertIn("cycle", contract_text)

    def test_four_skill_result_contracts_keep_gate_criteria_checks_and_recommendations_distinct(self) -> None:
        qa = (SKILL_ROOT / "quality-qa" / "references/results.md").read_text(encoding="utf-8")
        review = (SKILL_ROOT / "quality-review" / "references/finding-guidelines.md").read_text(encoding="utf-8")
        response = (SKILL_ROOT / "quality-response" / "references/response-guidelines.md").read_text(encoding="utf-8")
        blind = (SKILL_ROOT / "blind-qa-cycle" / "references/cloud_output_contract.md").read_text(encoding="utf-8")
        for text in (qa, blind):
            for value in ("PASS", "FAIL", "HOLD", "INCONCLUSIVE", "UNVERIFIED", "NOT_RUN", "ERROR"):
                self.assertIn(value, text)
            self.assertIn("対象SHA", text) if text is qa else self.assertIn("Reviewed SHA", text)
        for value in ("accept", "accept-with-conditions", "require-remediation", "defer"):
            self.assertIn(value, review)
        for value in ("accepted", "fix-submitted", "disagreed-with-evidence", "cannot-verify", "baseline-change-requested"):
            self.assertIn(value, response)
        self.assertIn("基準別", response)

    def test_formal_skills_keep_resume_outcomes_and_owner_decisions_distinct(self) -> None:
        review_text = (SKILL_ROOT / "quality-review" / "SKILL.md").read_text(encoding="utf-8")
        response_text = (SKILL_ROOT / "quality-response" / "SKILL.md").read_text(encoding="utf-8")
        for text in (review_text, response_text):
            self.assertIn("日本語", text)
            self.assertIn("再開用Markdown", text)
            for decision in ("`accepted`", "`accepted-with-risk`", "`rejected`", "`held`"):
                self.assertIn(decision, text)
        self.assertIn("Reviewer評価勧告", review_text)
        self.assertIn("Disposition", response_text)
        self.assertIn("status --format text --lang en", review_text)
        self.assertIn("status --format text --lang en", response_text)
        self.assertIn("baseline.target_revision", review_text)
        self.assertIn("baseline.target_revision", response_text)

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

    def test_qa_skill_descriptions_and_activation_cases_require_explicit_requests(self) -> None:
        for skill_name in ("quality-qa", "quality-review", "quality-response", "blind-qa-cycle"):
            with self.subTest(skill=skill_name):
                skill_text = (SKILL_ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
                frontmatter = skill_text.split("---", 2)[1]
                self.assertIn("description:", frontmatter)
                self.assertIn("現在のメッセージ", frontmatter)
                self.assertIn("明示的に依頼", frontmatter)
                self.assertIn("正例:", frontmatter)
                self.assertIn("では使用しない", frontmatter)

                eval_path = SKILL_ROOT / skill_name / "evals" / "evals.json"
                payload = json.loads(eval_path.read_text(encoding="utf-8"))
                self.assertEqual(skill_name, payload["skill_name"])
                cases = payload["activation_cases"]
                self.assertGreaterEqual(len(cases), 2)
                self.assertEqual(len(cases), len({case["id"] for case in cases}))
                for case in cases:
                    self.assertIsInstance(case["expected_trigger"], bool)
                    self.assertTrue(case["prompt"])
                    self.assertTrue(case["reason"])
                self.assertTrue(any(case["expected_trigger"] for case in cases))
                self.assertTrue(any(not case["expected_trigger"] for case in cases))

        blind_frontmatter = (SKILL_ROOT / "blind-qa-cycle" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("disable-model-invocation: true", blind_frontmatter)


if __name__ == "__main__":
    unittest.main()
