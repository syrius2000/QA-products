#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

VALID_DISPOSITIONS = {
    "accepted", "rejected-with-evidence", "fix-submitted", "deferred",
    "risk-accepted", "not-applicable",
}
FORBIDDEN_DISPOSITIONS = {"fixed-and-verified", "closed"}
HANDOFF_FINDING_PATTERN = re.compile(r"\|\s*(QA-[0-9]{4,}-F[0-9]+)\s*\|")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def case_id(case: Path) -> str:
    meta = frontmatter((case / "review.md").read_text(encoding="utf-8"))
    return meta.get("id", "")


def finding_ids(case: Path) -> set[str]:
    path = case / "findings.yaml"
    return set(re.findall(r"^\s*- id:\s*(QA-[0-9]+-F[0-9]+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE))


def open_finding_ids(case: Path) -> set[str]:
    text = (case / "findings.yaml").read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^\s*- id:\s*", text)[1:]
    ids: set[str] = set()
    for block in blocks:
        ident = block.splitlines()[0].strip().strip('"').strip("'")
        status = re.search(r"(?m)^\s{4}status:\s*([^\s#]+)", block)
        if status and status.group(1) not in {"fixed-and-verified", "closed", "not-applicable", "risk-accepted"}:
            ids.add(ident)
    return ids


def validate(case: Path, response: Path) -> list[str]:
    errors: list[str] = []
    if not (case / "review.md").exists() or not (case / "findings.yaml").exists():
        return [f"QA case is missing review.md or findings.yaml: {case}"]
    meta = frontmatter((case / "review.md").read_text(encoding="utf-8"))
    text = response.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm.get("case_id") != meta.get("id"):
        errors.append("response case_id does not match review.md")
    if fm.get("action") != "author-response":
        errors.append("response action must be author-response")
    role = fm.get("role", "")
    if not role:
        nested_role = re.search(r"(?m)^\s+role:\s*([^\s#]+)", text)
        role = nested_role.group(1).strip('"').strip("'") if nested_role else ""
    if role not in {"", "implementer"}:
        errors.append("response role must be implementer")
    if fm.get("cycle", "") != "" and not fm.get("cycle", "").isdigit():
        errors.append("response cycle must be an integer")
    if not fm.get("base_revision") or "REQUIRED:" in fm.get("base_revision", ""):
        errors.append("base_revision is required")
    if meta.get("status") in {"closed", "ready-for-closure"}:
        errors.append("author response cannot be submitted to a closed/ready-for-closure case")
    found = set(re.findall(r"(?m)^###\s+(QA-[0-9]+-F[0-9]+)\s*$", text))
    if not found:
        errors.append("no Finding response headings found")
    known = finding_ids(case)
    unknown = sorted(found - known)
    if unknown:
        errors.append(f"response contains unknown Finding IDs: {', '.join(unknown)}")
    missing = sorted(open_finding_ids(case) - found)
    if missing:
        errors.append(f"response is missing open Finding IDs: {', '.join(missing)}")
    dispositions = re.findall(r"(?mi)^\s*Disposition:\s*([a-z0-9-]+)\s*$", text)
    if len(dispositions) != len(found):
        errors.append("every Finding must have exactly one Disposition")
    for value in dispositions:
        if value in FORBIDDEN_DISPOSITIONS:
            errors.append(f"author response cannot self-close a Finding: {value}")
        elif value not in VALID_DISPOSITIONS:
            errors.append(f"invalid Disposition: {value}")
    if "fix-submitted" in dispositions:
        if not fm.get("result_revision") or fm.get("result_revision") in {"null", "REQUIRED:SYSTEM-REVISION"}:
            errors.append("fix-submitted requires result_revision")
    if response.name.startswith("0") and not response.name.startswith("cycle-"):
        errors.append("new response filename must use cycle-NN-author-response.md; legacy filename is history-only")
    if re.search(r"(?mi)^\s*(result|status):\s*(closed|fixed-and-verified)\s*$", text):
        errors.append("response text must not set closed/fixed-and-verified status")
    return errors


def validate_handoff_submission(handoff_text: str, submission: dict) -> list[str]:
    """公開handoffとAuthor提出物の境界を検証する。"""
    errors: list[str] = []
    meta = frontmatter(handoff_text)
    allowed_findings = set(HANDOFF_FINDING_PATTERN.findall(handoff_text))
    target_findings = submission.get("target_findings", [])
    if not isinstance(target_findings, list):
        return ["target_findings must be a list"]
    unknown = sorted(set(target_findings) - allowed_findings)
    if unknown:
        errors.append(f"unknown Finding: {unknown[0]}")
    if not submission.get("base_revision"):
        errors.append("base_revision is required")
    if not submission.get("expected_semantic_digest"):
        errors.append("expected_semantic_digest is required")
    implementation = submission.get("implementation")
    if implementation and meta.get("implementation_permission") != "scoped":
        errors.append("implementation is not permitted by handoff")
    responses = submission.get("responses", {})
    if not isinstance(responses, dict):
        errors.append("responses must be an object")
    else:
        unanswered = sorted(set(target_findings) - set(responses))
        if unanswered:
            errors.append(f"unanswered Finding: {unanswered[0]}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a Spec-Driven QA author response")
    ap.add_argument("case_dir")
    ap.add_argument("response")
    args = ap.parse_args()
    errors = validate(Path(args.case_dir), Path(args.response))
    if errors:
        print("Author response validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Author response is structurally valid and remains open for reviewer verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
