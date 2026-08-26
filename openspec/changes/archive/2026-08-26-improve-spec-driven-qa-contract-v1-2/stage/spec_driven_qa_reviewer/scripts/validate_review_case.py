#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from spec_driven_qa_reviewer.scripts.common import parse_simple_frontmatter
from spec_driven_qa_reviewer.scripts.render_handoff import comparable, render
from spec_driven_qa_reviewer.scripts.cli_json import emit

REQUIRED_FILES_STANDARD = {"review.md", "findings.yaml", "traceability.yaml", "events.jsonl"}
VALID_CASE_STATUS = {
    "draft", "review-in-progress", "author-action-required", "author-response-submitted",
    "verification-in-progress", "adjudication-required", "ready-for-closure", "closed",
    "blocked", "needs-review", "deferred", "risk-accepted", "superseded", "cancelled",
}
VALID_RESULTS = {
    "null", "accepted", "accepted-with-residual-risk", "conditionally-accepted", "rejected",
    "blocked-insufficient-evidence", "adjudication-required", "",
}


def unresolved_required(text: str) -> bool:
    return bool(re.search(r"REQUIRED:[A-Z0-9_-]+", text, re.IGNORECASE) or "{{HUMAN_INPUT" in text)


def parse_jsonl(path: Path) -> list[dict]:
    rows=[]
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{i}: invalid JSONL: {e}") from e
    return rows


def validate_case(case: Path) -> list[str]:
    errors: list[str] = []
    review = case / "review.md"
    if not review.exists():
        return [f"{case}: missing review.md"]
    text = review.read_text(encoding="utf-8")
    meta = parse_simple_frontmatter(text)
    status = meta.get("status", "")
    result = meta.get("result", "")
    profile = meta.get("qa_profile", "standard")

    if status not in VALID_CASE_STATUS:
        errors.append(f"{case}: invalid/missing status: {status!r}")
    if result not in VALID_RESULTS:
        errors.append(f"{case}: invalid result: {result!r}")
    if profile not in {"lite", "standard", "strict"}:
        errors.append(f"{case}: invalid qa_profile: {profile!r}")

    if profile in {"standard", "strict"}:
        missing = sorted(f for f in REQUIRED_FILES_STANDARD if not (case / f).exists())
        if missing:
            errors.append(f"{case}: missing required files: {', '.join(missing)}")

    handoff_required = meta.get("handoff_contract_version") == "1.0"
    handoff = case / "handoff.md"
    if handoff_required and not handoff.exists():
        errors.append(f"{case}: handoff contract requires handoff.md")
    if handoff.exists():
        handoff_meta = parse_simple_frontmatter(handoff.read_text(encoding="utf-8"))
        if handoff_meta.get("document_type") != "spec-driven-qa-handoff":
            errors.append(f"{case}: handoff.md has invalid document_type")
        if handoff_meta.get("handoff_contract_version") != "1.0":
            errors.append(f"{case}: handoff.md has unsupported contract version")
        if handoff_meta.get("case_id") != meta.get("id"):
            errors.append(f"{case}: handoff.md case_id does not match review.md")
        try:
            expected = render(case, recipient_role=handoff_meta.get("recipient_role", "implementer"), workflow=handoff_meta.get("workflow", "author-response"))
            if comparable(handoff.read_text(encoding="utf-8")) != comparable(expected):
                errors.append(f"{case}: handoff.md is stale; rerun render_handoff.py")
        except (OSError, ValueError) as e:
            errors.append(f"{case}: cannot render handoff.md: {e}")

    if (case / "events.jsonl").exists():
        try:
            rows = parse_jsonl(case / "events.jsonl")
            for idx, row in enumerate(rows, 1):
                for key in ("timestamp", "actor", "role", "action"):
                    if key not in row:
                        errors.append(f"{case}/events.jsonl row {idx}: missing {key}")
        except ValueError as e:
            errors.append(str(e))

    if status == "closed":
        for p in case.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".jsonl"}:
                try:
                    if unresolved_required(p.read_text(encoding="utf-8")):
                        errors.append(f"{case}: closed case contains unresolved REQUIRED marker in {p.relative_to(case)}")
                except UnicodeDecodeError:
                    pass
        if not result or result == "null":
            errors.append(f"{case}: closed case requires terminal result")

    # Minimal separation check from review front matter nested fields by text pattern.
    imp = re.search(r"implementer:\s*\n(?:.*\n){0,3}?\s*agent_id:\s*[\"']?([^\n\"']+)", text)
    rev = re.search(r"reviewer:\s*\n(?:.*\n){0,3}?\s*agent_id:\s*[\"']?([^\n\"']+)", text)
    if imp and rev and imp.group(1).strip() == rev.group(1).strip():
        errors.append(f"{case}: implementer and reviewer agent_id are identical")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Spec-Driven QA Review Case structure")
    ap.add_argument("path", nargs="?", default="docs/ADR/QA")
    ap.add_argument("--all", action="store_true", help="Validate all QA-* directories under path")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    path=Path(args.path)
    cases = []
    if args.all or (path.is_dir() and not (path / "review.md").exists()):
        cases = sorted(p for p in path.glob("QA-*") if p.is_dir()) if path.exists() else []
    else:
        cases=[path]
    if not cases:
        if args.as_json:
            emit(ok=True, status="not-found", path=path, next_action="create-case", errors=[])
            return 0
        print("No QA review cases found.")
        return 0
    errors=[]
    for case in cases:
        errors.extend(validate_case(case))
    if errors:
        if args.as_json:
            emit(ok=False, status="blocked", path=path, next_action="resolve-validation-errors", errors=errors)
            return 1
        print("QA validation errors:")
        for e in errors:
            print(f"- {e}")
        return 1
    if args.as_json:
        emit(ok=True, status="validated", path=path, next_action="continue", errors=[])
    else:
        print(f"Validated {len(cases)} QA review case(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
