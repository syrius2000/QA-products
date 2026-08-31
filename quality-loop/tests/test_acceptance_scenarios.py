from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop
from quality_loop.errors import QualityLoopError


def create_baseline_intake(case_id: str = "QMS-SCENARIO-01") -> dict:
    return {
        "operation_id": f"op-create-{case_id}",
        "actor_id": "owner-yamaguchi",
        "role": "owner",
        "invocation_id": "inv-owner-001",
        "case_id": case_id,
        "owner": "owner-yamaguchi",
        "baseline": {
            "purpose": "対象モジュールの品質基準適合を確認する",
            "intended_use": {
                "users": "データアナリスト・エンジニア",
                "environment": "分析実行環境",
                "operational_context": "定例集計バッチでの利用",
            },
            "risk_context": {
                "criticality": "medium",
                "safety_impact": "なし",
                "data_integrity_impact": "低",
                "security_context": "社内データ処理",
            },
            "requirements": [
                {"requirement_id": "REQ-001", "text": "正常に計算結果を返すこと"},
                {"requirement_id": "REQ-002", "text": "例外時に安全に停止すること"},
            ],
            "acceptance_criteria": ["REQ-001, REQ-002の検証Evidenceが揃っていること"],
            "exclusions": [],
            "targets": ["src/module.py"],
            "target_revision": "rev-1",
        },
        "implementation_authorization": {
            "allowed": True,
            "finding_ids": ["F-001", "F-002"],
            "allowed_targets": ["src/module.py"],
        },
        "change_observation": {
            "method": "finite-manifest",
            "scope": ["src/module.py"],
            "baseline_evidence_id": None,
            "exclusions": [],
            "limitations": [],
        },
    }


class AcceptanceScenariosTest(unittest.TestCase):
    def test_scenario_01_standard_cycle_to_accepted(self) -> None:
        """シナリオ1: 正常なFinding、修正、独立検証、Owner受入"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-01"))
            self.assertEqual("reviewer-action", loop.status("QMS-SCENARIO-01")["current_state"])

            r1 = loop.review(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-rev-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "不正確な計算結果が返される",
                            "impact": "データ不整合",
                            "expected_state": "正確な結果を返す",
                            "verification_method": "単体テスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("implementer-plan", loop.status("QMS-SCENARIO-01")["current_state"])

            # 2.5 Submit Plan and Review Plan
            p1 = loop.submit_plan(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-plan-01",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-plan-01",
                    "previous_handoff_id": r1["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "不正確な計算結果を修正する",
                            "disposition_intent": "fix",
                            "proposed_actions": ["アルゴリズムを修正する"],
                        }
                    ],
                },
            )
            rp1 = loop.review_plan(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-rev-plan-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-plan-01",
                    "previous_handoff_id": p1["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "修正方針を承認",
                        }
                    ],
                },
            )
            self.assertEqual("implementer-action", loop.status("QMS-SCENARIO-01")["current_state"])

            s1 = loop.submit_response(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-sub-01",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-01",
                    "previous_handoff_id": rp1["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["src/module.py"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "アルゴリズムを修正しテストに合格",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("reviewer-verification", loop.status("QMS-SCENARIO-01")["current_state"])

            v1 = loop.verify(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-ver-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-02",
                    "previous_handoff_id": s1["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "独立テストで期待値一致を確認",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": {
                        "method": "finite-manifest",
                        "scope": ["src/module.py"],
                        "before_evidence_id": "EV-B",
                        "after_evidence_id": "EV-A",
                        "observed_changed_targets": ["src/module.py"],
                        "limitations": [],
                    },
                    "evidence": [
                        {"evidence_id": "EV-B", "level": "observed", "target_revision": "r1", "method": "m", "result": "r", "summary": "s"},
                        {"evidence_id": "EV-A", "level": "observed", "target_revision": "r2", "method": "m", "result": "r", "summary": "s"},
                    ],
                },
            )
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-01")["current_state"])

            a1 = loop.adjudicate(
                "QMS-SCENARIO-01",
                {
                    "operation_id": "op-adj-01",
                    "actor_id": "owner-yamaguchi",
                    "role": "owner",
                    "invocation_id": "inv-owner-02",
                    "previous_handoff_id": v1["handoff"]["handoff_id"],
                    "expected_case_revision": 6,
                    "decision": "accepted",
                    "rationale": "有効性確認が完了したため受入承認",
                    "conditions": [],
                    "residual_risks": [],
                    "dry_run": False,
                    "confirm": True,
                },
            )
            self.assertEqual("accepted", loop.status("QMS-SCENARIO-01")["current_state"])

    def test_scenario_02_no_findings_routes_directly_to_owner(self) -> None:
        """シナリオ2: レビュー時に指摘なし（No findings）の場合、即座にOwner裁定へ遷移"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-02"))

            r1 = loop.review(
                "QMS-SCENARIO-02",
                {
                    "operation_id": "op-rev-02",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [],
                    "evidence": [],
                },
            )
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-02")["current_state"])
            self.assertEqual("owner", r1["handoff"]["next_role"])
            self.assertEqual("adjudicate", r1["handoff"]["next_action"])

    def test_scenario_03_improvement_proposal_does_not_block_adjudication(self) -> None:
        """シナリオ3: 改善提案（improvement-proposal）は受入を妨げない（品質目標を勝手に上げない）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-03"))

            r1 = loop.review(
                "QMS-SCENARIO-03",
                {
                    "operation_id": "op-rev-03",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "PROP-001",
                            "classification": "improvement-proposal",
                            "severity": "low",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "関数コメントにdocstringがない",
                            "impact": "可読性の問題",
                            "expected_state": "docstring追加が望ましい",
                            "verification_method": "コード目視",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-03")["current_state"])

    def test_scenario_04_implementer_rebuttal_with_evidence(self) -> None:
        """シナリオ4: ImplementerによるEvidence付き反論（disagreed-with-evidence）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-04"))
            r1 = loop.review(
                "QMS-SCENARIO-04",
                {
                    "operation_id": "op-rev-04",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "引数Noneで例外になる",
                            "impact": "None安全性の欠如",
                            "expected_state": "Noneを許容する",
                            "verification_method": "単体テスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )

            self.assertEqual("implementer-plan", loop.status("QMS-SCENARIO-04")["current_state"])

            p1 = loop.submit_plan(
                "QMS-SCENARIO-04",
                {
                    "operation_id": "op-plan-04",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-plan-01",
                    "previous_handoff_id": r1["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "引数Noneで例外になるとの指摘だが、仕様書通りの挙動である",
                            "disposition_intent": "disagree-with-evidence",
                            "proposed_actions": ["仕様書REQ-001の定義を反証として提示する"],
                        }
                    ],
                },
            )
            self.assertEqual("reviewer-plan-review", loop.status("QMS-SCENARIO-04")["current_state"])

            rp1 = loop.review_plan(
                "QMS-SCENARIO-04",
                {
                    "operation_id": "op-rev-plan-04",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-plan-02",
                    "previous_handoff_id": p1["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "finding-withdrawn",
                            "rationale": "反論根拠を確認。TypeError送出が仕様通りであることを確認したためF-001を撤回（自己訂正）。",
                        }
                    ],
                },
            )
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-04")["current_state"])
            self.assertEqual("finding-withdrawn", loop.store.load("QMS-SCENARIO-04")["findings"][0]["status"])

    def test_scenario_05_baseline_change_requested_routes_to_owner(self) -> None:
        """シナリオ5: Implementerからの基準変更要求（baseline-change-request）によるOwnerエスカレーション"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-05"))
            r1 = loop.review(
                "QMS-SCENARIO-05",
                {
                    "operation_id": "op-rev-05",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-002",
                            "observed_fact": "非同期処理で停止する",
                            "impact": "動作停止",
                            "expected_state": "非同期対応",
                            "verification_method": "非同期テスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )

            # Implementer requests baseline change via submit-plan -> review-plan -> owner
            p1 = loop.submit_plan(
                "QMS-SCENARIO-05",
                {
                    "operation_id": "op-plan-05",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-01",
                    "previous_handoff_id": r1["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "現行アーキテクチャでは非同期化困難",
                            "disposition_intent": "baseline-change-request",
                            "proposed_actions": ["REQ-002の緩和を要請"],
                        }
                    ],
                },
            )
            rp1 = loop.review_plan(
                "QMS-SCENARIO-05",
                {
                    "operation_id": "op-rev-plan-05",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-plan-01",
                    "previous_handoff_id": p1["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "owner-decision-required",
                            "rationale": "基準変更の是非はOwner裁定が必要",
                        }
                    ],
                },
            )
            # Must route directly to owner without changing baseline
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-05")["current_state"])
            self.assertEqual("owner", rp1["handoff"]["next_role"])

    def test_scenario_06_regression_detected_and_remediation_cycle(self) -> None:
        """シナリオ6: 修正による回帰検知（regression / new_findings）による再修正サイクル"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-06"))
            r1 = loop.review(
                "QMS-SCENARIO-06",
                {
                    "operation_id": "op-rev-06",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "不正確な計算結果",
                            "impact": "計算ミス",
                            "expected_state": "正確な計算",
                            "verification_method": "テスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            p1 = loop.submit_plan(
                "QMS-SCENARIO-06",
                {
                    "operation_id": "op-plan-06",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-01",
                    "previous_handoff_id": r1["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "計算アルゴリズム修正",
                            "disposition_intent": "fix",
                            "proposed_actions": ["計算ロジック書き換え"],
                        }
                    ],
                },
            )
            rp1 = loop.review_plan(
                "QMS-SCENARIO-06",
                {
                    "operation_id": "op-rev-plan-06",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-plan-01",
                    "previous_handoff_id": p1["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "修正方針承認",
                        }
                    ],
                },
            )
            s1 = loop.submit_response(
                "QMS-SCENARIO-06",
                {
                    "operation_id": "op-sub-06",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-02",
                    "previous_handoff_id": rp1["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["src/module.py"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "修正提出",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )

            # Reviewer verifies F-001 as verified, but detects new regression finding F-REG-01
            v1 = loop.verify(
                "QMS-SCENARIO-06",
                {
                    "operation_id": "op-ver-06",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-02",
                    "previous_handoff_id": s1["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "F-001は解消",
                            "evidence_refs": [],
                            "regression_detected": True,
                        }
                    ],
                    "new_findings": [
                        {
                            "finding_id": "F-REG-01",
                            "classification": "regression",
                            "severity": "high",
                            "requirement_ref": "REQ-002",
                            "observed_fact": "修正によりメモリリークが発生",
                            "impact": "クラッシュ",
                            "expected_state": "メモリ解放",
                            "verification_method": "リークテスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "change_observation": {
                        "method": "finite-manifest",
                        "scope": ["src/module.py"],
                        "before_evidence_id": "EV-B",
                        "after_evidence_id": "EV-A",
                        "observed_changed_targets": ["src/module.py"],
                        "limitations": [],
                    },
                    "evidence": [
                        {"evidence_id": "EV-B", "level": "observed", "target_revision": "r1", "method": "m", "result": "r", "summary": "s"},
                        {"evidence_id": "EV-A", "level": "observed", "target_revision": "r2", "method": "m", "result": "r", "summary": "s"},
                    ],
                },
            )
            # New High regression finding requires a fresh Plan before response
            self.assertEqual("implementer-plan", loop.status("QMS-SCENARIO-06")["current_state"])
            self.assertEqual("implementer", v1["handoff"]["next_role"])
            self.assertEqual("submit-plan", v1["handoff"]["next_action"])
            self.assertEqual(["F-REG-01"], v1["handoff"]["open_items"])

    def test_scenario_07_owner_accepts_with_residual_risk(self) -> None:
        """シナリオ7: 未解決Findingに対するOwnerのリスク付き受入（accepted-with-risk）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-07"))
            r1 = loop.review(
                "QMS-SCENARIO-07",
                {
                    "operation_id": "op-rev-07",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "evidence-gap",
                            "severity": "low",
                            "requirement_ref": "REQ-002",
                            "observed_fact": "本番クラスタ環境での負荷テストEvidenceが取得できない",
                            "impact": "高負荷時の性能未確認",
                            "expected_state": "負荷テストEvidenceの取得",
                            "verification_method": "実機クラスタテスト",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )

            revision = 2
            last_handoff = r1
            for cycle in range(1, 4):
                s = loop.submit_response(
                    "QMS-SCENARIO-07",
                    {
                        "operation_id": f"op-sub-07-{cycle}",
                        "actor_id": "imp-01",
                        "role": "implementer",
                        "invocation_id": f"inv-imp-07-{cycle}",
                        "previous_handoff_id": last_handoff["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "cannot-verify",
                                "rationale": "ローカル検証環境では本番クラスタ負荷テストを実行できません。",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
                revision += 1

                v = loop.verify(
                    "QMS-SCENARIO-07",
                    {
                        "operation_id": f"op-ver-07-{cycle}",
                        "actor_id": "reviewer-01",
                        "role": "reviewer",
                        "invocation_id": f"inv-rev-07-{cycle}",
                        "previous_handoff_id": s["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "unverified",
                                "rationale": "環境制約による未確認を確認。",
                                "evidence_refs": [],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                    },
                )
                revision += 1
                last_handoff = v

            # After 3 cycles with unverified findings, state transitions to reviewer-final-assessment
            self.assertEqual("reviewer-final-assessment", loop.status("QMS-SCENARIO-07")["current_state"])
            self.assertEqual("reviewer", last_handoff["handoff"]["next_role"])
            self.assertEqual("assess-risk", last_handoff["handoff"]["next_action"])

            # Reviewer executes assess-risk
            ar = loop.assess_risk(
                "QMS-SCENARIO-07",
                {
                    "operation_id": "op-assess-07",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-assess-01",
                    "previous_handoff_id": last_handoff["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "overall_recommendation": "accept-with-conditions",
                    "rationale": "ローカル検証の制約による未確認であり、ステージングでの追加テストを条件として受入を推奨する",
                    "residual_risks": [
                        {
                            "finding_id": "F-001",
                            "current_status": "unverified",
                            "severity": "low",
                            "implemented_controls": ["単体テストによる基本性能確認"],
                            "residual_risk_description": "高負荷時のクラスタ性能が未確認",
                            "assumptions_supporting_acceptance": ["ステージング環境で負荷試験を実施予定"],
                            "likelihood": "low",
                            "impact": "medium",
                            "alternatives": ["負荷試験環境をローカルに構築（工数大）"],
                            "proportionality_assessment": "現フェーズでの実機構築は過大負担であり、ステージングでの検証が妥当",
                            "qa_recommendation": "accept-with-conditions",
                            "confidence": "high",
                            "reassessment_triggers": ["ステージング環境へのデプロイ完了時"],
                        }
                    ],
                },
            )
            revision += 1
            self.assertEqual("owner-adjudication", loop.status("QMS-SCENARIO-07")["current_state"])
            self.assertEqual("owner", ar["handoff"]["next_role"])
            self.assertEqual("adjudicate", ar["handoff"]["next_action"])

            # Confirm final-risk-assessment.md was generated
            fra_path = Path(temp_dir) / "QMS-SCENARIO-07" / "final-risk-assessment.md"
            self.assertTrue(fra_path.exists())
            fra_content = fra_path.read_text(encoding="utf-8")
            self.assertIn("最終リスク評価報告書", fra_content)
            self.assertIn("F-001", fra_content)

            a1 = loop.adjudicate(
                "QMS-SCENARIO-07",
                {
                    "operation_id": "op-adj-07",
                    "actor_id": "owner-yamaguchi",
                    "role": "owner",
                    "invocation_id": "inv-owner-02",
                    "previous_handoff_id": ar["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "decision": "accepted-with-risk",
                    "rationale": "ステージング移行後に負荷テストを実施する条件付きで現版を受入承認する。",
                    "conditions": ["ステージング環境配備後にF-001の負荷テストを実施すること"],
                    "residual_risks": ["高負荷時のレイテンシ増加リスク"],
                    "dry_run": False,
                    "confirm": True,
                },
            )
            self.assertEqual("accepted-with-risk", loop.status("QMS-SCENARIO-07")["current_state"])

    def test_scenario_08_safety_firewall_and_rejections(self) -> None:
        """シナリオ8: 自己クローズ・権限外操作・競合Revision等の安全拒否"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            c1 = loop.create_case(create_baseline_intake("QMS-SCENARIO-08"))

            # 1. Non-owner trying to create case
            with self.assertRaises(QualityLoopError) as ctx:
                bad_intake = dict(create_baseline_intake("QMS-BAD"))
                bad_intake["role"] = "implementer"
                loop.create_case(bad_intake)
            self.assertEqual("role-not-allowed", ctx.exception.error_code)

            # 2. Implementer trying to execute review
            with self.assertRaises(QualityLoopError) as ctx:
                loop.review(
                    "QMS-SCENARIO-08",
                    {
                        "operation_id": "op-bad",
                        "actor_id": "imp-01",
                        "role": "implementer",
                        "invocation_id": "inv-01",
                        "previous_handoff_id": c1["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "findings": [],
                        "evidence": [],
                    },
                )
            # 3. Invalid state transition: Implementer calling submit-response during reviewer-action
            with self.assertRaises(QualityLoopError) as ctx:
                loop.submit_response(
                    "QMS-SCENARIO-08",
                    {
                        "operation_id": "op-sub-bad",
                        "actor_id": "imp-01",
                        "role": "implementer",
                        "invocation_id": "inv-01",
                        "previous_handoff_id": c1["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "changed_targets": [],
                        "responses": [],
                        "evidence": [],
                    },
                )
            self.assertEqual("state-transition-not-allowed", ctx.exception.error_code)

            # 4. Implementer trying to execute adjudicate
            with self.assertRaises(QualityLoopError) as ctx:
                loop.adjudicate(
                    "QMS-SCENARIO-08",
                    {
                        "operation_id": "op-adj-bad",
                        "actor_id": "imp-01",
                        "role": "implementer",
                        "invocation_id": "inv-01",
                        "previous_handoff_id": c1["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "decision": "accepted",
                        "rationale": "自己クローズ試行",
                        "conditions": [],
                        "residual_risks": [],
                        "confirm": True,
                    },
                )
            self.assertEqual("role-not-allowed", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
