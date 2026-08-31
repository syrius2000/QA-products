from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop


class PilotExecutionTest(unittest.TestCase):
    def test_full_pilot_lifecycle_four_stages(self) -> None:
        """実案件E2Eテスト: ドキュメント改善を対象とした4段階ライフサイクルの完全完走"""
        with tempfile.TemporaryDirectory() as temp_dir:
            case_root = Path(temp_dir)
            loop = QualityLoop(case_root)

            # 対象ファイル準備
            target_file = case_root / "README.md"
            target_file.write_text("# Target Module\n\nInitial version.\n", encoding="utf-8")
            init_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()

            # 1. Owner: create-case
            intake = {
                "operation_id": "op-create-pilot-01",
                "actor_id": "owner-yamaguchi",
                "role": "owner",
                "invocation_id": "inv-owner-01",
                "case_id": "QMS-PILOT-01",
                "owner": "owner-yamaguchi",
                "baseline": {
                    "purpose": "対象モジュールのドキュメント品質確保",
                    "intended_use": {
                        "users": "開発者・運用者",
                        "environment": "ローカル開発環境",
                        "operational_context": "CLI利用マニュアルの確認",
                    },
                    "risk_context": {
                        "criticality": "low",
                        "safety_impact": "なし",
                        "data_integrity_impact": "なし",
                        "security_context": "公開ドキュメント",
                    },
                    "requirements": [
                        {"requirement_id": "REQ-01", "text": "CLI実行例が記載されていること"},
                    ],
                    "acceptance_criteria": ["READMEにCLIコマンド構文があること"],
                    "exclusions": [],
                    "targets": [str(target_file)],
                    "target_revision": "rev-1",
                },
                "implementation_authorization": {
                    "allowed": True,
                    "finding_ids": ["F-01"],
                    "allowed_targets": [str(target_file)],
                },
                "change_observation": {
                    "method": "finite-manifest",
                    "scope": [str(target_file)],
                    "baseline_evidence_id": None,
                    "exclusions": [],
                    "limitations": [],
                },
            }

            c = loop.create_case(intake)
            self.assertEqual("reviewer-action", loop.status("QMS-PILOT-01")["current_state"])

            # 2. Reviewer: review
            r = loop.review(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-rev-pilot-01",
                    "actor_id": "reviewer-ai",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-01",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-01",
                            "observed_fact": "CLI実行例が不足している",
                            "impact": "利用者が操作方法を把握できない",
                            "expected_state": "CLI実行例が追記されていること",
                            "verification_method": "ファイル目視確認",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("implementer-plan", loop.status("QMS-PILOT-01")["current_state"])

            # 2.5 Implementer: submit-plan -> Reviewer: review-plan
            p = loop.submit_plan(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-plan-pilot-01",
                    "actor_id": "implementer-ai",
                    "role": "implementer",
                    "invocation_id": "inv-imp-plan-01",
                    "previous_handoff_id": r["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-01",
                            "understanding": "CLI実行例をドキュメントに追記する",
                            "disposition_intent": "fix",
                            "proposed_actions": ["READMEにCLI Usageセクションを追記"],
                        }
                    ],
                },
            )
            rp = loop.review_plan(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-revplan-pilot-01",
                    "actor_id": "reviewer-ai",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-plan-01",
                    "previous_handoff_id": p["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-01",
                            "outcome": "plan-accepted",
                            "rationale": "追記方針に合意",
                        }
                    ],
                },
            )
            self.assertEqual("implementer-action", loop.status("QMS-PILOT-01")["current_state"])

            # 3. Implementer: submit-response (対象ファイルを修正)
            target_file.write_text("# Target Module\n\n## CLI Usage\n`python -m module`\n", encoding="utf-8")
            mod_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()

            ev_imp_dir = case_root / "QMS-PILOT-01" / "evidence"
            ev_imp_dir.mkdir(parents=True, exist_ok=True)
            ev_diff = ev_imp_dir / "fix_diff.txt"
            ev_diff.write_text("Added CLI Usage section.\n", encoding="utf-8")
            ev_diff_hash = hashlib.sha256(ev_diff.read_bytes()).hexdigest()

            s = loop.submit_response(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-sub-pilot-01",
                    "actor_id": "implementer-ai",
                    "role": "implementer",
                    "invocation_id": "inv-imp-01",
                    "previous_handoff_id": rp["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": [str(target_file)],
                    "responses": [
                        {
                            "finding_id": "F-01",
                            "disposition": "fix-submitted",
                            "rationale": "READMEにCLI Usageセクションを追記しました",
                            "evidence_refs": ["EV-DIFF"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-DIFF",
                            "level": "observed",
                            "target_revision": "rev-2",
                            "method": "file-diff",
                            "result": "diff captured",
                            "path": "evidence/fix_diff.txt",
                            "sha256": ev_diff_hash,
                        }
                    ],
                },
            )
            self.assertEqual("reviewer-verification", loop.status("QMS-PILOT-01")["current_state"])

            # 4. Reviewer: verify (独立変更観測と検証)
            ev_before = ev_imp_dir / "before.txt"
            ev_before.write_text(f"hash: {init_hash}\n", encoding="utf-8")
            ev_before_hash = hashlib.sha256(ev_before.read_bytes()).hexdigest()

            ev_after = ev_imp_dir / "after.txt"
            ev_after.write_text(f"hash: {mod_hash}\n", encoding="utf-8")
            ev_after_hash = hashlib.sha256(ev_after.read_bytes()).hexdigest()

            v = loop.verify(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-ver-pilot-01",
                    "actor_id": "reviewer-ai",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-02",
                    "previous_handoff_id": s["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-01",
                            "result": "verified",
                            "rationale": "CLI Usageの追記とREQ-01適合を確認",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": {
                        "method": "finite-manifest",
                        "scope": [str(target_file)],
                        "before_evidence_id": "EV-B",
                        "after_evidence_id": "EV-A",
                        "observed_changed_targets": [str(target_file)],
                        "limitations": [],
                    },
                    "evidence": [
                        {
                            "evidence_id": "EV-B",
                            "level": "observed",
                            "target_revision": "rev-1",
                            "method": "manifest-before",
                            "result": "captured",
                            "path": "evidence/before.txt",
                            "sha256": ev_before_hash,
                        },
                        {
                            "evidence_id": "EV-A",
                            "level": "observed",
                            "target_revision": "rev-2",
                            "method": "manifest-after",
                            "result": "captured",
                            "path": "evidence/after.txt",
                            "sha256": ev_after_hash,
                        },
                    ],
                },
            )
            self.assertEqual("owner-adjudication", loop.status("QMS-PILOT-01")["current_state"])

            # 5. Owner: adjudicate
            a = loop.adjudicate(
                "QMS-PILOT-01",
                {
                    "operation_id": "op-adj-pilot-01",
                    "actor_id": "owner-yamaguchi",
                    "role": "owner",
                    "invocation_id": "inv-owner-02",
                    "previous_handoff_id": v["handoff"]["handoff_id"],
                    "expected_case_revision": 6,
                    "decision": "accepted",
                    "rationale": "有効性確認が完了したため受入を承認する",
                    "conditions": [],
                    "residual_risks": [],
                    "dry_run": False,
                    "confirm": True,
                },
            )
            self.assertEqual("accepted", loop.status("QMS-PILOT-01")["current_state"])

            # 6. Status & Resume.md check
            st = loop.status("QMS-PILOT-01", resume_format="markdown")
            self.assertEqual("accepted", st["current_state"])
            self.assertEqual("resume.md", st["resume_path"])
            resume_file = case_root / "QMS-PILOT-01" / "resume.md"
            self.assertTrue(resume_file.is_file())
            resume_text = resume_file.read_text(encoding="utf-8")
            self.assertIn("# 案件ステータス要約: QMS-PILOT-01", resume_text)
            self.assertIn("現在の状態**: accepted", resume_text)


if __name__ == "__main__":
    unittest.main()
