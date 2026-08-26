import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.render_handoff import render
from spec_driven_qa_reviewer.scripts.validate_handoff_contract import validate_handoff_contract


def make_case(tmp_path: Path) -> Path:
    case = tmp_path / "QA-0001-demo"
    case.mkdir()
    (case / "review.md").write_text(
        "---\nid: QA-0001\nstatus: author-action-required\nqa_profile: standard\n"
        "current_cycle: 1\ncase_revision: 3\nimplementation_revision: abc123\n---\n",
        encoding="utf-8",
    )
    (case / "findings.yaml").write_text(
        "findings:\n  - id: QA-0001-F01\n    severity: high\n    status: open\n"
        "    evidence:\n      - type: code\n        reference: src/demo.py\n",
        encoding="utf-8",
    )
    (case / "handoff.md").write_text(render(case), encoding="utf-8")
    return case


def test_current_handoff_contract_is_accepted(tmp_path: Path):
    assert validate_handoff_contract(make_case(tmp_path)) == []


def test_stale_revision_is_rejected(tmp_path: Path):
    case = make_case(tmp_path)
    review = case / "review.md"
    review.write_text(review.read_text(encoding="utf-8").replace("case_revision: 3", "case_revision: 4"), encoding="utf-8")
    errors = validate_handoff_contract(case)
    assert any("case_revision" in error for error in errors)


def test_unknown_finding_is_rejected(tmp_path: Path):
    case = make_case(tmp_path)
    handoff = case / "handoff.md"
    handoff.write_text(handoff.read_text(encoding="utf-8").replace(
        "| QA-0001-F01 |", "| QA-0001-F99 |"
    ), encoding="utf-8")
    errors = validate_handoff_contract(case)
    assert any("unknown Finding" in error for error in errors)
