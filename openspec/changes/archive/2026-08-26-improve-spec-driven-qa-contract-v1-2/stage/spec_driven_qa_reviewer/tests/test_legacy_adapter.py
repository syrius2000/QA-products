import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

import pytest

from spec_driven_qa_reviewer.scripts.legacy_adapter import (
    UnsupportedContractVersion,
    read_legacy,
)


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_supported_legacy_versions_are_read_only(version):
    document = {
        "handoff_contract_version": version,
        "case_id": "QA-0001",
        "status": "author-action-required",
        "findings": [{"id": "QA-0001-F01", "status": "open"}],
    }
    original = deepcopy(document)
    view = read_legacy(document)
    assert view["source_contract_version"] == version
    assert view["read_only"] is True
    assert view["case_status"] == "author-action-required"
    assert document == original


def test_unknown_major_version_stops_without_guessing():
    with pytest.raises(UnsupportedContractVersion, match="blocked: unsupported-contract-version"):
        read_legacy({"contract_version": "2.0", "case_id": "QA-0001"})


def test_unsupported_minor_version_is_not_silently_converted():
    with pytest.raises(UnsupportedContractVersion):
        read_legacy({"contract_version": "1.3", "case_id": "QA-0001"})
