#!/usr/bin/env python3
"""ReviewerからAuthorへの連鎖を版別に実行し、欠落をEvidence Gapとして記録する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import parity_harness
from runner import FIXTURE_CLASSES, safe_extract_zip


def run_command(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, env={**os.environ, **(environment or {})}, text=True, capture_output=True, check=False)
    return {"command": command, "stdout": completed.stdout, "stderr": completed.stderr, "exit_code": completed.returncode}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    try:
        _, block, _ = text.split("---\n", 2)
    except ValueError:
        return {}
    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def author_response(case_id: str) -> str:
    return f'''---
case_id: {case_id}
action: author-response
role: implementer
cycle: 1
base_revision: 0
---

### {case_id}-F01

Disposition: accepted

対応を受け入れ、Reviewerによる独立検証を依頼します。
'''


def compact_flow(bundle_root: Path, input_path: Path, output: Path) -> dict[str, Any]:
    reviewer = bundle_root / "spec-driven-qa-review" / "launcher.py"
    author = bundle_root / "spec-driven-qa-author-response" / "launcher.py"
    workspace = output / "workspace"
    workspace.mkdir()
    review_payload = json.dumps({"request_id": "cross-skill-parity", "case_id": "QA-0001", "workspace": str(workspace), "fixture_path": input_path.name}, ensure_ascii=False)
    review = run_command([sys.executable, "-B", str(reviewer), "chain-review", "--json", review_payload], output)
    review_result = json.loads(review["stdout"]) if review["exit_code"] == 0 else {}
    submit_payload = json.dumps({
        "request_id": "cross-skill-parity-submit", "case_id": "QA-0001", "workspace": str(workspace),
        "submission_id": "submission-cross-skill", "base_revision": review_result.get("case_revision"),
        "expected_semantic_digest": review_result.get("semantic_digest"),
        "expected_content_digest": review_result.get("content_digest"),
        "target_findings": review_result.get("finding_ids", []),
        "responses": {finding_id: {"disposition": "accepted"} for finding_id in review_result.get("finding_ids", [])},
    }, ensure_ascii=False)
    response = run_command([sys.executable, "-B", str(author), "chain-submit", "--json", submit_payload], output)
    response_result = json.loads(response["stdout"]) if response["exit_code"] == 0 else {}
    verify_payload = json.dumps({"request_id": "cross-skill-parity-verify", "case_id": "QA-0001", "workspace": str(workspace), "submission_id": response_result.get("submission_id", "submission-cross-skill")}, ensure_ascii=False)
    verification = run_command([sys.executable, "-B", str(reviewer), "chain-verify", "--json", verify_payload], output)
    (output / "reviewer.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "author.json").write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "bundle": "compact",
        "reviewer": {"exit_code": review["exit_code"], "verification_exit_code": verification["exit_code"], "status": "observed"},
        "author": {"exit_code": response["exit_code"], "status": "observed"},
        "handoff": {"status": "observed", "path": "workspace/qa-cases/QA-0001/handoff.md"},
        "submission": {"status": "observed", "path": "workspace/qa-cases/QA-0001/submissions/submission-cross-skill.json"},
        "digest": {"status": "observed", "semantic_digest": review_result.get("semantic_digest"), "content_digest": review_result.get("content_digest")},
        "revision": {"status": "observed", "value": review_result.get("case_revision")},
    }


def legacy_or_candidate_flow(bundle: dict[str, Any], input_path: Path, output: Path) -> dict[str, Any]:
    source = parity_harness.repository_root() / bundle["source"]
    with tempfile.TemporaryDirectory(prefix="cross-skill-") as temporary:
        workdir = Path(temporary)
        if bundle["kind"] == "zip":
            root = safe_extract_zip(source, workdir / "bundle")
            reviewer_root = root / "spec-driven-qa-review"
            author_root = root / "spec-driven-qa-author-response"
            environment = {}
        else:
            root = source
            reviewer_root = root / "spec_driven_qa_reviewer"
            author_root = root / "spec_driven_qa_author_response"
            environment = {"PYTHONPATH": str(root)}
        create = run_command([
            sys.executable, "-B", str(reviewer_root / "scripts/create_review_case.py"),
            "--root", str(workdir), "--title", "parity-cross-skill", "--target", "fixture-input", "--profile", "lite",
        ], workdir, environment)
        case_dir = workdir / "docs" / "ADR" / "QA" / "QA-0001-parity-cross-skill"
        handoff_path = case_dir / "handoff.md"
        render = run_command([sys.executable, "-B", str(reviewer_root / "scripts/render_handoff.py"), str(case_dir)], workdir, environment)
        handoff_text = handoff_path.read_text(encoding="utf-8") if handoff_path.is_file() else ""
        response_path = case_dir / "cycles" / "cycle-01-author-response.md"
        response_path.write_text(author_response("QA-0001"), encoding="utf-8")
        response = run_command([sys.executable, "-B", str(author_root / "scripts/validate_author_response.py"), str(case_dir), str(response_path)], workdir, environment)
        result: dict[str, Any] = {
            "bundle": bundle["name"],
            "reviewer": {"create_exit_code": create["exit_code"], "render_exit_code": render["exit_code"], "status": "observed"},
            "author": {"validation_exit_code": response["exit_code"], "status": "observed"},
            "handoff": {"status": "observed" if handoff_path.is_file() else "evidence-gap", "path": "handoff.md"},
        }
        (output / "create.json").write_text(json.dumps(create, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "render.json").write_text(json.dumps(render, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output / "author-validation.json").write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if handoff_path.is_file():
            (output / "handoff.md").write_text(handoff_text, encoding="utf-8")
        (output / "author-response.md").write_text(response_path.read_text(encoding="utf-8"), encoding="utf-8")
        metadata = frontmatter(handoff_text)
        digest_ok = all(re.fullmatch(r"[0-9a-f]{64}", metadata.get(key, "")) for key in ("semantic_digest", "content_digest"))
        revision_ok = bool(metadata.get("case_revision", "").isdigit())
        result["digest"] = {"status": "observed" if digest_ok else "evidence-gap", "semantic_digest_present": digest_ok}
        result["revision"] = {"status": "observed" if revision_ok else "evidence-gap", "value": metadata.get("case_revision")}
        if bundle["name"] == "candidate" and handoff_path.is_file() and digest_ok:
            submission = {
                "base_revision": metadata["case_revision"],
                "expected_semantic_digest": metadata["semantic_digest"],
                "target_findings": ["QA-0001-F01"],
                "responses": {"QA-0001-F01": {"disposition": "accepted"}},
            }
            submission_path = output / "submission.json"
            submission_path.write_text(json.dumps(submission, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            code = "from pathlib import Path; import json,sys; from spec_driven_qa_author_response.scripts.validate_author_response import validate_handoff_submission; errors=validate_handoff_submission(Path(sys.argv[1]).read_text(), json.loads(Path(sys.argv[2]).read_text())); print(json.dumps(errors, ensure_ascii=False)); raise SystemExit(0 if not errors else 1)"
            submission_check = run_command([sys.executable, "-B", "-c", code, str(output / "handoff.md"), str(submission_path)], workdir, environment)
            (output / "submission-validation.json").write_text(json.dumps(submission_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result["submission"] = {"status": "observed" if submission_check["exit_code"] == 0 else "failed", "exit_code": submission_check["exit_code"]}
        else:
            result["submission"] = {"status": "evidence-gap", "reason": "対象版にhandoff submission validatorまたはdigestがない"}
        return result


def run_flow(stage: Path, output_root: Path, run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id must contain only ASCII letters, digits, '_' or '-'")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"output directory is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads((stage / "fixtures" / "cross-skill.json").read_text(encoding="utf-8"))
    (output_root / "input.json").write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = parity_harness.build_manifest()
    results = []
    for bundle in manifest["bundles"]:
        bundle_output = output_root / bundle["name"]
        bundle_output.mkdir()
        if bundle["name"] == "compact":
            result = compact_flow(parity_harness.repository_root() / bundle["source"], output_root / "input.json", bundle_output)
        else:
            result = legacy_or_candidate_flow(bundle, output_root / "input.json", bundle_output)
        result["bundle_identity"] = {key: bundle[key] for key in ("name", "version", "source_sha256")}
        (bundle_output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(result)
    report = {
        "schema_version": "cross-skill-result-1",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fixture": {"class": "cross-skill", "digest": runner_digest(fixtures), "path": "fixtures/cross-skill.json"},
        "results": results,
        "status": "evidence-gap" if any(item.get("submission", {}).get("status") != "observed" for item in results) else "observed",
    }
    (output_root / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def runner_digest(value: Any) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        report = run_flow(args.stage.resolve(), args.output_root.resolve(), args.run_id)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "run_id": report["run_id"], "status": report["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
