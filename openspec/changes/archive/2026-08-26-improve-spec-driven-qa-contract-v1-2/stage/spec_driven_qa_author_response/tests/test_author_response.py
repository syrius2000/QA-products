from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_author_response.scripts.validate_author_response import validate


def make_case(tmp_path: Path) -> Path:
    case = tmp_path / "QA-0001-demo"
    case.mkdir()
    (case / "review.md").write_text(
        "---\nid: QA-0001\nstatus: author-action-required\n---\n", encoding="utf-8"
    )
    (case / "findings.yaml").write_text(
        "findings:\n  - id: QA-0001-F01\n    status: open\n  - id: QA-0001-F02\n    status: open\n", encoding="utf-8"
    )
    return case


def response(case: Path, dispositions: tuple[str, str] = ("accepted", "deferred"), name: str = "cycle-01-author-response.md") -> Path:
    path = case / name
    path.write_text(
        "---\ncase_id: QA-0001\ncycle: 1\naction: author-response\nbase_revision: abc123\nresult_revision: def456\n---\n\n"
        f"### QA-0001-F01\n\nDisposition: {dispositions[0]}\nRationale: reason\nEvidence: evidence\n\n"
        f"### QA-0001-F02\n\nDisposition: {dispositions[1]}\nRationale: reason\nEvidence: evidence\n",
        encoding="utf-8",
    )
    return path


def test_all_dispositions_are_allowed(tmp_path: Path):
    case = make_case(tmp_path)
    for value in ["accepted", "rejected-with-evidence", "fix-submitted", "deferred", "risk-accepted", "not-applicable"]:
        errors = validate(case, response(case, (value, "accepted")))
        assert not any("invalid Disposition" in error for error in errors)


def test_unknown_finding_is_rejected(tmp_path: Path):
    case = make_case(tmp_path)
    path = response(case)
    path.write_text(path.read_text(encoding="utf-8").replace("QA-0001-F02", "QA-0001-F99"), encoding="utf-8")
    assert any("unknown Finding" in error for error in validate(case, path))


def test_self_close_is_rejected(tmp_path: Path):
    case = make_case(tmp_path)
    path = response(case, ("fixed-and-verified", "accepted"))
    errors = validate(case, path)
    assert any("self-close" in error for error in errors)


def test_fix_requires_result_revision(tmp_path: Path):
    case = make_case(tmp_path)
    path = response(case, ("fix-submitted", "accepted"))
    text = path.read_text(encoding="utf-8").replace("result_revision: def456", "result_revision: null")
    path.write_text(text, encoding="utf-8")
    assert any("result_revision" in error for error in validate(case, path))


def test_legacy_cycle_name_is_not_new_contract(tmp_path: Path):
    case = make_case(tmp_path)
    path = response(case, name="01-author-response.md")
    assert any("cycle-NN" in error for error in validate(case, path))
