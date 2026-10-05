"""Contract v1.2の意味フィールドを安定JSONへ正規化してdigestを計算する。"""

from __future__ import annotations

import hashlib
import json
from typing import Any


CASE_SEMANTIC_KEYS = (
    "contract_version",
    "schema_version",
    "case_id",
    "case_status",
    "next_action",
    "case_revision",
    "quality_intent",
    "target_scope",
    "terminal_result",
)
FINDING_SEMANTIC_KEYS = (
    "id",
    "severity",
    "finding_status",
    "technical_status",
    "required_evidence",
    "implementation_permission",
    "base_revision",
)


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def semantic_view(document: dict[str, Any]) -> dict[str, Any]:
    """表示用フィールドとイベント履歴を除いたdigest対象を返す。"""
    view = {
        key: _normalize(document[key])
        for key in CASE_SEMANTIC_KEYS
        if key in document
    }
    findings = []
    for finding in document.get("findings", []):
        findings.append({
            key: _normalize(finding[key])
            for key in FINDING_SEMANTIC_KEYS
            if key in finding
        })
    view["findings"] = sorted(findings, key=lambda finding: finding.get("id", ""))
    return view


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(
        semantic_view(document),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def semantic_digest(document: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()
