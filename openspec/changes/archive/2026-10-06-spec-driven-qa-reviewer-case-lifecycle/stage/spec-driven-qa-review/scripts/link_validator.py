"""Repository内外のEvidence参照形式を検証する。"""

from __future__ import annotations

from urllib.parse import urlparse


def validate_reference(reference: str, reference_type: str) -> list[str]:
    if not isinstance(reference, str) or not reference:
        return ["reference must be a non-empty string"]
    if reference.startswith("file://"):
        return ["file:// references are not accepted"]
    if reference_type == "repository-relative":
        if reference.startswith("/"):
            return ["repository references must be relative"]
        if urlparse(reference).scheme:
            return ["repository references must not use an external URL scheme"]
        return []
    if reference_type == "external-url" and urlparse(reference).scheme not in {"http", "https"}:
        return ["external-url references require http or https"]
    if reference_type == "external-absolute" and not reference.startswith("/"):
        return ["external-absolute references require an absolute path"]
    if reference_type not in {"external-url", "external-absolute"}:
        return ["reference_type is invalid"]
    return []
