from __future__ import annotations

import tempfile
import unittest
import hashlib
from pathlib import Path

from quality_loop import QualityLoop


def complete_intake() -> dict:
    return {
        "operation_id": "op-create-001",
        "actor_id": "owner-001",
        "role": "owner",
        "invocation_id": "inv-owner-001",
        "case_id": "QMS-0001",
        "owner": "owner-001",
        "baseline": {
            "purpose": "要求に対する品質を確認する",
            "intended_use": {
                "users": "開発者・レビュアー",
                "environment": "ローカル検証環境",
                "operational_context": "機能追加に伴う品質検証",
            },
            "risk_context": {
                "criticality": "medium",
                "safety_impact": "なし",
                "data_integrity_impact": "低",
                "security_context": "内部テスト",
            },
            "requirements": [
                {"requirement_id": "REQ-001", "text": "結果を再現できる"}
            ],
            "acceptance_criteria": ["再現Evidenceがある"],
            "exclusions": [],
            "targets": ["artifact.txt"],
            "target_revision": "r1",
        },
        "implementation_authorization": {
            "allowed": False,
            "finding_ids": [],
            "allowed_targets": [],
        },
        "change_observation": {
            "method": "finite-manifest",
            "scope": ["artifact.txt"],
            "baseline_evidence_id": None,
            "exclusions": [],
            "limitations": [],
        },
    }


class CreateCaseTest(unittest.TestCase):
    def test_owner_creates_revision_one_and_reviewer_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))

            result = loop.create_case(complete_intake())

            self.assertEqual("ok", result["status"])
            self.assertEqual("QMS-0001", result["case_id"])
            self.assertEqual(1, result["case_revision"])
            self.assertTrue(result["state_changed"])
            self.assertEqual("reviewer", result["next_role"])
            self.assertEqual("review", result["next_action"])
            self.assertEqual("issued", result["handoff"]["status"])
            self.assertEqual(1, result["handoff"]["issued_revision"])
            self.assertTrue(
                (Path(temp_dir) / "QMS-0001" / "case.json").is_file()
            )


class ReviewTest(unittest.TestCase):
    def test_reviewer_records_finding_and_hands_off_to_implementer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            finding = {
                "finding_id": "F-001",
                "classification": "requirement-violation",
                "severity": "high",
                "requirement_ref": "REQ-001",
                "observed_fact": "再現手順が記録されていない",
                "impact": "第三者が結果を再現できない",
                "expected_state": "再現手順が成果物に記録されている",
                "verification_method": "記載された手順を別環境で実行する",
                "evidence_refs": [],
                "status": "open",
            }

            result = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [finding],
                    "evidence": [],
                },
            )

            self.assertEqual(2, result["case_revision"])
            self.assertEqual("implementer", result["next_role"])
            self.assertEqual("submit-plan", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("F-001", case["findings"][0]["finding_id"])
            self.assertEqual("implementer-plan", case["case_metadata"]["status"])

    def test_reviewer_records_low_finding_and_hands_off_to_direct_response(self) -> None:
        """Low指摘（plan_required=False）の場合は直接submit-responseへ遷移可能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())

            finding = {
                "finding_id": "F-002",
                "classification": "requirement-violation",
                "severity": "low",
                "plan_required": False,
                "requirement_ref": "REQ-001",
                "observed_fact": "軽微なtypo",
                "impact": "誤字",
                "expected_state": "正しい表記",
                "verification_method": "目視",
                "evidence_refs": [],
                "status": "open",
            }

            result = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-002",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [finding],
                    "evidence": [],
                },
            )

            self.assertEqual(2, result["case_revision"])
            self.assertEqual("implementer", result["next_role"])
            self.assertEqual("submit-response", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("implementer-action", case["case_metadata"]["status"])


class SubmitResponseTest(unittest.TestCase):
    def test_authorized_fix_with_integrity_evidence_moves_to_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": ["artifact.txt"],
            }
            created = loop.create_case(intake)
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "再現手順がない",
                            "impact": "再現できない",
                            "expected_state": "手順がある",
                            "verification_method": "手順を実行する",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            # Plan Before Fix: submit-plan and review-plan
            planned = loop.submit_plan(
                "QMS-0001",
                {
                    "operation_id": "op-plan-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "再現手順がない",
                            "disposition_intent": "fix",
                            "proposed_actions": ["手順を追記する"],
                        }
                    ],
                },
            )
            plan_reviewed = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-rev-plan-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-002",
                    "previous_handoff_id": planned["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "手順追記の方針を承認",
                        }
                    ],
                },
            )

            evidence_path = Path(temp_dir) / "QMS-0001" / "evidence" / "fix.txt"
            evidence_path.write_text("修正後テスト: passed\n", encoding="utf-8")
            digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()

            result = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-submit-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-002",
                    "previous_handoff_id": plan_reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["artifact.txt"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "再現手順を追記した",
                            "evidence_refs": ["EV-FIX-001"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-FIX-001",
                            "level": "observed",
                            "target_revision": "r1-fixed",
                            "method": "修正後テスト",
                            "result": "passed",
                            "path": "evidence/fix.txt",
                            "sha256": digest,
                        }
                    ],
                },
            )

            self.assertEqual(5, result["case_revision"])
            self.assertEqual("reviewer", result["next_role"])
            self.assertEqual("verify", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("reviewer-verification", case["case_metadata"]["status"])
            self.assertEqual(["artifact.txt"], case["responses"][0]["changed_targets"])


class VerifyTest(unittest.TestCase):
    def test_independent_verification_and_change_observation_move_to_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": ["artifact.txt"],
            }
            created = loop.create_case(intake)
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "再現手順がない",
                            "impact": "再現できない",
                            "expected_state": "手順がある",
                            "verification_method": "手順を実行する",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            # Plan Before Fix: submit-plan and review-plan
            planned = loop.submit_plan(
                "QMS-0001",
                {
                    "operation_id": "op-plan-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "再現手順がない",
                            "disposition_intent": "fix",
                            "proposed_actions": ["手順を追記する"],
                        }
                    ],
                },
            )
            plan_reviewed = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-rev-plan-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-002",
                    "previous_handoff_id": planned["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "手順追記の方針を承認",
                        }
                    ],
                },
            )

            evidence_path = Path(temp_dir) / "QMS-0001" / "evidence" / "fix.txt"
            evidence_path.write_text("修正後テスト: passed\n", encoding="utf-8")
            submitted = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-submit-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-003",
                    "previous_handoff_id": plan_reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["artifact.txt"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "再現手順を追記した",
                            "evidence_refs": ["EV-FIX-001"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-FIX-001",
                            "level": "observed",
                            "target_revision": "r1-fixed",
                            "method": "修正後テスト",
                            "result": "passed",
                            "path": "evidence/fix.txt",
                            "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                        }
                    ],
                },
            )

            result = loop.verify(
                "QMS-0001",
                {
                    "operation_id": "op-verify-001",
                    "actor_id": "reviewer-002",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-003",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "独立実行で受入基準を満たした",
                            "evidence_refs": ["EV-VERIFY-001"],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": {
                        "method": "finite-manifest",
                        "scope": ["artifact.txt"],
                        "before_evidence_id": "EV-OBS-BEFORE",
                        "after_evidence_id": "EV-OBS-AFTER",
                        "observed_changed_targets": ["artifact.txt"],
                        "limitations": [],
                    },
                    "evidence": [
                        {
                            "evidence_id": "EV-VERIFY-001",
                            "level": "reproduced",
                            "target_revision": "r1-fixed",
                            "method": "別Invocationで再現手順を実行",
                            "result": "passed",
                            "summary": "受入基準を満たした",
                        },
                        {
                            "evidence_id": "EV-OBS-BEFORE",
                            "level": "observed",
                            "target_revision": "r1",
                            "method": "変更前manifest",
                            "result": "captured",
                            "summary": "artifact.txtの変更前hash",
                        },
                        {
                            "evidence_id": "EV-OBS-AFTER",
                            "level": "observed",
                            "target_revision": "r1-fixed",
                            "method": "変更後manifest",
                            "result": "captured",
                            "summary": "artifact.txtの変更後hash",
                        },
                    ],
                },
            )

            self.assertEqual(6, result["case_revision"])
            self.assertEqual("owner", result["next_role"])
            self.assertEqual("adjudicate", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("verified", case["findings"][0]["status"])
            self.assertEqual(1, case["case_metadata"]["cycle_count"])

    def test_qa_can_self_correct_with_finding_withdrawn(self) -> None:
        """Implementerの反論Evidenceにより、Reviewerが指摘をfinding-withdrawnとして自己訂正し、Owner裁定へ進む"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "仕様未達に見える",
                            "impact": "動作不能",
                            "expected_state": "仕様達成",
                            "verification_method": "ログ確認",
                            "evidence_refs": [],
                            "status": "open",
                            "plan_required": True,
                        }
                    ],
                    "evidence": [],
                },
            )
            # Implementer submits evidence rebuttal via submit_plan (disagree-with-evidence)
            planned = loop.submit_plan(
                "QMS-0001",
                {
                    "operation_id": "op-plan-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "仕様未達との指摘だが、別ログで正常性が証明されている",
                            "disposition_intent": "disagree-with-evidence",
                            "proposed_actions": ["反証ログを提示し、修正は行わない"],
                            "evidence_refs": ["EV-REBUTTAL-001"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-REBUTTAL-001",
                            "level": "observed",
                            "target_revision": "r1",
                            "method": "ログ確認",
                            "result": "正常動作を確認",
                            "summary": "仕様を満たしているログ",
                        }
                    ],
                },
            )
            # Reviewer self-corrects during review_plan and withdraws the finding
            plan_review_result = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-rev-plan-001",
                    "actor_id": "reviewer-002",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-002",
                    "previous_handoff_id": planned["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "finding-withdrawn",
                            "rationale": "反証ログを確認し、指摘の前提が不成立であったため撤回",
                            "evidence_refs": ["EV-REBUTTAL-001"],
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("owner", plan_review_result["next_role"])
            self.assertEqual("adjudicate", plan_review_result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("finding-withdrawn", case["findings"][0]["status"])


class AdjudicateTest(unittest.TestCase):
    def test_owner_accepts_only_after_effectiveness_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": [],
            }
            created = loop.create_case(intake)
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "low",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "説明が不足している",
                            "impact": "再現条件を判断できない",
                            "expected_state": "再現条件が説明されている",
                            "verification_method": "説明を独立確認する",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-submit-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "accepted",
                            "rationale": "要求解釈に合意する",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            verified = loop.verify(
                "QMS-0001",
                {
                    "operation_id": "op-verify-001",
                    "actor_id": "reviewer-002",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-002",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "説明が要求を満たすことを確認した",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                },
            )

            result = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": verified["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "decision": "accepted",
                    "rationale": "受入基準と有効性確認Evidenceが揃った",
                    "conditions": [],
                    "residual_risks": [],
                    "dry_run": False,
                    "confirm": True,
                },
            )

            self.assertEqual(5, result["case_revision"])
            self.assertIsNone(result["next_role"])
            self.assertIsNone(result["next_action"])
            self.assertEqual("terminal", result["handoff"]["status"])
            self.assertEqual("accepted", loop.store.load("QMS-0001")["case_metadata"]["status"])


class StatusTest(unittest.TestCase):
    def test_status_is_read_only_and_can_write_noncanonical_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            loop.create_case(complete_intake())
            case_path = Path(temp_dir) / "QMS-0001" / "case.json"
            before = hashlib.sha256(case_path.read_bytes()).hexdigest()

            result = loop.status("QMS-0001", resume_format="markdown")

            after = hashlib.sha256(case_path.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertFalse(result["state_changed"])
            self.assertEqual("reviewer-action", result["current_state"])
            self.assertEqual("review", result["next_action"])
            self.assertEqual("create-case", result["last_completed_operation"])
            resume_path = Path(temp_dir) / "QMS-0001" / "resume.md"
            self.assertTrue(resume_path.is_file())
            self.assertIn("**次の操作**: review", resume_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
