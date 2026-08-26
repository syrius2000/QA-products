from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.detect_unresolved_markers import scan
from spec_driven_qa_reviewer.scripts.common import slugify
from spec_driven_qa_reviewer.scripts.render_handoff import comparable, render


def test_slugify():
    assert slugify("Patient Normalization") == "patient-normalization"


def test_detect_required(tmp_path: Path):
    p = tmp_path / "x.md"
    p.write_text("<!-- REQUIRED:AUTHOR-RESPONSE:QA-1 -->\n", encoding="utf-8")
    hits = scan(tmp_path)
    assert hits and hits[0][0] == p


def test_no_required(tmp_path: Path):
    p = tmp_path / "x.md"
    p.write_text("review complete\n", encoding="utf-8")
    assert scan(tmp_path) == []


def test_handoff_render_is_deterministic_except_timestamp(tmp_path: Path):
    case = tmp_path / "QA-0001-demo"
    case.mkdir()
    (case / "review.md").write_text(
        "---\nid: QA-0001\nstatus: author-action-required\nqa_profile: standard\ncurrent_cycle: 1\n"
        "subject:\n  targets:\n    - \"src/demo\"\n---\n",
        encoding="utf-8",
    )
    (case / "findings.yaml").write_text(
        "findings:\n  - id: QA-0001-F01\n    severity: high\n    status: open\n"
        "    requested_action: \"修正を提出\"\n    evidence:\n      - type: code\n        reference: src/demo.py\n",
        encoding="utf-8",
    )
    first = render(case)
    second = render(case)
    assert comparable(first) == comparable(second)
    assert "QA-0001-F01" in first
    assert "src/demo.py" in first
