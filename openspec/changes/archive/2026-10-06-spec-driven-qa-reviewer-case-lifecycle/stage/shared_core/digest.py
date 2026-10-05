"""意味構造と文書内容を分離した決定論的digest。"""

import hashlib
import json
import re
from typing import Any

DIGEST_CONTRACT_VERSION = "v1"
SECRET_KEYS = {"password", "passwd", "token", "secret", "api_key", "apikey"}


def validate_digest_version(version: str) -> str:
    if version != DIGEST_CONTRACT_VERSION:
        raise ValueError("unsupported-digest-version")
    return version


def _digest(namespace: str, value: Any) -> str:
    _reject_secrets(value)
    payload = {"namespace": namespace, "value": value}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reject_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in SECRET_KEYS:
                raise ValueError("secret-in-digest-input")
            _reject_secrets(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_secrets(child)


def semantic_digest(value: Any) -> str:
    """意思決定に影響する正規化済み構造をdigestする。"""
    return _digest("qa-semantic-v1", value)


def content_digest(value: Any) -> str:
    """handoff等の正規化文書内容をdigestする。"""
    return _digest("qa-content-v1", value)


def normalize_handoff_content(text: str) -> str:
    """digest自身と生成時刻を除いたhandoff本文を正規化する。"""
    kept = []
    for line in text.replace("\r\n", "\n").splitlines():
        if re.match(r"^\s*-?\s*(semantic_digest|content_digest|created_at):", line):
            continue
        kept.append(line.rstrip())
    return "\n".join(kept).strip() + "\n"


def handoff_content_digest(text: str) -> str:
    """handoff本文の実測content digestを返す。"""
    return content_digest(normalize_handoff_content(text))


def canonical_handoff_content(
    case_id: str,
    open_finding_ids: list[str],
    cycle: int,
    case_revision: str = "",
) -> str:
    ids = sorted(open_finding_ids)
    lines = [
        "# QA Review Handoff Contract",
        "",
        '- schema_version: "1.2"',
        f'- digest_version: "{DIGEST_CONTRACT_VERSION}"',
        f"- case_id: {case_id}",
        f"- cycle: {cycle}",
        f"- case_revision: {case_revision}",
        "- content_digest: {CONTENT_DIGEST}",
        "- semantic_digest: {SEMANTIC_DIGEST}",
        "- created_at: {CREATED_AT}",
        "- origin_role: reviewer",
        "- implementation_permission: scoped",
        f"- open_finding_ids: {json.dumps(ids)}",
        "",
        "## Active Open Findings",
        "",
    ]
    lines.extend(f"- `{finding_id}`: Awaiting author response or fix submission." for finding_id in ids)
    return "\n".join(lines) + "\n"


def handoff_digests(
    case_id: str,
    open_finding_ids: list[str],
    cycle: int,
    case_revision: str = "",
) -> dict[str, str]:
    """Reviewer/Author共通のhandoff digest入力を返す。"""
    ids = sorted(open_finding_ids)
    semantic_value = {
        "case_id": case_id,
        "open_finding_ids": ids,
        "cycle": cycle,
        "case_revision": case_revision,
    }
    content_value = normalize_handoff_content(canonical_handoff_content(case_id, ids, cycle, case_revision))
    return {
        "semantic_digest": semantic_digest(semantic_value),
        "content_digest": content_digest(content_value),
    }
