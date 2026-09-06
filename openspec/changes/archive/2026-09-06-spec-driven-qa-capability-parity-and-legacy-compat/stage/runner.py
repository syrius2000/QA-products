#!/usr/bin/env python3
"""三版へ同一fixtureを投入し、版別Run証跡を保存する標準ライブラリRunner。

LegacyとCandidateにはcompactと共通の単一JSON Launcherがないため、未定義の
版別Adapterを実行したことにしない。入力と未検証理由を保存し、共通Adapterが
実装された場合だけ実行結果をObservedとして記録する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import parity_harness


FIXTURE_CLASSES = ("golden", "negative", "cross-skill", "legacy-compat", "size")
SUPPORTED_BUNDLES = ("legacy", "candidate", "compact")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_fixture_suite(stage: Path) -> dict[str, dict[str, Any]]:
    """fixture-indexと実体を読み、fixture digest付きの入力集合を返す。"""
    index_path = stage / "evidence" / "fixture-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("schema_version") != "fixture-index-1":
        raise ValueError("unsupported fixture index schema")
    if set(index.get("classes", {})) != set(FIXTURE_CLASSES):
        raise ValueError("fixture classes are incomplete")
    fixtures: dict[str, dict[str, Any]] = {}
    for fixture_class in FIXTURE_CLASSES:
        relative = index["classes"][fixture_class]["fixture"]
        fixture_path = (stage / relative).resolve()
        if fixture_path.parent != (stage / "fixtures").resolve() or not fixture_path.is_file():
            raise ValueError(f"fixture path escapes fixture directory: {relative}")
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "parity-fixture-1" or payload.get("class") != fixture_class:
            raise ValueError(f"fixture metadata mismatch: {fixture_class}")
        fixtures[fixture_class] = {
            "class": fixture_class,
            "path": relative,
            "digest": digest_json(payload),
            "payload": payload,
        }
    return fixtures


def compact_command(bundle_root: Path, fixture_class: str, input_path: Path) -> list[str]:
    """compactの役割入口をfixture種別に対応付ける。"""
    role = "author" if fixture_class == "negative" else "reviewer"
    operation = "close" if fixture_class == "negative" else (
        "handoff" if fixture_class == "cross-skill" else "review"
    )
    launcher_name = "spec-driven-qa-review" if role == "reviewer" else "spec-driven-qa-author-response"
    launcher = bundle_root / launcher_name / "launcher.py"
    request = json.dumps(
        {"request_id": f"parity-{fixture_class}", "fixture_class": fixture_class, "fixture_path": input_path.name},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return [sys.executable, "-B", str(launcher), operation, "--json", request]


def adapter_for(bundle_name: str, fixture_class: str, bundle_root: Path, input_path: Path, workdir: Path) -> tuple[list[str] | None, str, dict[str, str]]:
    if bundle_name == "compact":
        return compact_command(bundle_root, fixture_class, input_path), "compact JSON Launcher", {}
    if bundle_name not in {"legacy", "candidate"}:
        raise ValueError(f"unknown bundle: {bundle_name}")

    if bundle_name == "legacy":
        reviewer_root = bundle_root / "spec-driven-qa-review"
        author_root = bundle_root / "spec-driven-qa-author-response"
        environment = {}
    else:
        reviewer_root = bundle_root / "spec_driven_qa_reviewer"
        author_root = bundle_root / "spec_driven_qa_author_response"
        environment = {"PYTHONPATH": str(bundle_root)}

    if fixture_class in {"golden", "cross-skill", "legacy-compat"}:
        script = reviewer_root / "scripts" / "create_review_case.py"
        return (
            [sys.executable, "-B", str(script), "--root", str(workdir), "--title", f"parity-{fixture_class}",
             "--target", "fixture-input", "--profile", "lite"],
            f"{bundle_name} Reviewer create_review_case.py",
            environment,
        )
    if fixture_class == "negative":
        script = author_root / "scripts" / "validate_author_response.py"
        return (
            [sys.executable, "-B", str(script), str(workdir / "missing-case"), str(input_path)],
            f"{bundle_name} Author validate_author_response.py (negative)",
            environment,
        )
    script = reviewer_root / "scripts" / "create_review_case.py"
    return [sys.executable, "-B", str(script), "--help"], f"{bundle_name} Reviewer CLI help", environment


def safe_extract_zip(source: Path, target: Path) -> Path:
    """ZIPのTraversalとsymlinkを拒否して一時Bundleへ展開する。"""
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            name = info.filename.rstrip("/")
            if not name:
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"symlink is not allowed in archive: {name}")
            destination = (target / name).resolve()
            try:
                destination.relative_to(target.resolve())
            except ValueError as exc:
                raise ValueError(f"archive path escapes temporary root: {name}") from exc
        archive.extractall(target)
    roots = [path for path in target.iterdir() if path.is_dir()]
    if len(roots) != 2:
        raise ValueError("Legacy archive must contain reviewer and author roots")
    return target


def file_snapshot(root: Path, *, excluded_parts: set[str] | None = None) -> list[dict[str, Any]]:
    excluded_parts = excluded_parts or set()
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "input.json" or any(part in excluded_parts for part in Path(relative).parts):
            continue
        data = path.read_bytes()
        records.append({"path": relative, "bytes": len(data), "sha256": digest_bytes(data)})
    return records


def parse_structured_output(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run_one(*, bundle: dict[str, Any], fixture: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    input_path = run_dir / "input.json"
    input_path.write_text(json.dumps(fixture["payload"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    command: list[str] | None
    adapter_reason: str
    source_root = parity_harness.repository_root() / bundle["source"]

    stdout = ""
    stderr = ""
    exit_code: int | None = None
    execution_status = "unverified"
    with tempfile.TemporaryDirectory(prefix="parity-run-") as work:
        workdir = Path(work)
        if bundle["kind"] == "zip":
            execution_root = safe_extract_zip(source_root, workdir / "legacy-bundle")
        else:
            execution_root = source_root
        command, adapter_reason, environment = adapter_for(
            bundle["name"], fixture["class"], execution_root, input_path, workdir
        )
        # 実行環境はBundleごとに一時領域へ隔離し、リポジトリへ副作用を出さない。
        if command is not None:
            completed = subprocess.run(command, cwd=workdir, env={**os.environ, **environment}, text=True, capture_output=True, check=False)
            stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
            execution_status = "observed"
        side_effects = file_snapshot(workdir, excluded_parts={"legacy-bundle"})

    (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    (run_dir / "exit_code.json").write_text(json.dumps({"exit_code": exit_code}, indent=2) + "\n", encoding="utf-8")
    structured = parse_structured_output(stdout)
    (run_dir / "structured-output.json").write_text(
        json.dumps(structured, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "state-snapshot.json").write_text(
        json.dumps({"status": "unverified", "reason": "fixtureに状態Adapterを定義していない"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "side-effects-snapshot.json").write_text(
        json.dumps({"status": "observed", "files": side_effects}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = {
        "schema_version": "parity-run-result-1",
        "bundle": {key: bundle[key] for key in ("name", "version", "kind", "source_sha256")},
        "fixture": {key: fixture[key] for key in ("class", "path", "digest")},
        "input": "input.json",
        "command": command,
        "adapter": adapter_reason,
        "execution_status": execution_status,
        "exit_code": exit_code,
        "structured_output": "structured-output.json",
        "state_snapshot": "state-snapshot.json",
        "side_effects_snapshot": "side-effects-snapshot.json",
        "unverified": [
            "state snapshot: fixture-specific state adapter is not defined",
            "cross-version semantic equivalence: version-specific adapter is not defined" if command is None else "cross-version semantic equivalence: not inferred from one execution",
        ],
    }
    (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_run(*, stage: Path, output_root: Path, run_id: str, selected: tuple[str, ...]) -> dict[str, Any]:
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in run_id):
        raise ValueError("run_id must contain only ASCII letters, digits, '_' or '-'")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"output directory is not empty: {output_root}")
    fixtures = load_fixture_suite(stage)
    bundle_manifest = parity_harness.build_manifest()
    bundles = {item["name"]: item for item in bundle_manifest["bundles"]}
    if set(selected) - set(SUPPORTED_BUNDLES):
        raise ValueError("unknown bundle selected")
    missing = set(selected) - set(bundles)
    if missing:
        raise ValueError(f"bundle missing from manifest: {sorted(missing)}")
    output_root.mkdir(parents=True, exist_ok=True)
    run_entries: list[dict[str, Any]] = []
    for bundle_name in selected:
        bundle = bundles[bundle_name]
        for fixture_class in FIXTURE_CLASSES:
            run_dir = output_root / bundle_name / fixture_class
            run_dir.mkdir(parents=True, exist_ok=False)
            run_entries.append(run_one(bundle=bundle, fixture=fixtures[fixture_class], run_dir=run_dir))
    manifest = {
        "schema_version": "parity-run-manifest-1",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fixture_classes": list(FIXTURE_CLASSES),
        "bundle_names": list(selected),
        "bundle_manifest_digest": digest_json(bundle_manifest),
        "fixture_suite_digest": digest_json({key: value["digest"] for key, value in fixtures.items()}),
        "run_count": len(run_entries),
        "observed_count": sum(item["execution_status"] == "observed" for item in run_entries),
        "unverified_count": sum(item["execution_status"] == "unverified" for item in run_entries),
        "runs": run_entries,
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--bundle", action="append", choices=SUPPORTED_BUNDLES, dest="bundles")
    args = parser.parse_args(argv)
    try:
        selected = tuple(args.bundles or SUPPORTED_BUNDLES)
        manifest = build_run(stage=args.stage.resolve(), output_root=args.output_root.resolve(), run_id=args.run_id, selected=selected)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "run_id": manifest["run_id"], "run_count": manifest["run_count"], "unverified_count": manifest["unverified_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
