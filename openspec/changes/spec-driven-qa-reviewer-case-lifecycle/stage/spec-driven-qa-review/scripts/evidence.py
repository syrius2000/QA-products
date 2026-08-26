"""Evidenceの要求、実体、検証結果、秘密値を検証する。"""

from __future__ import annotations

import re
from typing import Any


RESULTS = {"verified", "unverified", "evidence-gap", "not-applicable"}
REFERENCE_TYPES = {"repository-relative", "external-url", "external-absolute"}
SECRET_PATTERN = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._-]+|(?:token|password|api[_-]?key|secret)\s*[:=]\s*\S+)"
)


def validate_requirement(requirement: Any) -> list[str]:
    if not isinstance(requirement, dict):
        return ["required evidence item must be an object"]
    errors = []
    for key in ("id", "description"):
        if not isinstance(requirement.get(key), str) or not requirement[key].strip():
            errors.append(f"required evidence field is missing: {key}")
    return errors


def validate_evidence(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["evidence record must be an object"]
    errors = []
    required = {"id", "reference", "reference_type", "verifier", "acquired_at", "result", "secret_status"}
    errors.extend(f"evidence field is missing: {key}" for key in sorted(required - record.keys()))
    if errors:
        return errors
    for key in ("id", "reference", "verifier", "acquired_at"):
        if not isinstance(record[key], str) or not record[key].strip():
            errors.append(f"evidence field must be a non-empty string: {key}")
    if record["reference_type"] not in REFERENCE_TYPES:
        errors.append("evidence reference_type is invalid")
    if record["result"] not in RESULTS:
        errors.append("evidence result is invalid")
    if record["secret_status"] not in {"none", "masked", "rejected"}:
        errors.append("evidence secret_status is invalid")
    for key in ("reference", "summary"):
        value = record.get(key, "")
        if isinstance(value, str) and SECRET_PATTERN.search(value):
            errors.append("evidence contains an unmasked secret")
    if record["secret_status"] == "rejected":
        errors.append("evidence with rejected secret_status must not be submitted")
    return errors


def validate_evidence_bundle(bundle: Any) -> list[str]:
    if not isinstance(bundle, dict):
        return ["evidence bundle must be an object"]
    errors = []
    errors.extend(validate_requirement(item) for item in bundle.get("required_evidence", []))
    errors.extend(validate_evidence(item) for item in bundle.get("evidence", []))
    return [error for group in errors for error in (group if isinstance(group, list) else [group])]


def is_success(record: dict[str, Any]) -> bool:
    """取得不能や証拠不足を成功扱いしない。"""
    return record.get("result") == "verified" and record.get("secret_status") in {"none", "masked"}
