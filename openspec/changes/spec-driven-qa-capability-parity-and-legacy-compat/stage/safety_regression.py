#!/usr/bin/env python3
"""Candidateとcompactの安全契約を標準ライブラリだけで回帰検証する。"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


def check(label: str, operation: Callable[[], bool]) -> dict[str, Any]:
    try:
        passed = bool(operation())
    except Exception:
        passed = False
    return {"id": label, "status": "passed" if passed else "failed"}


def compact_checks(bundle_root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(bundle_root))
    from shared_core.chain import ChainError, chain_review, chain_submit, run_chain

    checks: list[dict[str, Any]] = []

    def reviewed(case_id: str) -> tuple[str, str, str, list[str]]:
        workspace = str(Path(tempfile.mkdtemp()) / "workspace")
        result = chain_review({"case_id": case_id, "workspace": workspace})
        return workspace, result["semantic_digest"], result["content_digest"], result["finding_ids"]

    checks.append(check("compact-author-self-close-denied", lambda: _raises(
        ChainError, lambda: run_chain("author", "chain-verify", {"case_id": "QA-9101", "workspace": str(Path(tempfile.mkdtemp()) / "workspace")})
    )))

    workspace, semantic, content, finding_ids = reviewed("QA-9102")
    base = {
        "case_id": "QA-9102", "workspace": workspace, "submission_id": "submission-safety",
        "base_revision": 1, "expected_semantic_digest": semantic, "expected_content_digest": content,
        "target_findings": finding_ids, "responses": {finding_ids[0]: {"disposition": "accepted"}},
    }
    checks.append(check("compact-reviewer-owned-write-denied", lambda: _raises(
        ChainError, lambda: chain_submit({**base, "case_status": "closed"})
    )))
    checks.append(check("compact-unknown-finding-denied", lambda: _raises(
        ChainError, lambda: chain_submit({**base, "target_findings": ["QA-9102-F99"], "responses": {"QA-9102-F99": {"disposition": "accepted"}}})
    )))
    checks.append(check("compact-stale-semantic-digest-denied", lambda: _raises(
        ChainError, lambda: chain_submit({**base, "expected_semantic_digest": "0" * 64})
    )))
    checks.append(check("compact-stale-content-digest-denied", lambda: _raises(
        ChainError, lambda: chain_submit({**base, "expected_content_digest": "0" * 64})
    )))
    checks.append(check("compact-unknown-digest-version-denied", lambda: _raises(
        ChainError, lambda: chain_review({"case_id": "QA-9103", "workspace": str(Path(tempfile.mkdtemp()) / "workspace"), "digest_version": "v9"})
    )))
    checks.append(check("compact-workspace-boundary-denied", lambda: _raises(
        ChainError, lambda: chain_review({"case_id": "QA-9104", "workspace": str(Path(tempfile.mkdtemp()) / "workspace"), "target_path": "/tmp/outside"})
    )))
    checks.append(check("compact-secret-input-denied", lambda: _raises(
        ChainError, lambda: chain_review({"case_id": "QA-9105", "workspace": str(Path(tempfile.mkdtemp()) / "workspace"), "token": "synthetic"})
    )))
    return checks


def candidate_checks(bundle_root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(bundle_root))
    from spec_driven_qa_author_response.scripts.execution_policy import can_execute, eligible_fast_path
    from spec_driven_qa_author_response.scripts.submission_store import validate_no_reviewer_mutation
    from spec_driven_qa_reviewer.scripts.digest import semantic_digest
    from spec_driven_qa_reviewer.scripts.evidence import validate_evidence_bundle
    from spec_driven_qa_reviewer.scripts.link_validator import validate_reference
    from spec_driven_qa_reviewer.scripts.submission_validator import accept_author_submission

    change = {"severity": "low", "local": True, "reversible": True, "destructive": False, "external_operation": False, "preapproved": True, "documentation_only": True, "scoped": True}
    case = {"contract_version": "1.2", "case_id": "QA-9106", "case_status": "author-action-required", "next_action": "author-response", "case_revision": 2, "findings": [{"id": "QA-9106-F01", "severity": "medium", "finding_status": "awaiting-author"}], "terminal_result": None}
    valid = {"submission_id": "submission-safety", "base_revision": 2, "expected_semantic_digest": semantic_digest(case), "target_findings": ["QA-9106-F01"], "author_response": "synthetic"}
    stale = {**valid, "base_revision": 1}
    checks = [
        check("candidate-fast-path-boundary", lambda: eligible_fast_path(change) and not eligible_fast_path({**change, "external_operation": True})),
        check("candidate-author-reviewer-field-denied", lambda: bool(validate_no_reviewer_mutation({"case_status": "closed"}))),
        check("candidate-stale-revision-denied", lambda: not accept_author_submission(case, stale)["accepted"]),
        check("candidate-unknown-finding-denied", lambda: not accept_author_submission(case, {**valid, "target_findings": ["QA-9106-F99"]})["accepted"]),
        check("candidate-secret-evidence-denied", lambda: bool(validate_evidence_bundle({"evidence": [{"id": "EV-1", "reference": "token=synthetic", "reference_type": "repository-relative", "verifier": "author", "acquired_at": "2026-08-27", "result": "verified", "secret_status": "none"}]}))),
        check("candidate-workspace-absolute-repository-path-denied", lambda: bool(validate_reference("/tmp/outside", "repository-relative"))),
    ]
    return checks


def _raises(error_type: type[Exception], operation: Callable[[], Any]) -> bool:
    try:
        operation()
    except error_type:
        return True
    return False


def build_report(stage: Path) -> dict[str, Any]:
    candidate_root = stage.parent.parent.parent / "changes/archive/2026-08-26-improve-spec-driven-qa-contract-v1-2/stage"
    compact_root = stage / "spec-driven-qa-bundle"
    candidate = candidate_checks(candidate_root)
    compact = compact_checks(compact_root)
    all_checks = {item["id"]: item["status"] for item in candidate + compact}
    regression = json.loads((stage / "fixtures" / "contract-regression.json").read_text(encoding="utf-8"))
    if regression.get("schema_version") != "contract-regression-fixture-1":
        raise ValueError("unsupported contract regression fixture")
    regression_cases = []
    for case in regression.get("cases", []):
        source = stage.parents[3] / case["source"]
        expected = case.get("expected_checks", [])
        statuses = {check_id: all_checks.get(check_id, "missing") for check_id in expected}
        regression_cases.append({"id": case["id"], "source": case["source"], "checks": statuses, "status": "observed" if source.is_file() and all(value == "passed" for value in statuses.values()) else "evidence-gap"})
    regression_status = "observed" if regression_cases and all(case["status"] == "observed" for case in regression_cases) else "evidence-gap"
    return {
        "schema_version": "safety-regression-1",
        "status": "observed" if all(item["status"] == "passed" for item in candidate + compact) else "failed",
        "bundles": {"candidate": {"status": "observed", "checks": candidate}, "compact": {"status": "observed", "checks": compact}},
        "contract_regression": {"status": regression_status, "cases": regression_cases},
        "secret_policy": "secret values are not included in report",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.stage.resolve())
    except (OSError, ImportError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"]}, ensure_ascii=False))
    return 0 if report["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
