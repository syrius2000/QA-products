"""handoffの契約version、対象Finding、権限、revision、digestを突合する。"""

from __future__ import annotations

import re
from pathlib import Path

from .common import parse_findings_summary, parse_simple_frontmatter
from .render_handoff import comparable, render


def validate_handoff_contract(case: Path, handoff: Path | None = None) -> list[str]:
    handoff_path = handoff or (case / "handoff.md")
    if not handoff_path.exists():
        return ["handoff is missing"]
    actual_text = handoff_path.read_text(encoding="utf-8")
    actual = parse_simple_frontmatter(actual_text)
    expected_text = render(case)
    expected = parse_simple_frontmatter(expected_text)
    errors: list[str] = []
    if actual.get("contract_version") != "1.2":
        errors.append("unsupported or missing contract_version")
    for key in ("case_id", "case_revision", "source_revision", "semantic_digest", "content_digest"):
        if actual.get(key) != expected.get(key):
            errors.append(f"handoff field is stale or inconsistent: {key}")
    if actual.get("implementation_permission") not in {"none", "scoped"}:
        errors.append("handoff implementation_permission is invalid")
    if not actual.get("requested_evidence"):
        errors.append("handoff requested_evidence is missing")

    canonical_ids = {
        row.get("id")
        for row in parse_findings_summary(case / "findings.yaml")
        if row.get("id")
    } if (case / "findings.yaml").exists() else set()
    handed_off_ids = set(re.findall(r"\|\s*(QA-[0-9]{4,}-F[0-9]+)\s*\|", actual_text))
    unknown = sorted(handed_off_ids - canonical_ids)
    if unknown:
        errors.append(f"handoff contains unknown Finding: {unknown[0]}")
    if comparable(actual_text) != comparable(expected_text):
        errors.append("handoff content does not match Reviewer rendering")
    return errors
