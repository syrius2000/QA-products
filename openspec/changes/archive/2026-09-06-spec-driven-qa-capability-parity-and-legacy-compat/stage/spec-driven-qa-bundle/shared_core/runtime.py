"""Bundle境界、役割認可、構造化入出力を担う薄い共通実装。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class BundleError(RuntimeError):
    """安全境界違反または不正な入力。"""


def bundle_root(anchor: Path) -> Path:
    """anchorから、実ファイル位置に基づくBundleルートを返す。"""
    resolved = anchor.resolve()
    root = resolved.parent.parent
    if root.name != "spec-driven-qa-bundle":
        raise BundleError("bundle_root_unexpected")
    if resolved.is_symlink():
        raise BundleError("launcher_symlink_rejected")
    return root


def verify_manifest(root: Path) -> None:
    required = {
        "shared_core", "spec-driven-qa-review", "spec-driven-qa-author-response",
        "schemas", "templates", "fixtures", "evals",
    }
    if any(not (root / name).is_dir() for name in required):
        raise BundleError("bundle_structure_incomplete")
    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise BundleError("manifest_missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError("manifest_invalid") from exc
    for item in manifest.get("files", []):
        relative = Path(item["path"])
        target = (root / relative).resolve()
        if relative.is_absolute() or target.parent != (root / relative).parent.resolve():
            raise BundleError("manifest_path_escape")
        if not target.is_file() or target.is_symlink():
            raise BundleError("bundle_file_missing")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            raise BundleError("bundle_digest_mismatch")


def load_request(payload: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise BundleError("request_invalid_json") from exc
    if not isinstance(value, dict):
        raise BundleError("request_object_required")
    return value


def authorize(role: str, operation: str) -> None:
    allowed = {
        "reviewer": {"review", "handoff", "verify", "close", "chain-review", "chain-verify"},
        "author": {"respond", "submit", "chain-submit"},
    }
    if operation not in allowed.get(role, set()):
        raise BundleError("operation_not_authorized")


def run(role: str, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    authorize(role, operation)
    if operation.startswith("chain-"):
        from .chain import run_chain
        return run_chain(role, operation, payload)
    return {
        "status": "ok",
        "role": role,
        "operation": operation,
        "request_id": payload.get("request_id"),
    }
