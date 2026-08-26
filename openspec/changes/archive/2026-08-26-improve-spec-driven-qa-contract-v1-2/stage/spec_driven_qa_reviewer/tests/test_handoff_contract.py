import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.render_handoff import render
from spec_driven_qa_reviewer.scripts.validate_handoff_origin import validate_handoff_origin


def make_case(tmp_path: Path) -> Path:
    case = tmp_path / "QA-0001-demo"
    case.mkdir()
    (case / "review.md").write_text(
        "---\nid: QA-0001\nstatus: author-action-required\nqa_profile: standard\n"
        "current_cycle: 1\ncase_revision: 3\nimplementation_revision: abc123\n"
        "subject:\n  targets:\n    - \"src/demo\"\n---\n",
        encoding="utf-8",
    )
    (case / "findings.yaml").write_text(
        "findings:\n  - id: QA-0001-F01\n    severity: high\n    status: open\n"
        "    requested_action: \"修正を提出\"\n    evidence:\n"
        "      - type: code\n        reference: src/demo.py\n",
        encoding="utf-8",
    )
    return case


def test_handoff_contains_contract_v1_2_fields(tmp_path: Path):
    case = make_case(tmp_path)
    handoff = case / "handoff.md"
    handoff.write_text(render(case), encoding="utf-8")
    text = handoff.read_text(encoding="utf-8")
    assert 'contract_version: "1.2"' in text
    assert "semantic_digest:" in text
    assert "content_digest:" in text
    assert validate_handoff_origin(case) == []


def test_direct_handoff_edit_is_rejected(tmp_path: Path):
    case = make_case(tmp_path)
    handoff = case / "handoff.md"
    handoff.write_text(render(case), encoding="utf-8")
    handoff.write_text(handoff.read_text(encoding="utf-8").replace("author-response", "adjudication"), encoding="utf-8")
    errors = validate_handoff_origin(case)
    assert errors == ["handoff must be generated from the Reviewer canonical case"]
