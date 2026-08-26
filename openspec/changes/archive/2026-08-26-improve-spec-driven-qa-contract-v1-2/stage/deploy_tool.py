#!/usr/bin/env python3
"""Candidate Skill Bundleのdry-run、差分、backup、rollbackを安全に検証する。"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path


ROLES = {
    "spec-driven-qa-review": "spec_driven_qa_reviewer",
    "spec-driven-qa-author-response": "spec_driven_qa_author_response",
}
FORBIDDEN_PARTS = {".pytest_cache", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc"}


class SafetyError(RuntimeError):
    """安全境界を満たせない場合に発生する。"""


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _safe_target(path: str | Path) -> Path:
    target = _resolve(path)
    home = Path.home().resolve()
    if target == Path("/") or target == home or home in target.parents:
        raise SafetyError("homeまたは広すぎる保護対象をtargetに指定できません")
    if len(target.parts) < 3:
        raise SafetyError("targetが広すぎるため拒否しました")
    return target


def _is_ignored(path: Path) -> bool:
    return any(part in FORBIDDEN_PARTS for part in path.parts) or path.suffix in FORBIDDEN_SUFFIXES


def _files(root: Path) -> list[Path]:
    if not root.is_dir():
        raise SafetyError(f"source directoryが存在しません: {root}")
    return sorted(path for path in root.rglob("*") if path.is_file() and not _is_ignored(path))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_manifest(source_root: str | Path) -> dict[str, object]:
    source = _resolve(source_root)
    roles: dict[str, dict[str, object]] = {}
    for role, directory in ROLES.items():
        role_root = source / directory
        entries = []
        for path in _files(role_root):
            entries.append({
                "path": str(path.relative_to(role_root)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            })
        roles[role] = {"source": str(role_root), "files": entries}
    return {"schema_version": "deploy-plan-1", "source_root": str(source), "roles": roles}


def _role_changes(source_root: Path, target_root: Path, role: str) -> list[dict[str, object]]:
    source_role = source_root / ROLES[role]
    target_role = target_root / role
    source_files = {str(p.relative_to(source_role)): p for p in _files(source_role)}
    target_files = {str(p.relative_to(target_role)): p for p in _files(target_role)} if target_role.is_dir() else {}
    changes: list[dict[str, object]] = []
    for relative in sorted(set(source_files) | set(target_files)):
        src = source_files.get(relative)
        dst = target_files.get(relative)
        if src is None:
            changes.append({"role": role, "path": relative, "action": "remove"})
        elif dst is None:
            changes.append({"role": role, "path": relative, "action": "add", "sha256": _sha256(src)})
        elif _sha256(src) == _sha256(dst):
            changes.append({"role": role, "path": relative, "action": "unchanged", "sha256": _sha256(src)})
        else:
            changes.append({"role": role, "path": relative, "action": "replace", "sha256": _sha256(src)})
    return changes


def deployment_plan(source_root: str | Path, target_root: str | Path) -> dict[str, object]:
    source = _resolve(source_root)
    target = _safe_target(target_root)
    changes = []
    for role in ROLES:
        changes.extend(_role_changes(source, target, role))
    return {
        "schema_version": "deploy-plan-1",
        "mode": "dry-run",
        "source_root": str(source),
        "target_root": str(target),
        "manifest": bundle_manifest(source),
        "changes": changes,
    }


def _text_diff(source: Path, target: Path, label: str) -> str:
    try:
        before = target.read_text(encoding="utf-8").splitlines(keepends=True) if target.exists() else []
        after = source.read_text(encoding="utf-8").splitlines(keepends=True)
    except (UnicodeDecodeError, OSError):
        return f"Binary or unreadable file: {label}\n"
    return "".join(difflib.unified_diff(before, after, fromfile=f"target/{label}", tofile=f"stage/{label}"))


def diff_text(source_root: str | Path, target_root: str | Path) -> str:
    source = _resolve(source_root)
    target = _safe_target(target_root)
    chunks: list[str] = []
    for role in ROLES:
        source_role = source / ROLES[role]
        target_role = target / role
        for path in _files(source_role):
            relative = path.relative_to(source_role)
            chunks.append(_text_diff(path, target_role / relative, f"{role}/{relative}"))
    return "".join(chunks)


def create_backup(target_root: str | Path, backup_root: str | Path) -> dict[str, object]:
    target = _safe_target(target_root)
    backup = _safe_target(backup_root)
    if not target.is_dir():
        raise SafetyError(f"backup対象が存在しません: {target}")
    if backup.exists():
        raise SafetyError(f"既存backupを上書きしません: {backup}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    payload = backup / "target"
    shutil.copytree(target, payload)
    manifest = {
        "schema_version": "backup-manifest-1",
        "status": "COMPLETE",
        "target_root": str(target),
        "backup_root": str(backup),
        "files": [
            {"path": str(path.relative_to(payload)), "sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in _files(payload)
        ],
    }
    (backup / "backup-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def rollback(target_root: str | Path, backup_root: str | Path, *, apply: bool, confirmation: str | None) -> dict[str, object]:
    target = _safe_target(target_root)
    backup = _safe_target(backup_root)
    payload = backup / "target"
    if not backup.is_dir() or not (backup / "backup-manifest.json").is_file() or not payload.is_dir():
        raise SafetyError("検証済みbackup-manifest.jsonのないbackupは使えません")
    if not apply:
        return {"status": "DRY-RUN", "target_root": str(target), "backup_root": str(backup)}
    if confirmation != str(target):
        raise SafetyError("rollback実行にはtarget絶対パスと一致する--confirm-targetが必要です")
    parent = target.parent
    temporary = parent / f".{target.name}.rollback-{uuid.uuid4().hex}"
    previous = parent / f".{target.name}.pre-rollback-{uuid.uuid4().hex}"
    shutil.copytree(payload, temporary)
    try:
        if target.exists():
            os.replace(target, previous)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"status": "COMPLETE", "target_root": str(target), "backup_root": str(backup), "previous_root": str(previous)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安全なstage Bundleのdry-run/backup/rollback")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "diff"):
        item = sub.add_parser(command)
        item.add_argument("--source", required=True)
        item.add_argument("--target", required=True)
        item.add_argument("--json", action="store_true")
    backup = sub.add_parser("backup")
    backup.add_argument("--target", required=True)
    backup.add_argument("--backup", required=True)
    backup.add_argument("--json", action="store_true")
    restore = sub.add_parser("rollback")
    restore.add_argument("--target", required=True)
    restore.add_argument("--backup", required=True)
    restore.add_argument("--apply", action="store_true")
    restore.add_argument("--confirm-target")
    restore.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            result = deployment_plan(args.source, args.target)
        elif args.command == "diff":
            result = {"status": "DRY-RUN", "diff": diff_text(args.source, args.target)}
        elif args.command == "backup":
            result = create_backup(args.target, args.backup)
        else:
            result = rollback(args.target, args.backup, apply=args.apply, confirmation=args.confirm_target)
        if getattr(args, "json", False) or args.command != "diff":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["diff"], end="")
        return 0
    except (OSError, SafetyError, ValueError) as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
