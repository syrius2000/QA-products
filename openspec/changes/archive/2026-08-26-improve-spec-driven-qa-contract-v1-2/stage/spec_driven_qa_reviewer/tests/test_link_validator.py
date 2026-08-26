import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.link_validator import validate_reference


def test_repository_reference_is_relative():
    assert validate_reference("docs/QA/review.md:10", "repository-relative") == []


def test_absolute_and_file_references_are_rejected_for_repository():
    assert validate_reference("/Users/example/review.md", "repository-relative")
    assert validate_reference("file:///Users/example/review.md", "repository-relative")


def test_external_reference_type_is_explicit():
    assert validate_reference("https://example.test/evidence", "external-url") == []
    assert validate_reference("/var/log/service.log", "external-absolute") == []
    assert validate_reference("https://example.test/evidence", "repository-relative")
