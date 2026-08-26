"""Bundle境界、役割認可、構造化入出力を担う薄い共通実装。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


class BundleError(RuntimeError):
    """安全境界違反または不正な入力。"""


def bundle_root(anchor: Path) -> Path:
    """anchorから、実ファイル位置に基づくBundleルートを返す。"""
    resolved = anchor.resolve()
    root = resolved.parent.parent
    if not (root / "shared_core").is_dir():
        raise BundleError("bundle_root_unexpected")
    if resolved.is_symlink():
        raise BundleError("launcher_symlink_rejected")
    return root


def verify_manifest(root: Path) -> None:
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
        "reviewer": {"review", "handoff", "verify", "close"},
        "author": {"respond", "submit"},
    }
    if operation not in allowed.get(role, set()):
        raise BundleError("operation_not_authorized")


def _get_reviewer_lifecycle(root: Path, qa_root: str, role: str):
    pkg_dir = root / "spec-driven-qa-review"
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    
    # Register package alias if needed
    if "spec_driven_qa_review" not in sys.modules:
        init_file = pkg_dir / "__init__.py"
        if init_file.exists():
            spec = importlib.util.spec_from_file_location("spec_driven_qa_review", str(init_file))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules["spec_driven_qa_review"] = mod
                mod.__path__ = [str(pkg_dir)]
                spec.loader.exec_module(mod)
    
    try:
        from spec_driven_qa_review.lifecycle import ReviewerLifecycle
        return ReviewerLifecycle(qa_root=qa_root, role=role)
    except Exception:
        spec = importlib.util.spec_from_file_location("lifecycle", str(pkg_dir / "lifecycle.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.ReviewerLifecycle(qa_root=qa_root, role=role)


def run(role: str, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    authorize(role, operation)
    
    if role == "reviewer":
        root = bundle_root(Path(__file__))
        qa_root = payload.get("qa_root", "docs/ADR/QA")
        lifecycle = _get_reviewer_lifecycle(root, qa_root, role)
        action = payload.get("action", operation)
        case_id = payload.get("case_id")
        
        if action == "init" or (operation == "review" and action == "init"):
            return lifecycle.init_case(
                case_id=case_id,
                target=payload.get("target", ""),
                purpose=payload.get("purpose", ""),
                profile=payload.get("profile", "standard"),
                title=payload.get("title", "QA Review Case"),
            )
        elif operation == "review":
            return lifecycle.record_findings(
                case_id=case_id,
                findings=payload.get("findings", []),
                cycle=payload.get("cycle", 1),
            )
        elif operation == "handoff":
            return lifecycle.render_handoff(
                case_id=case_id,
                cycle=payload.get("cycle", 1),
                case_revision=payload.get("case_revision", "rev-001"),
            )
        elif operation == "verify":
            return lifecycle.verify_submission(
                case_id=case_id,
                submission=payload.get("submission", {}),
                cycle=payload.get("cycle", 1),
            )
        elif operation == "close":
            return lifecycle.close_case(
                case_id=case_id,
                terminal_status=payload.get("terminal_status", "accepted"),
                rationale=payload.get("rationale", ""),
            )

    return {
        "status": "ok",
        "role": role,
        "operation": operation,
        "request_id": payload.get("request_id"),
    }
