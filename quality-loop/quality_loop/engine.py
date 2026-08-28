from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .authorization import validate_authorization, validate_changed_targets
from .case_store import CaseStore
from .errors import QualityLoopError
from .evidence import validate_evidence
from .handoff import issue_handoff, terminal_handoff
from .model import validate_findings
from .transitions import ALLOWED_FIELDS, EXPECTED_ROLE, EXPECTED_STATE


CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class QualityLoop:
    def __init__(self, case_root: Path) -> None:
        self.store = CaseStore(case_root)

    def create_case(self, payload: dict) -> dict:
        self._validate_create(payload)
        case_id = payload["case_id"]
        now = utc_now()
        handoff = issue_handoff(
            revision=1,
            next_role="reviewer",
            next_action="review",
            purpose="baselineと対象成果物を独立レビューする",
            inputs=["baseline", "対象成果物", "利用可能なEvidence"],
            open_items=[],
            expected_outputs=["FindingまたはFindingなしの根拠", "次工程handoff"],
        )
        result = self._result(
            case_id=case_id,
            revision=1,
            state_changed=True,
            next_role="reviewer",
            next_action="review",
            handoff=handoff,
        )
        case = {
            "schema_version": "1.0",
            "case_metadata": {
                "case_id": case_id,
                "revision": 1,
                "status": "reviewer-action",
                "owner": payload["owner"],
                "cycle_count": 0,
                "cycle_limit": 3,
                "created_at": now,
                "updated_at": now,
            },
            "baseline": deepcopy(payload["baseline"]),
            "implementation_authorization": validate_authorization(
                payload.get(
                    "implementation_authorization",
                    {"allowed": False, "finding_ids": [], "allowed_targets": []},
                )
            ),
            "change_observation": deepcopy(
                payload.get(
                    "change_observation",
                    {
                        "method": "external",
                        "scope": [],
                        "baseline_evidence_id": None,
                        "exclusions": [],
                        "limitations": ["開始時の変更観測Evidenceが未登録"],
                    },
                )
            ),
            "findings": [],
            "evidence": [],
            "responses": [],
            "verifications": [],
            "adjudications": [],
            "events": [
                {
                    "operation_id": payload["operation_id"],
                    "actor_id": payload["actor_id"],
                    "role": "owner",
                    "invocation_id": payload["invocation_id"],
                    "operation": "create-case",
                    "revision": 1,
                    "timestamp": now,
                    "result": deepcopy(result),
                }
            ],
            "handoff": handoff,
        }
        self.store.create(case_id, case)
        return result

    def review(self, case_id: str, payload: dict) -> dict:
        def mutation(current: dict) -> tuple[dict | None, dict]:
            duplicate = self._duplicate_result(current, payload.get("operation_id"))
            if duplicate is not None:
                return None, duplicate
            self._validate_update(current, payload, "review")
            findings = validate_findings(
                payload.get("findings"),
                {item["finding_id"] for item in current["findings"]},
            )
            rereviews = self._validate_rereviews(
                current, payload.get("rereviews", [])
            )
            evidence = validate_evidence(
                self.store.case_dir(case_id),
                payload.get("evidence", []),
                {item["evidence_id"] for item in current["evidence"]},
            )
            available_evidence_ids = {
                item["evidence_id"] for item in current["evidence"] + evidence
            }
            for finding in findings:
                unknown_refs = set(finding["evidence_refs"]) - available_evidence_ids
                if unknown_refs:
                    raise QualityLoopError(
                        "unknown-evidence-id",
                        f"未知のEvidence IDです: {', '.join(sorted(unknown_refs))}",
                    )
            for rereview in rereviews:
                unknown_refs = set(rereview["evidence_refs"]) - available_evidence_ids
                if unknown_refs:
                    raise QualityLoopError(
                        "unknown-evidence-id",
                        f"未知のEvidence IDです: {', '.join(sorted(unknown_refs))}",
                    )
            updated = deepcopy(current)
            rereview_by_id = {item["finding_id"]: item for item in rereviews}
            for finding in updated["findings"]:
                rereview = rereview_by_id.get(finding["finding_id"])
                if rereview is not None:
                    record = deepcopy(rereview)
                    record["rereview_revision"] = current["case_metadata"]["revision"] + 1
                    finding.setdefault("rereviews", []).append(record)
                    finding["status"] = rereview["result"]
            updated["findings"].extend(deepcopy(findings))
            updated["evidence"].extend(evidence)
            revision = current["case_metadata"]["revision"] + 1
            blocking_findings = [
                item
                for item in updated["findings"]
                if item["classification"] != "improvement-proposal"
                and item.get("status") != "verified"
            ]
            if blocking_findings:
                next_role = "implementer"
                next_action = "submit-response"
                state = "implementer-action"
                purpose = "Findingごとに回答し、許可範囲だけを修正する"
                open_items = [item["finding_id"] for item in blocking_findings]
                expected_outputs = ["Finding別回答", "変更Evidence", "次工程handoff"]
            else:
                next_role = "owner"
                next_action = "adjudicate"
                state = "owner-adjudication"
                purpose = "Findingなしのレビュー結果を裁定する"
                open_items = []
                expected_outputs = ["Owner裁定"]
            handoff = issue_handoff(
                revision=revision,
                next_role=next_role,
                next_action=next_action,
                purpose=purpose,
                inputs=["baseline", "review結果", "Evidence"],
                open_items=open_items,
                expected_outputs=expected_outputs,
            )
            result = self._result(
                case_id=case_id,
                revision=revision,
                state_changed=True,
                next_role=next_role,
                next_action=next_action,
                handoff=handoff,
            )
            self._finish_update(
                updated=updated,
                payload=payload,
                operation="review",
                revision=revision,
                state=state,
                handoff=handoff,
                result=result,
            )
            return updated, result

        return self.store.mutate(case_id, mutation)

    def submit_response(self, case_id: str, payload: dict) -> dict:
        def mutation(current: dict) -> tuple[dict | None, dict]:
            duplicate = self._duplicate_result(current, payload.get("operation_id"))
            if duplicate is not None:
                return None, duplicate
            self._validate_update(current, payload, "submit-response")
            responses = self._validate_responses(current, payload.get("responses"))
            response_finding_ids = {item["finding_id"] for item in responses}
            changed_targets = validate_changed_targets(
                current["implementation_authorization"],
                finding_ids=response_finding_ids,
                changed_targets=payload.get("changed_targets"),
            )
            if any(
                item["disposition"] == "fix-submitted" for item in responses
            ) and not changed_targets:
                raise QualityLoopError(
                    "invalid-response",
                    "fix-submittedにはchanged_targetsが必要です。",
                )
            evidence = validate_evidence(
                self.store.case_dir(case_id),
                payload.get("evidence", []),
                {item["evidence_id"] for item in current["evidence"]},
            )
            available_evidence_ids = {
                item["evidence_id"] for item in current["evidence"] + evidence
            }
            for response in responses:
                unknown_refs = set(response["evidence_refs"]) - available_evidence_ids
                if unknown_refs:
                    raise QualityLoopError(
                        "unknown-evidence-id",
                        f"未知のEvidence IDです: {', '.join(sorted(unknown_refs))}",
                    )
            updated = deepcopy(current)
            revision = current["case_metadata"]["revision"] + 1
            for response in responses:
                record = deepcopy(response)
                record["changed_targets"] = list(changed_targets)
                record["submission_revision"] = revision
                updated["responses"].append(record)
            updated["evidence"].extend(evidence)
            for finding in updated["findings"]:
                if finding["finding_id"] in response_finding_ids:
                    finding["status"] = "response-submitted"
            baseline_change_requested = any(
                item["disposition"] == "baseline-change-requested"
                for item in responses
            )
            if baseline_change_requested:
                next_role = "owner"
                next_action = "adjudicate"
                state = "owner-adjudication"
                purpose = "baseline変更要求をOwnerが裁定する"
                expected_outputs = ["baseline維持・変更・保留のOwner裁定"]
            else:
                next_role = "reviewer"
                next_action = "verify"
                state = "reviewer-verification"
                purpose = "Implementer提出と修正結果を独立検証する"
                expected_outputs = ["Finding別検証", "変更範囲照合", "次工程handoff"]
            handoff = issue_handoff(
                revision=revision,
                next_role=next_role,
                next_action=next_action,
                purpose=purpose,
                inputs=["Finding", "Implementer回答", "変更Evidence", "変更観測"],
                open_items=sorted(response_finding_ids),
                expected_outputs=expected_outputs,
            )
            result = self._result(
                case_id=case_id,
                revision=revision,
                state_changed=True,
                next_role=next_role,
                next_action=next_action,
                handoff=handoff,
            )
            self._finish_update(
                updated=updated,
                payload=payload,
                operation="submit-response",
                revision=revision,
                state=state,
                handoff=handoff,
                result=result,
            )
            return updated, result

        return self.store.mutate(case_id, mutation)

    def verify(self, case_id: str, payload: dict) -> dict:
        def mutation(current: dict) -> tuple[dict | None, dict]:
            duplicate = self._duplicate_result(current, payload.get("operation_id"))
            if duplicate is not None:
                return None, duplicate
            self._validate_update(current, payload, "verify")
            latest_submit_event = next(
                event
                for event in reversed(current["events"])
                if event["operation"] == "submit-response"
            )
            if latest_submit_event["invocation_id"] == payload["invocation_id"]:
                raise QualityLoopError(
                    "verification-not-independent",
                    "verifyは対象submit-responseと異なるInvocationで実行してください。",
                )
            submission_revision = latest_submit_event["revision"]
            submitted_responses = [
                item
                for item in current["responses"]
                if item["submission_revision"] == submission_revision
            ]
            verifications = self._validate_verifications(
                submitted_responses, payload.get("verifications")
            )
            new_findings = validate_findings(
                payload.get("new_findings", []),
                {item["finding_id"] for item in current["findings"]},
            )
            evidence = validate_evidence(
                self.store.case_dir(case_id),
                payload.get("evidence", []),
                {item["evidence_id"] for item in current["evidence"]},
            )
            available_evidence_ids = {
                item["evidence_id"] for item in current["evidence"] + evidence
            }
            for verification in verifications:
                unknown_refs = set(verification["evidence_refs"]) - available_evidence_ids
                if unknown_refs:
                    raise QualityLoopError(
                        "unknown-evidence-id",
                        f"未知のEvidence IDです: {', '.join(sorted(unknown_refs))}",
                    )
            observation = self._validate_change_observation(
                current=current,
                responses=submitted_responses,
                observation=payload.get("change_observation"),
                evidence_ids=available_evidence_ids,
            )
            updated = deepcopy(current)
            revision = current["case_metadata"]["revision"] + 1
            verification_by_id = {
                item["finding_id"]: item for item in verifications
            }
            for verification in verifications:
                record = deepcopy(verification)
                record["verification_revision"] = revision
                record["change_observation"] = deepcopy(observation)
                updated["verifications"].append(record)
            for finding in updated["findings"]:
                verification = verification_by_id.get(finding["finding_id"])
                if verification is not None:
                    finding["status"] = verification["result"]
            updated["findings"].extend(deepcopy(new_findings))
            updated["evidence"].extend(evidence)
            cycle_count = current["case_metadata"].get("cycle_count", 0) + 1
            updated["case_metadata"]["cycle_count"] = cycle_count
            all_verified = all(
                item["result"] == "verified" for item in verifications
            ) and not new_findings
            authorization_missing = (
                not current["implementation_authorization"].get("allowed", False)
                and not all_verified
            )
            if (
                all_verified
                or authorization_missing
                or cycle_count >= current["case_metadata"].get("cycle_limit", 3)
            ):
                next_role = "owner"
                next_action = "adjudicate"
                state = "owner-adjudication"
                if authorization_missing:
                    purpose = "実装許可がない未解決Findingを裁定する"
                else:
                    purpose = "独立検証結果と残余リスクを裁定する"
                expected_outputs = ["Owner裁定"]
            else:
                next_role = "implementer"
                next_action = "submit-response"
                state = "implementer-action"
                purpose = "未解決または新規Findingへ回答する"
                expected_outputs = ["Finding別回答", "変更Evidence"]
            open_items = [
                item["finding_id"]
                for item in updated["findings"]
                if item.get("status") != "verified"
                and item.get("classification") != "improvement-proposal"
            ]
            handoff = issue_handoff(
                revision=revision,
                next_role=next_role,
                next_action=next_action,
                purpose=purpose,
                inputs=["Finding", "Implementer回答", "Reviewer検証", "Evidence"],
                open_items=open_items,
                expected_outputs=expected_outputs,
            )
            result = self._result(
                case_id=case_id,
                revision=revision,
                state_changed=True,
                next_role=next_role,
                next_action=next_action,
                handoff=handoff,
            )
            self._finish_update(
                updated=updated,
                payload=payload,
                operation="verify",
                revision=revision,
                state=state,
                handoff=handoff,
                result=result,
            )
            return updated, result

        return self.store.mutate(case_id, mutation)

    def adjudicate(self, case_id: str, payload: dict) -> dict:
        def mutation(current: dict) -> tuple[dict | None, dict]:
            duplicate = self._duplicate_result(current, payload.get("operation_id"))
            if duplicate is not None:
                return None, duplicate
            self._validate_update(current, payload, "adjudicate")
            decision = payload.get("decision")
            allowed_decisions = {
                "accepted",
                "accepted-with-risk",
                "held",
                "rejected",
                "rework-requested",
            }
            if decision not in allowed_decisions:
                raise QualityLoopError(
                    "invalid-adjudication",
                    "未対応のOwner裁定です。",
                )
            if not payload.get("rationale"):
                raise QualityLoopError(
                    "invalid-adjudication", "Owner裁定にはrationaleが必要です。"
                )
            unresolved = [
                item["finding_id"]
                for item in current["findings"]
                if item.get("status") != "verified"
                and item.get("classification") != "improvement-proposal"
            ]
            if decision == "accepted" and unresolved:
                raise QualityLoopError(
                    "unresolved-findings",
                    f"未解決Findingがあるため通常受入できません: {', '.join(unresolved)}",
                    remediation="再作業、保留、却下、または残余リスク付き受入を裁定してください。",
                )
            if decision == "accepted-with-risk":
                if not payload.get("residual_risks"):
                    raise QualityLoopError(
                        "residual-risk-required",
                        "リスク付き受入にはresidual_risksが必要です。",
                    )
                if not payload.get("conditions"):
                    raise QualityLoopError(
                        "risk-conditions-required",
                        "リスク付き受入にはconditionsが必要です。",
                    )
                if not payload.get("review_trigger"):
                    raise QualityLoopError(
                        "risk-review-trigger-required",
                        "リスク付き受入には期限または再確認トリガーとなるreview_triggerが必要です。",
                    )
            baseline_update = payload.get("baseline_update")
            if baseline_update is not None:
                if decision != "rework-requested":
                    raise QualityLoopError(
                        "invalid-adjudication",
                        "baseline変更はrework-requestedと組み合わせてください。",
                    )
                self._validate_baseline(baseline_update)
            cycle_count = current["case_metadata"].get("cycle_count", 0)
            cycle_limit = current["case_metadata"].get("cycle_limit", 3)
            additional_cycles = payload.get("additional_cycles")
            if decision == "rework-requested" and cycle_count >= cycle_limit:
                if not isinstance(additional_cycles, int) or isinstance(
                    additional_cycles, bool
                ) or additional_cycles <= 0:
                    raise QualityLoopError(
                        "additional-cycles-required",
                        "3サイクル到達後の再作業にはOwnerによる正の追加サイクル数が必要です。",
                    )
            elif additional_cycles is not None:
                raise QualityLoopError(
                    "invalid-adjudication",
                    "additional_cyclesはサイクル上限到達後のrework-requestedだけで指定できます。",
                )
            authorization_update = payload.get("implementation_authorization")
            if authorization_update is not None:
                authorization_update = validate_authorization(authorization_update)
            dry_run = payload.get("dry_run", False)
            terminal_decisions = {"accepted", "accepted-with-risk", "rejected"}
            if not isinstance(dry_run, bool) or not isinstance(
                payload.get("confirm", False), bool
            ):
                raise QualityLoopError(
                    "invalid-adjudication",
                    "dry_runとconfirmはbooleanで指定してください。",
                )
            if dry_run:
                preview = self._result(
                    case_id=case_id,
                    revision=current["case_metadata"]["revision"],
                    state_changed=False,
                    next_role=current["handoff"]["next_role"],
                    next_action=current["handoff"]["next_action"],
                    handoff=current["handoff"],
                    status="dry-run",
                )
                preview["preview_decision"] = decision
                preview["unresolved_findings"] = unresolved
                return None, preview
            if decision in terminal_decisions and not payload.get("confirm", False):
                raise QualityLoopError(
                    "confirmation-required",
                    "終端裁定にはconfirm: trueが必要です。",
                    remediation="dry-runの内容を確認後、confirm: trueで再実行してください。",
                )
            updated = deepcopy(current)
            revision = current["case_metadata"]["revision"] + 1
            adjudication = {
                "decision": decision,
                "rationale": payload["rationale"],
                "conditions": deepcopy(payload.get("conditions", [])),
                "residual_risks": deepcopy(payload.get("residual_risks", [])),
                "review_trigger": payload.get("review_trigger"),
                "adjudication_revision": revision,
            }
            updated["adjudications"].append(adjudication)
            if additional_cycles is not None:
                updated["case_metadata"]["cycle_limit"] = cycle_count + additional_cycles
            if authorization_update is not None:
                updated["implementation_authorization"] = authorization_update
            if baseline_update is not None:
                updated["baseline"] = deepcopy(baseline_update)
                for item in updated["findings"]:
                    if item.get("classification") != "improvement-proposal":
                        item["status"] = "requires-rereview"
                next_role = "reviewer"
                next_action = "review"
                state = "reviewer-action"
                handoff = issue_handoff(
                    revision=revision,
                    next_role=next_role,
                    next_action=next_action,
                    purpose="Owner変更後のbaselineで対象を再レビューする",
                    inputs=["baseline変更差分", "影響するFinding", "対象成果物"],
                    open_items=unresolved,
                    expected_outputs=["再評価したFinding", "次工程handoff"],
                )
            elif decision == "rework-requested":
                next_role = "implementer"
                next_action = "submit-response"
                state = "implementer-action"
                handoff = issue_handoff(
                    revision=revision,
                    next_role=next_role,
                    next_action=next_action,
                    purpose="Owner裁定に基づき追加改善を提出する",
                    inputs=["Owner裁定", "未解決Finding"],
                    open_items=unresolved,
                    expected_outputs=["Finding別回答", "変更Evidence"],
                )
            elif decision == "held":
                next_role = "owner"
                next_action = "adjudicate"
                state = "held"
                handoff = issue_handoff(
                    revision=revision,
                    next_role=next_role,
                    next_action=next_action,
                    purpose="不足する判断材料を確認し、Owner裁定を再開する",
                    inputs=["保留理由", "必要な追加情報", "残余リスク"],
                    open_items=unresolved,
                    expected_outputs=["再開後のOwner裁定"],
                )
            else:
                next_role = None
                next_action = None
                state = decision
                handoff = terminal_handoff(revision=revision, result=decision)
            result = self._result(
                case_id=case_id,
                revision=revision,
                state_changed=True,
                next_role=next_role,
                next_action=next_action,
                handoff=handoff,
            )
            self._finish_update(
                updated=updated,
                payload=payload,
                operation="adjudicate",
                revision=revision,
                state=state,
                handoff=handoff,
                result=result,
            )
            return updated, result

        return self.store.mutate(case_id, mutation)

    def status(self, case_id: str, *, resume_format: str | None = None) -> dict:
        case = self.store.load(case_id)
        metadata = case["case_metadata"]
        handoff = deepcopy(case["handoff"])
        open_findings = [
            item["finding_id"]
            for item in case["findings"]
            if item.get("status") != "verified"
            and item.get("classification") != "improvement-proposal"
        ]
        evidence_gaps = [
            item["finding_id"]
            for item in case["findings"]
            if item.get("classification") == "evidence-gap"
            and item.get("status") != "verified"
        ]
        result = self._result(
            case_id=case_id,
            revision=metadata["revision"],
            state_changed=False,
            next_role=handoff["next_role"],
            next_action=handoff["next_action"],
            handoff=handoff,
        )
        result.update(
            {
                "current_state": metadata["status"],
                "last_completed_operation": case["events"][-1]["operation"],
                "open_findings": open_findings,
                "evidence_gaps": evidence_gaps,
                "owner_decisions_required": metadata["status"]
                in {"owner-adjudication", "held-for-owner", "held"},
                "implementation_authorization": deepcopy(
                    case["implementation_authorization"]
                ),
            }
        )
        if resume_format is not None:
            if resume_format != "markdown":
                raise QualityLoopError(
                    "invalid-resume-format",
                    "resume-formatはmarkdownだけを指定できます。",
                )
            open_text = ", ".join(open_findings) if open_findings else "なし"
            text = (
                f"# 案件 {case_id} 再開要約\n\n"
                f"- 正本revision: {metadata['revision']}\n"
                f"- 現在状態: {metadata['status']}\n"
                f"- 最後の完了操作: {case['events'][-1]['operation']}\n"
                f"- 未解決Finding: {open_text}\n"
                f"- 次のRole: {handoff['next_role']}\n"
                f"- 次の操作: {handoff['next_action']}\n"
                f"- 最新handoff ID: {handoff['handoff_id']}\n\n"
                "このファイルは表示用であり、案件正本ではありません。\n"
            )
            self.store.atomic_write_text(self.store.case_dir(case_id) / "resume.md", text)
            result["resume_path"] = "resume.md"
        return result

    @staticmethod
    def _validate_create(payload: dict) -> None:
        required = (
            "operation_id",
            "actor_id",
            "role",
            "invocation_id",
            "case_id",
            "owner",
            "baseline",
        )
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise QualityLoopError(
                "invalid-input",
                f"必須項目が不足しています: {', '.join(missing)}",
                remediation="create-caseの必須項目を補完してください。",
            )
        if payload["role"] != "owner":
            raise QualityLoopError(
                "role-not-allowed",
                "create-caseはOwnerだけが実行できます。",
                remediation="roleをownerにし、OwnerのInvocationから実行してください。",
            )
        if payload["actor_id"] != payload["owner"]:
            raise QualityLoopError(
                "owner-identity-mismatch",
                "create-caseのactor_idとownerは一致しなければなりません。",
                remediation="案件Owner自身のactor_idで作成してください。",
            )
        if not CASE_ID_PATTERN.fullmatch(payload["case_id"]):
            raise QualityLoopError(
                "invalid-case-id",
                "case_idは英数字で始まる英数字・ドット・ハイフン・下線だけを使用してください。",
                remediation="安全なcase_idへ変更してください。",
            )
        QualityLoop._validate_baseline(payload["baseline"])

    @staticmethod
    def _validate_rereviews(case: dict, rereviews: object) -> list[dict]:
        if not isinstance(rereviews, list):
            raise QualityLoopError("invalid-rereview", "rereviewsは配列で指定してください。")
        required_ids = {
            item["finding_id"]
            for item in case["findings"]
            if item.get("status") == "requires-rereview"
        }
        if not required_ids:
            if rereviews:
                raise QualityLoopError(
                    "unexpected-rereview", "再評価が必要なFindingはありません。"
                )
            return []
        seen_ids: set[str] = set()
        validated: list[dict] = []
        for rereview in rereviews:
            if not isinstance(rereview, dict):
                raise QualityLoopError("invalid-rereview", "再評価はobjectで指定してください。")
            required = ("finding_id", "result", "rationale", "evidence_refs")
            missing = [field for field in required if field not in rereview]
            if missing:
                raise QualityLoopError(
                    "invalid-rereview",
                    f"再評価必須項目が不足しています: {', '.join(missing)}",
                )
            finding_id = rereview["finding_id"]
            if finding_id not in required_ids:
                raise QualityLoopError(
                    "invalid-rereview", f"再評価対象でないFindingです: {finding_id}"
                )
            if finding_id in seen_ids:
                raise QualityLoopError(
                    "duplicate-rereview", f"Finding {finding_id} の再評価が重複しています。"
                )
            if rereview["result"] not in {"verified", "open", "unverified"}:
                raise QualityLoopError("invalid-rereview", "未対応の再評価結果です。")
            evidence_refs = rereview["evidence_refs"]
            if not isinstance(evidence_refs, list) or not all(
                isinstance(item, str) and item for item in evidence_refs
            ):
                raise QualityLoopError(
                    "invalid-rereview",
                    "再評価のevidence_refsはEvidence ID配列で指定してください。",
                )
            if not evidence_refs and (
                rereview["result"] != "unverified"
                or not rereview.get("unverified_reason")
                or not rereview.get("required_evidence")
            ):
                raise QualityLoopError(
                    "rereview-evidence-required",
                    "再評価にはEvidence参照が必要です。未検証の場合はunverified_reasonとrequired_evidenceを指定してください。",
                )
            seen_ids.add(finding_id)
            validated.append(deepcopy(rereview))
        if seen_ids != required_ids:
            missing_ids = sorted(required_ids - seen_ids)
            raise QualityLoopError(
                "incomplete-rereview",
                f"再評価されていないFindingがあります: {', '.join(missing_ids)}",
            )
        return validated

    @staticmethod
    def _validate_responses(case: dict, responses: object) -> list[dict]:
        if not isinstance(responses, list) or not responses:
            raise QualityLoopError(
                "invalid-response",
                "responsesにはFinding別回答が必要です。",
            )
        allowed_dispositions = {
            "accepted",
            "fix-submitted",
            "disagreed-with-evidence",
            "cannot-verify",
            "baseline-change-requested",
        }
        known_ids = {item["finding_id"] for item in case["findings"]}
        seen_ids: set[str] = set()
        validated: list[dict] = []
        for response in responses:
            if not isinstance(response, dict):
                raise QualityLoopError("invalid-response", "Responseはobjectで指定してください。")
            required = ("finding_id", "disposition", "rationale", "evidence_refs")
            missing = [field for field in required if field not in response]
            if missing:
                raise QualityLoopError(
                    "invalid-response",
                    f"Response必須項目が不足しています: {', '.join(missing)}",
                )
            finding_id = response["finding_id"]
            if finding_id not in known_ids:
                raise QualityLoopError(
                    "unknown-finding-id",
                    f"未知のFinding IDです: {finding_id}",
                )
            if finding_id in seen_ids:
                raise QualityLoopError(
                    "duplicate-finding-response",
                    f"Finding {finding_id} への回答が重複しています。",
                )
            if response["disposition"] not in allowed_dispositions:
                raise QualityLoopError("invalid-response", "未対応のDispositionです。")
            seen_ids.add(finding_id)
            validated.append(deepcopy(response))
        return validated

    @staticmethod
    def _validate_verifications(
        responses: list[dict], verifications: object
    ) -> list[dict]:
        if not isinstance(verifications, list) or not verifications:
            raise QualityLoopError(
                "invalid-verification",
                "verificationsにはFinding別検証が必要です。",
            )
        expected_ids = {item["finding_id"] for item in responses}
        seen_ids: set[str] = set()
        validated: list[dict] = []
        for verification in verifications:
            if not isinstance(verification, dict):
                raise QualityLoopError(
                    "invalid-verification", "Verificationはobjectで指定してください。"
                )
            required = ("finding_id", "result", "rationale", "evidence_refs")
            missing = [field for field in required if field not in verification]
            if missing:
                raise QualityLoopError(
                    "invalid-verification",
                    f"Verification必須項目が不足しています: {', '.join(missing)}",
                )
            finding_id = verification["finding_id"]
            if finding_id not in expected_ids:
                raise QualityLoopError(
                    "unknown-finding-id",
                    f"今回の提出対象でないFindingです: {finding_id}",
                )
            if finding_id in seen_ids:
                raise QualityLoopError(
                    "duplicate-verification",
                    f"Finding {finding_id} の検証が重複しています。",
                )
            if verification["result"] not in {
                "verified",
                "not-verified",
                "unverified",
            }:
                raise QualityLoopError(
                    "invalid-verification", "未対応のVerification resultです。"
                )
            evidence_refs = verification["evidence_refs"]
            if not isinstance(evidence_refs, list) or not all(
                isinstance(item, str) and item for item in evidence_refs
            ):
                raise QualityLoopError(
                    "invalid-verification",
                    "Verificationのevidence_refsは空でないEvidence ID配列で指定してください。",
                )
            if not evidence_refs and (
                verification["result"] != "unverified"
                or not verification.get("unverified_reason")
                or not verification.get("required_evidence")
            ):
                raise QualityLoopError(
                    "verification-evidence-required",
                    "VerificationにはEvidence参照が必要です。未検証の場合はunverified_reasonとrequired_evidenceを指定してください。",
                )
            seen_ids.add(finding_id)
            validated.append(deepcopy(verification))
        if seen_ids != expected_ids:
            missing_ids = sorted(expected_ids - seen_ids)
            raise QualityLoopError(
                "incomplete-verification",
                f"未検証の提出Findingがあります: {', '.join(missing_ids)}",
            )
        return validated

    @staticmethod
    def _validate_change_observation(
        *,
        current: dict,
        responses: list[dict],
        observation: object,
        evidence_ids: set[str],
    ) -> dict:
        declared = {
            target for response in responses for target in response["changed_targets"]
        }
        if not declared:
            return {
                "method": "none",
                "scope": [],
                "observed_changed_targets": [],
                "limitations": [],
            }
        if not isinstance(observation, dict):
            raise QualityLoopError(
                "change-observation-required",
                "変更提出のverifyには独立change_observationが必要です。",
            )
        required = (
            "method",
            "scope",
            "before_evidence_id",
            "after_evidence_id",
            "observed_changed_targets",
            "limitations",
        )
        missing = [field for field in required if field not in observation]
        if missing:
            raise QualityLoopError(
                "invalid-change-observation",
                f"change_observation必須項目が不足しています: {', '.join(missing)}",
            )
        observation_refs = {
            observation["before_evidence_id"],
            observation["after_evidence_id"],
        }
        if not observation_refs.issubset(evidence_ids):
            raise QualityLoopError(
                "unknown-evidence-id",
                "変更観測の開始・終了Evidenceを確認できません。",
            )
        observed = set(observation["observed_changed_targets"])
        undeclared = sorted(observed - declared)
        if undeclared:
            raise QualityLoopError(
                "undeclared-change-detected",
                f"申告外変更を検出しました: {', '.join(undeclared)}",
                remediation="申告外変更を戻すか、Implementer提出を訂正してください。",
            )
        allowed = set(current["implementation_authorization"].get("allowed_targets", []))
        unauthorized = sorted(observed - allowed)
        if unauthorized:
            raise QualityLoopError(
                "unauthorized-change-detected",
                f"許可外変更を検出しました: {', '.join(unauthorized)}",
            )
        unobserved = sorted(declared - observed)
        if unobserved:
            raise QualityLoopError(
                "change-observation-incomplete",
                f"申告された変更を観測できません: {', '.join(unobserved)}",
                remediation="観測範囲を補完するかunverifiedとして再提出してください。",
            )
        return deepcopy(observation)

    @staticmethod
    def _validate_baseline(baseline: object) -> None:
        if not isinstance(baseline, dict):
            raise QualityLoopError("invalid-input", "baselineはobjectで指定してください。")
        baseline_required = (
            "purpose",
            "requirements",
            "acceptance_criteria",
            "targets",
            "target_revision",
        )
        baseline_missing = [key for key in baseline_required if not baseline.get(key)]
        if baseline_missing:
            raise QualityLoopError(
                "invalid-input",
                f"baseline必須項目が不足しています: {', '.join(baseline_missing)}",
                remediation="Purpose、要求、受入基準、対象、対象revisionを指定してください。",
            )

    @staticmethod
    def _duplicate_result(case: dict, operation_id: object) -> dict | None:
        if not operation_id:
            return None
        for event in case["events"]:
            if event["operation_id"] == operation_id:
                result = deepcopy(event["result"])
                result["status"] = "already-processed"
                result["state_changed"] = False
                return result
        return None

    @staticmethod
    def _validate_update(case: dict, payload: dict, operation: str) -> None:
        required = (
            "operation_id",
            "actor_id",
            "role",
            "invocation_id",
            "previous_handoff_id",
            "expected_case_revision",
        )
        missing = [key for key in required if payload.get(key) is None]
        if missing:
            raise QualityLoopError(
                "invalid-input",
                f"更新操作の必須項目が不足しています: {', '.join(missing)}",
            )
        forbidden = sorted(set(payload) - ALLOWED_FIELDS[operation])
        if forbidden:
            raise QualityLoopError(
                "forbidden-field",
                f"{operation}が更新できない項目です: {', '.join(forbidden)}",
                remediation="Roleに許可された入力Schemaだけを提出してください。",
            )
        expected_role = EXPECTED_ROLE[operation]
        if payload["role"] != expected_role:
            raise QualityLoopError(
                "role-not-allowed",
                f"{operation}は{expected_role} Roleだけが実行できます。",
            )
        if operation == "adjudicate" and payload["actor_id"] != case["case_metadata"]["owner"]:
            raise QualityLoopError(
                "owner-identity-mismatch",
                "adjudicateは案件に登録されたOwnerだけが実行できます。",
                remediation="登録済みOwnerのactor_idで裁定してください。",
            )
        for event in case["events"]:
            if (
                event["invocation_id"] == payload["invocation_id"]
                and event["role"] != payload["role"]
            ):
                raise QualityLoopError(
                    "role-conflict",
                    "同一Invocationで複数Roleを兼務できません。",
                )
        current_revision = case["case_metadata"]["revision"]
        if payload["expected_case_revision"] != current_revision:
            raise QualityLoopError(
                "revision-conflict",
                f"期待revision {payload['expected_case_revision']} と現行revision {current_revision} が一致しません。",
                remediation="statusで最新revisionとhandoffを取得してください。",
            )
        expected_states = {EXPECTED_STATE[operation]}
        if operation == "adjudicate":
            expected_states.add("held")
        if case["case_metadata"]["status"] not in expected_states:
            raise QualityLoopError(
                "state-transition-not-allowed",
                f"現在状態では{operation}を実行できません。",
                remediation="statusが示すnext_actionを実行してください。",
            )
        handoff = case["handoff"]
        if (
            payload["previous_handoff_id"] != handoff["handoff_id"]
            or handoff["issued_revision"] != current_revision
            or handoff["next_role"] != payload["role"]
            or handoff["next_action"] != operation
        ):
            raise QualityLoopError(
                "handoff-mismatch",
                "現在handoffと操作入力が一致しません。",
                remediation="statusで最新handoffを取得してください。",
            )

    @staticmethod
    def _finish_update(
        *,
        updated: dict,
        payload: dict,
        operation: str,
        revision: int,
        state: str,
        handoff: dict,
        result: dict,
    ) -> None:
        now = utc_now()
        previous_handoff_id = updated["handoff"]["handoff_id"]
        updated["case_metadata"]["revision"] = revision
        updated["case_metadata"]["status"] = state
        updated["case_metadata"]["updated_at"] = now
        updated["handoff"] = handoff
        updated["events"].append(
            {
                "operation_id": payload["operation_id"],
                "actor_id": payload["actor_id"],
                "role": payload["role"],
                "invocation_id": payload["invocation_id"],
                "operation": operation,
                "revision": revision,
                "previous_handoff_id": previous_handoff_id,
                "handoff_acknowledged": True,
                "timestamp": now,
                "result": deepcopy(result),
            }
        )

    @staticmethod
    def _result(
        *,
        case_id: str,
        revision: int,
        state_changed: bool,
        next_role: str | None,
        next_action: str | None,
        handoff: dict | None,
        status: str = "ok",
    ) -> dict:
        return {
            "status": status,
            "case_id": case_id,
            "case_revision": revision,
            "state_changed": state_changed,
            "next_role": next_role,
            "next_action": next_action,
            "handoff": deepcopy(handoff),
        }
