import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

import pytest

from spec_driven_qa_author_response.scripts.submission_store import (
    validate_no_reviewer_mutation,
    validate_submission_shape,
    write_submission,
)


def submission():
    return {"submission_id": "submission-001", "base_revision": 2, "responses": {"QA-0001-F01": {}}}


def test_submission_is_written_once(tmp_path: Path):
    path = write_submission(tmp_path, "QA-0001", submission())
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["submission_id"] == "submission-001"
    with pytest.raises(FileExistsError):
        write_submission(tmp_path, "QA-0001", submission())


def test_reviewer_owned_field_is_not_writable():
    document = submission()
    document["severity"] = "high"
    assert any("not writable" in error for error in validate_submission_shape(document))


def test_invalid_submission_id_is_rejected():
    document = submission()
    document["submission_id"] = "cycle-1"
    assert any("invalid submission_id" in error for error in validate_submission_shape(document))


@pytest.mark.parametrize("field", ["severity", "verification", "events", "closure"])
def test_reviewer_owned_fields_are_rejected(field):
    document = submission()
    document["responses"]["QA-0001-F01"][field] = "changed"
    assert validate_no_reviewer_mutation(document)
