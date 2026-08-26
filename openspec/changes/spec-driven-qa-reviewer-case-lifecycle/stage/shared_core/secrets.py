"""診断出力へ秘密値を漏らさないための最小検出器。"""

import re

SECRET_PATTERNS = (re.compile(r"(?i)\b(token|password|secret|api[_-]?key)\s*=\s*[^\s]+"),)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def safe_diagnostic(code: str, detail: str = "") -> dict[str, str]:
    return {"status": "error", "code": code} if contains_secret(detail) else {"status": "error", "code": code, "detail": detail}
