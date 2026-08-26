"""CLI JSON、event、handoffへ秘密値を出力しないための検出・マスク。"""

from __future__ import annotations

import re
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"(?i)(token|password|secret|api[_-]?key)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)bearer\s+([A-Za-z0-9._-]+)"),
    re.compile(r"\b(?:sk|ghp)_[A-Za-z0-9_-]{8,}\b"),
)


def sanitize_text(value: str) -> str:
    value = SECRET_PATTERNS[0].sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    value = SECRET_PATTERNS[1].sub("Bearer [REDACTED]", value)
    return SECRET_PATTERNS[2].sub("[REDACTED]", value)


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    return value
