"""旧Contract v1.0/v1.1を読み取り専用で正規化する。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_LEGACY_VERSIONS = {"1.0", "1.1"}


class UnsupportedContractVersion(ValueError):
    """未知majorまたは未対応minorのContractを示す。"""

    def __init__(self, version: str):
        super().__init__(f"blocked: unsupported-contract-version: {version}")
        self.version = version


def _version(document: dict[str, Any]) -> str:
    value = document.get("contract_version", document.get("handoff_contract_version"))
    if not isinstance(value, str) or not value:
        raise UnsupportedContractVersion("missing")
    return value


def read_legacy(document: dict[str, Any]) -> dict[str, Any]:
    """旧文書を変更せず、Contract v1.2移行時の読み取りビューを返す。"""
    version = _version(document)
    if version not in SUPPORTED_LEGACY_VERSIONS:
        raise UnsupportedContractVersion(version)
    return {
        "source_contract_version": version,
        "read_only": True,
        "case_id": document.get("case_id", document.get("id")),
        "case_status": document.get("case_status", document.get("status")),
        "case_revision": document.get("case_revision", 0),
        "findings": deepcopy(document.get("findings", [])),
    }
