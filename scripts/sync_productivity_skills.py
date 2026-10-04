#!/usr/bin/env python3
"""Productivity-Skill の管理対象Skillだけを安全に同期する。"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path


SKILL_NAMES = ("quality-review", "quality-response", "quality-qa")
FORBIDDEN_NAMES = {"__pycache__", ".pytest_cache"}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_skills_root() -> Path:
    return repository_root() / "quality-loop" / "skills"


def run_git(destination: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(destination), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} に失敗しました: {detail}")
    return result.stdout.strip()


def ensure_productivity_repository(destination: Path) -> None:
    if not destination.is_dir():
        raise RuntimeError(f"宛先ディレクトリがありません: {destination}")
    try:
        run_git(destination, "rev-parse", "--show-toplevel")
    except RuntimeError as exc:
        raise RuntimeError(f"Gitリポジトリを確認できません: {destination}") from exc
    try:
        remote = run_git(destination, "remote", "get-url", "origin")
    except RuntimeError:
        remote = ""

    normalized = remote.rstrip("/").removesuffix(".git").lower()
    accepted = {
        "https://github.com/syrius2000/productivity-skill",
        "git@github.com:syrius2000/productivity-skill",
    }
    if normalized and normalized not in accepted:
        raise RuntimeError(
            "宛先originがsyrius2000/Productivity-Skillと一致しません。"
        )
    if not normalized:
        marker = destination / "README.md"
        marker_text = marker.read_text(encoding="utf-8") if marker.exists() else ""
        if "Productivity-Skill" not in marker_text:
            raise RuntimeError(
                "宛先がsyrius2000/Productivity-Skillと確認できません。"
            )


def ensure_source_skill(skill_dir: Path, skill_name: str) -> None:
    runtime_package = "qa_workflow" if skill_name == "quality-qa" else "quality_loop"
    required = (
        skill_dir / "SKILL.md",
        skill_dir / "VERSION",
        skill_dir / "bin" / f"{skill_name}-cli",
        skill_dir / "runtime" / runtime_package / "__init__.py",
    )
    missing = [str(path.relative_to(skill_dir)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"{skill_name} の必須ファイルがありません: {', '.join(missing)}")

    generated = [
        path
        for path in skill_dir.rglob("*")
        if path.name in FORBIDDEN_NAMES or path.suffix == ".pyc"
    ]
    if generated:
        names = ", ".join(str(path.relative_to(skill_dir)) for path in generated)
        raise RuntimeError(f"配布対象に生成物があります: {names}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for name, file_digest in sorted(manifest(root).items()):
        digest.update(f"{name}\0{file_digest}\n".encode("utf-8"))
    return digest.hexdigest()


def compare(source: Path, destination: Path) -> tuple[list[str], list[str], list[str]]:
    source_manifest = manifest(source)
    destination_manifest = manifest(destination)
    added = sorted(set(source_manifest) - set(destination_manifest))
    removed = sorted(set(destination_manifest) - set(source_manifest))
    changed = sorted(
        name
        for name in set(source_manifest) & set(destination_manifest)
        if source_manifest[name] != destination_manifest[name]
    )
    return added, changed, removed


def git_is_dirty(destination: Path) -> bool:
    return bool(run_git(destination, "status", "--porcelain", "--untracked-files=all"))


def print_plan(source_root: Path, destination_root: Path) -> bool:
    has_changes = False
    for skill_name in SKILL_NAMES:
        source = source_root / skill_name
        destination = destination_root / skill_name
        added, changed, removed = compare(source, destination)
        print(f"[{skill_name}]")
        for label, paths in (("追加", added), ("変更", changed), ("削除", removed)):
            for path in paths:
                print(f"{label}: {path}")
        if added or changed or removed:
            has_changes = True
        if not (added or changed or removed):
            print("差分なし")
    return has_changes


def version(path: Path) -> str:
    value = (path / "VERSION").read_text(encoding="utf-8").strip()
    if not value:
        raise RuntimeError(f"VERSIONが空です: {path}")
    return value


def validate_package_replacement(source: Path, destination: Path, accepted_old_version: str | None) -> None:
    if not destination.exists():
        return
    added, changed, removed = compare(source, destination)
    source_version = version(source)
    destination_version = version(destination)
    if removed:
        raise RuntimeError(f"宛先Skillにコピー元にない追加ファイルがあります。保護のため上書きしません: {destination.name}: {removed}")
    if source_version == destination_version and (added or changed):
        raise RuntimeError(f"同じVERSION `{source_version}` で内容差異があります。未知差異を保護するため停止します: {destination.name}: {added + changed}")
    if (added or changed) and accepted_old_version != destination_version:
        raise RuntimeError(f"{destination.name} の更新には既存VERSION `{destination_version}` を明示した --replace-version {destination.name}={destination_version} が必要です")


def copy_skill(source: Path, destination: Path, temp_root: Path) -> Path:
    staged = temp_root / destination.name
    shutil.copytree(source, staged)
    return staged


def sync(source_root: Path, destination_root: Path) -> None:
    parent = destination_root.parent
    parent.mkdir(parents=True, exist_ok=True)
    backup_root = parent / f".quality-loop-sync-backup-{uuid.uuid4().hex}"
    staged_root = Path(tempfile.mkdtemp(prefix=".quality-loop-sync-", dir=parent))
    moved: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    completed = False
    try:
        destination_root.mkdir(parents=True, exist_ok=True)
        backup_root.mkdir()
        for skill_name in SKILL_NAMES:
            source = source_root / skill_name
            destination = destination_root / skill_name
            staged = copy_skill(source, destination, staged_root)
            backup = backup_root / skill_name
            if destination.exists():
                shutil.move(str(destination), str(backup))
                moved.append((destination, backup))
            shutil.move(str(staged), str(destination))
            installed.append(destination)

        for skill_name in SKILL_NAMES:
            source = source_root / skill_name
            destination = destination_root / skill_name
            if manifest(source) != manifest(destination):
                raise RuntimeError(f"同期後の同一性検査に失敗しました: {skill_name}")
        completed = True
    except Exception:
        try:
            for destination in installed:
                if destination.exists():
                    shutil.rmtree(destination)
            for destination, backup in reversed(moved):
                if backup.exists():
                    shutil.move(str(backup), str(destination))
        except Exception as restore_error:
            raise RuntimeError(
                f"同期に失敗し、元のSkillの復元にも失敗しました。バックアップを保持しています: {backup_root}"
            ) from restore_error
        raise
    finally:
        shutil.rmtree(staged_root, ignore_errors=True)
        if completed:
            shutil.rmtree(backup_root, ignore_errors=True)


def write_record(
    record_path: Path,
    source_root: Path,
    destination_root: Path,
    source_revision: str,
    destination_revision: str,
    source_tag: str,
) -> None:
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    lines = [
        "# Quality Loop同期記録",
        "",
        f"created: {now:%Y-%m-%d %H:%M} (JST)",
        f"update: {now:%Y-%m-%d %H:%M} (JST)",
        "author: Codex (GPT-5)",
        "",
        "## 同期結果",
        "",
        f"- コピー元: `{source_root}`",
        f"- コピー先: `{destination_root}`",
        f"- コピー元revision: `{source_revision}`",
        f"- コピー先revision: `{destination_revision}`",
        f"- コピー元tag: `{source_tag or '未指定'}`",
        f"- 同期日時: `{now:%Y-%m-%d %H:%M:%S %z}`",
        "",
        "## 対象Skill",
        "",
    ]
    for skill_name in SKILL_NAMES:
        lines.append(f"- `{skill_name}`: 同期済み、tree SHA-256 `{tree_digest(source_root / skill_name)}`")
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=None,
        help="Productivity-Skillのパス（省略時は../Productivity-Skill）",
    )
    parser.add_argument("--dry-run", action="store_true", help="差分だけ表示する")
    parser.add_argument(
        "--force",
        action="store_true",
        help="後方互換のため受け付けるが、dirty宛先の同期を強制する機能はありません",
    )
    parser.add_argument("--replace-version", action="append", default=[], metavar="SKILL=VERSION", help="差分確認済みの宛先Skill版を指定して置換を認可する（skill単位）")
    parser.add_argument("--record", type=Path, help="同期記録の出力先")
    parser.add_argument("--tag", default="", help="コピー元の確定tag")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = repository_root()
    source_root = source_skills_root()
    destination_root = (args.destination or root.parent / "Productivity-Skill").resolve()
    try:
        accepted_versions = {}
        for item in args.replace_version:
            if "=" not in item:
                raise RuntimeError("--replace-versionはSKILL=VERSION形式で指定してください")
            name, value = item.split("=", 1)
            if name not in SKILL_NAMES or not value or name in accepted_versions:
                raise RuntimeError(f"--replace-versionの対象または指定が不正です: {item}")
            accepted_versions[name] = value
        for skill_name in SKILL_NAMES:
            ensure_source_skill(source_root / skill_name, skill_name)
        ensure_productivity_repository(destination_root)
        target_skills = destination_root / ".agents" / "skills"
        has_changes = print_plan(source_root, target_skills)
        for skill_name in SKILL_NAMES:
            validate_package_replacement(source_root / skill_name, target_skills / skill_name, accepted_versions.get(skill_name))
        if args.dry_run:
            return 0
        if not has_changes:
            return 0
        dirty = git_is_dirty(destination_root)
        if dirty:
            raise RuntimeError(
                "宛先Gitワークツリーに未コミット変更があります。Skill単位の--replace-versionはdirty状態を上書きしません。"
            )
        if args.record is None:
            raise RuntimeError("実同期には--recordで同期記録の出力先を指定してください。")
        sync(source_root, target_skills)
        source_revision = run_git(root, "rev-parse", "HEAD")
        destination_revision = run_git(destination_root, "rev-parse", "HEAD")
        write_record(
            args.record.resolve(),
            source_root,
            target_skills,
            source_revision,
            destination_revision,
            args.tag,
        )
        print(f"同期完了: {destination_root}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"停止: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
