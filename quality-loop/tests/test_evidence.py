from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from quality_loop.evidence import validate_evidence
from quality_loop.errors import QualityLoopError


class EvidenceTest(unittest.TestCase):
    def test_valid_evidence_with_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir)
            evidence_file = case_dir / "evidence" / "test_run.txt"
            evidence_file.parent.mkdir(parents=True, exist_ok=True)
            evidence_file.write_text("All 10 tests passed successfully.\n", encoding="utf-8")
            digest = hashlib.sha256(evidence_file.read_bytes()).hexdigest()

            evidence_items = [
                {
                    "evidence_id": "EV-001",
                    "level": "observed",
                    "target_revision": "rev-1",
                    "method": "pytest run",
                    "result": "passed",
                    "path": "evidence/test_run.txt",
                    "sha256": digest,
                }
            ]

            validated = validate_evidence(case_dir, evidence_items, set())
            self.assertEqual(1, len(validated))
            self.assertEqual("EV-001", validated[0]["evidence_id"])
            self.assertEqual(digest, validated[0]["sha256"])

    def test_missing_evidence_file_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir)
            evidence_items = [
                {
                    "evidence_id": "EV-001",
                    "level": "observed",
                    "target_revision": "rev-1",
                    "method": "pytest run",
                    "result": "passed",
                    "path": "evidence/non_existent.txt",
                    "sha256": "fakehash",
                }
            ]

            with self.assertRaises(QualityLoopError) as ctx:
                validate_evidence(case_dir, evidence_items, set())
            self.assertEqual("evidence-not-found", ctx.exception.error_code)

    def test_tampered_evidence_file_raises_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir)
            evidence_file = case_dir / "evidence" / "test_run.txt"
            evidence_file.parent.mkdir(parents=True, exist_ok=True)
            evidence_file.write_text("Modified content.\n", encoding="utf-8")

            evidence_items = [
                {
                    "evidence_id": "EV-001",
                    "level": "observed",
                    "target_revision": "rev-1",
                    "method": "pytest run",
                    "result": "passed",
                    "path": "evidence/test_run.txt",
                    "sha256": "incorrect_hash_value",
                }
            ]

            with self.assertRaises(QualityLoopError) as ctx:
                validate_evidence(case_dir, evidence_items, set())
            self.assertEqual("evidence-digest-mismatch", ctx.exception.error_code)

    def test_invalid_level_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir)
            evidence_items = [
                {
                    "evidence_id": "EV-001",
                    "level": "guessed_and_probably_fine",
                    "target_revision": "rev-1",
                    "method": "gut feeling",
                    "result": "passed",
                }
            ]

            with self.assertRaises(QualityLoopError) as ctx:
                validate_evidence(case_dir, evidence_items, set())
            self.assertEqual("invalid-evidence", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
