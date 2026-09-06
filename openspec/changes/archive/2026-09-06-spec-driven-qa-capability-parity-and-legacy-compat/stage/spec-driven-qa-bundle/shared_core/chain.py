"""ReviewerからAuthorへ受け渡す最小の連鎖API。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class ChainError(ValueError):
    """連鎖契約、権限、digest、revisionの違反。"""


FINDING_ID = re.compile(r"QA-[0-9]+-F[0-9]+\Z")
CASE_ID = re.compile(r"QA-[0-9]+\Z")
SUBMISSION_ID = re.compile(r"submission-[A-Za-z0-9_-]+\Z")
HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
SECRET_KEY = re.compile(r"(?i)(api[_-]?key|token|password|secret)")
SECRET_VALUE = re.compile(r"(?i)(bearer\s+\S+|api[_-]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+|secret\s*[:=]\s*\S+)")
DISPOSITIONS = {"accepted", "rejected-with-evidence", "fix-submitted", "deferred", "risk-accepted", "not-applicable"}
REVIEWER_OWNED = {"finding", "severity", "verification", "events", "closure", "case_status", "terminal_result"}
DIGEST_VERSION = "v1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _secret(value: Any, path: str = "root") -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if SECRET_KEY.search(str(key)):
                return True
            if _secret(item, f"{path}.{key}"):
                return True
    if isinstance(value, list):
        return any(_secret(item, f"{path}[]") for item in value)
    return isinstance(value, str) and bool(SECRET_VALUE.search(value))


def _workspace(payload: dict[str, Any]) -> Path:
    value = payload.get("workspace")
    if not isinstance(value, str) or not value:
        raise ChainError("workspace_required")
    workspace = Path(value).expanduser()
    if not workspace.is_absolute():
        raise ChainError("workspace_must_be_absolute")
    if workspace.exists() and workspace.is_symlink():
        raise ChainError("workspace_symlink_rejected")
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace.resolve()


def _validate_target_boundary(payload: dict[str, Any], workspace: Path) -> None:
    value = payload.get("fixture_path", payload.get("target_path"))
    if not isinstance(value, str) or not value:
        return
    target = Path(value).expanduser()
    if not target.is_absolute():
        return
    resolved = target.resolve()
    if resolved != workspace and workspace not in resolved.parents:
        raise ChainError("workspace_boundary_violation")


def _digest_version(payload: dict[str, Any], expected: str = DIGEST_VERSION) -> str:
    value = payload.get("digest_version", DIGEST_VERSION)
    if value != expected:
        raise ChainError("unsupported-digest-version")
    return value


def _case_id(payload: dict[str, Any]) -> str:
    value = payload.get("case_id", "QA-9000")
    if not isinstance(value, str) or not CASE_ID.fullmatch(value):
        raise ChainError("invalid_case_id")
    return value


def _paths(workspace: Path, case_id: str) -> tuple[Path, Path, Path]:
    case_dir = workspace / "qa-cases" / case_id
    return case_dir, case_dir / "case.json", case_dir / "handoff.md"


def _findings(case_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("findings", [{"id": f"{case_id}-F01", "severity": "medium", "status": "open"}])
    if not isinstance(raw, list) or not raw:
        raise ChainError("findings_required")
    findings = []
    for finding in raw:
        if not isinstance(finding, dict) or not FINDING_ID.fullmatch(str(finding.get("id", ""))):
            raise ChainError("invalid_finding_id")
        if not str(finding["id"]).startswith(case_id + "-"):
            raise ChainError("finding_case_mismatch")
        findings.append({
            "id": finding["id"],
            "severity": finding.get("severity", "medium"),
            "status": "open",
            "classification": finding.get("classification", "spec-required"),
        })
    return findings


def chain_review(payload: dict[str, Any]) -> dict[str, Any]:
    if _secret(payload):
        raise ChainError("secret-in-chain-input")
    workspace = _workspace(payload)
    _validate_target_boundary(payload, workspace)
    digest_version = _digest_version(payload)
    case_id = _case_id(payload)
    case_dir, case_path, handoff_path = _paths(workspace, case_id)
    if case_path.exists() or handoff_path.exists():
        raise ChainError("case_already_exists")
    findings = _findings(case_id, payload)
    semantic = {
        "contract_version": "1.2",
        "schema_version": "qa-case-v1.2",
        "case_id": case_id,
        "case_status": "needs-response",
        "next_action": "author-response",
        "case_revision": 1,
        "digest_version": digest_version,
        "findings": findings,
    }
    semantic_digest = _digest(semantic)
    body = "# QA Handoff\n\n" + json.dumps({"case_id": case_id, "findings": findings}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    content_digest = _digest(body)
    handoff = (
        "---\n"
        "document_type: spec-driven-qa-handoff\n"
        "contract_version: \"1.2\"\n"
        f"case_id: {case_id}\n"
        "case_revision: 1\n"
        "case_status: needs-response\n"
        "next_action: author-response\n"
        f"semantic_digest: {semantic_digest}\n"
        f"content_digest: {content_digest}\n"
        f"digest_version: {digest_version}\n"
        "implementation_permission: scoped\n"
        "recipient_role: implementer\n"
        "---\n\n"
        + body
    )
    record = {**semantic, "semantic_digest": semantic_digest, "content_digest": content_digest, "handoff": "handoff.md"}
    case_dir.mkdir(parents=True, exist_ok=False)
    case_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    handoff_path.write_text(handoff, encoding="utf-8")
    return {"status": "ok", "operation": "chain-review", "case_id": case_id, "case_revision": 1, "digest_version": digest_version, "semantic_digest": semantic_digest, "content_digest": content_digest, "finding_ids": [item["id"] for item in findings], "handoff": "qa-cases/" + case_id + "/handoff.md"}


def _load_case(payload: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    workspace = _workspace(payload)
    case_id = _case_id(payload)
    _, case_path, handoff_path = _paths(workspace, case_id)
    if not case_path.is_file() or not handoff_path.is_file():
        raise ChainError("case_or_handoff_missing")
    try:
        case = json.loads(case_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChainError("case_invalid") from exc
    return case_path, case


def chain_submit(payload: dict[str, Any]) -> dict[str, Any]:
    if _secret(payload):
        raise ChainError("secret-in-chain-input")
    case_path, case = _load_case(payload)
    _digest_version(payload, str(case.get("digest_version", DIGEST_VERSION)))
    if case.get("case_status") != "needs-response":
        raise ChainError("case_not_accepting_submission")
    if str(payload.get("base_revision")) != str(case.get("case_revision")):
        raise ChainError("base_revision_mismatch")
    if payload.get("expected_semantic_digest") != case.get("semantic_digest"):
        raise ChainError("semantic_digest_mismatch")
    if payload.get("expected_content_digest") != case.get("content_digest"):
        raise ChainError("content_digest_mismatch")
    submission_id = payload.get("submission_id")
    if not isinstance(submission_id, str) or not SUBMISSION_ID.fullmatch(submission_id):
        raise ChainError("invalid_submission_id")
    target_findings = payload.get("target_findings")
    responses = payload.get("responses")
    known = {item["id"] for item in case.get("findings", [])}
    if not isinstance(target_findings, list) or set(target_findings) != known:
        raise ChainError("target_findings_mismatch")
    if not isinstance(responses, dict) or set(responses) != known:
        raise ChainError("unanswered_finding")
    for finding_id, response in responses.items():
        if not isinstance(response, dict) or response.get("disposition") not in DISPOSITIONS:
            raise ChainError(f"invalid_disposition:{finding_id}")
        if REVIEWER_OWNED.intersection(response):
            raise ChainError("reviewer_owned_field_rejected")
    if REVIEWER_OWNED.intersection(payload):
        raise ChainError("reviewer_owned_field_rejected")
    submission = {
        "submission_id": submission_id,
        "base_revision": case["case_revision"],
        "expected_semantic_digest": case["semantic_digest"],
        "expected_content_digest": case["content_digest"],
        "target_findings": target_findings,
        "responses": responses,
    }
    destination = case_path.parent / "submissions" / f"{submission_id}.json"
    if destination.exists():
        raise ChainError("submission_already_exists")
    destination.parent.mkdir(parents=True, exist_ok=False)
    destination.write_text(json.dumps(submission, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "ok", "operation": "chain-submit", "case_id": case["case_id"], "submission_id": submission_id, "base_revision": case["case_revision"], "submission": str(destination.relative_to(case_path.parent.parent.parent))}


def chain_verify(payload: dict[str, Any]) -> dict[str, Any]:
    if _secret(payload):
        raise ChainError("secret-in-chain-input")
    case_path, case = _load_case(payload)
    _validate_target_boundary(payload, _workspace(payload))
    _digest_version(payload, str(case.get("digest_version", DIGEST_VERSION)))
    submission_id = payload.get("submission_id")
    if not isinstance(submission_id, str) or not SUBMISSION_ID.fullmatch(submission_id):
        raise ChainError("invalid_submission_id")
    submission_path = case_path.parent / "submissions" / f"{submission_id}.json"
    if not submission_path.is_file():
        raise ChainError("submission_missing")
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    if submission.get("base_revision") != case.get("case_revision") or submission.get("expected_semantic_digest") != case.get("semantic_digest") or submission.get("expected_content_digest") != case.get("content_digest"):
        raise ChainError("submission_freshness_failed")
    verification = {"status": "verified", "submission_id": submission_id, "case_revision": case["case_revision"], "semantic_digest": case["semantic_digest"], "content_digest": case["content_digest"]}
    verification_path = case_path.parent / "verification.json"
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    case["case_status"] = "verification-in-progress"
    case["next_action"] = "reviewer-verification"
    case_path.write_text(json.dumps(case, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "ok", "operation": "chain-verify", "case_id": case["case_id"], "submission_id": submission_id, "verification": "verified", "case_revision": case["case_revision"]}


def run_chain(role: str, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"reviewer": {"chain-review", "chain-verify"}, "author": {"chain-submit"}}
    if operation not in allowed.get(role, set()):
        raise ChainError("operation_not_authorized")
    if operation == "chain-review":
        return chain_review(payload)
    if operation == "chain-submit":
        return chain_submit(payload)
    return chain_verify(payload)
