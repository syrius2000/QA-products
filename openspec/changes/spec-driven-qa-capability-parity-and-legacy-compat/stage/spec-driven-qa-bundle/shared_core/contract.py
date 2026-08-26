"""契約フィールドと最小状態遷移の共有定義。"""

import re

REQUIRED_FIELDS = ("case_id", "case_revision", "case_status", "next_action", "findings", "evidence", "digest_target")
CASE_STATUSES = {"open", "needs-response", "verification-in-progress", "closed", "blocked"}
FINDING_CLASSES = {"critical", "high", "medium", "low"}
FINDING_STATUSES = {"open", "accepted", "fix-submitted", "fixed-and-verified", "risk-accepted", "not-applicable"}
EVIDENCE_STATUSES = {"verified", "unverified", "evidence-gap", "risk-accepted", "fixed-and-verified"}


def validate_contract(value: dict) -> list[str]:
    errors = [f"missing:{key}" for key in REQUIRED_FIELDS if key not in value]
    if "case_revision" in value and (not isinstance(value["case_revision"], int) or value["case_revision"] < 0):
        errors.append("invalid:case_revision")
    if "case_status" in value and value["case_status"] not in CASE_STATUSES:
        errors.append("invalid:case_status")
    if "next_action" in value and (not isinstance(value["next_action"], str) or not value["next_action"]):
        errors.append("invalid:next_action")
    for key in ("findings", "evidence"):
        if key in value and not isinstance(value[key], list):
            errors.append(f"invalid:{key}")
    for index, finding in enumerate(value.get("findings", []) if isinstance(value.get("findings"), list) else []):
        if not isinstance(finding, dict):
            errors.append(f"invalid:findings[{index}]")
            continue
        if not re.fullmatch(r"QA-[0-9]+-F[0-9]+", str(finding.get("id", ""))):
            errors.append(f"invalid:findings[{index}].id")
        if finding.get("classification") not in FINDING_CLASSES:
            errors.append(f"invalid:findings[{index}].classification")
        if finding.get("status") not in FINDING_STATUSES:
            errors.append(f"invalid:findings[{index}].status")
    for index, evidence in enumerate(value.get("evidence", []) if isinstance(value.get("evidence"), list) else []):
        if not isinstance(evidence, dict) or not evidence.get("id") or evidence.get("status") not in EVIDENCE_STATUSES:
            errors.append(f"invalid:evidence[{index}]")
    target = value.get("digest_target")
    if not isinstance(target, dict) or not isinstance(target.get("paths"), list) or not all(isinstance(path, str) and path for path in target.get("paths", [])):
        errors.append("invalid:digest_target")
    for key in ("semantic_digest", "content_digest"):
        if key in value and not re.fullmatch(r"[0-9a-f]{64}", str(value[key])):
            errors.append(f"invalid:{key}")
    return errors
