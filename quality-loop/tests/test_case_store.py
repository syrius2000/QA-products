from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quality_loop.case_store import CaseStore
from quality_loop.errors import QualityLoopError


class CaseStoreTest(unittest.TestCase):
    def test_init_case_creates_case_json_and_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(Path(temp_dir))
            data = {"case_metadata": {"case_id": "QMS-0001", "case_revision": 1}}

            store.init_case("QMS-0001", data)

            case_path = Path(temp_dir) / "QMS-0001" / "case.json"
            evidence_dir = Path(temp_dir) / "QMS-0001" / "evidence"
            self.assertTrue(case_path.is_file())
            self.assertTrue(evidence_dir.is_dir())
            loaded = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual("QMS-0001", loaded["case_metadata"]["case_id"])
            self.assertEqual(1, loaded["case_metadata"]["case_revision"])

    def test_init_case_fails_if_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(Path(temp_dir))
            data = {"case_metadata": {"case_id": "QMS-0001", "case_revision": 1}}
            store.init_case("QMS-0001", data)

            with self.assertRaises(QualityLoopError) as ctx:
                store.init_case("QMS-0001", data)
            self.assertEqual("case-already-exists", ctx.exception.error_code)

    def test_mutate_creates_backup_and_atomically_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(Path(temp_dir))
            init_data = {"case_metadata": {"case_id": "QMS-0001", "case_revision": 1}, "data": "initial"}
            store.init_case("QMS-0001", init_data)

            def update_fn(current: dict) -> tuple[dict, dict]:
                updated = dict(current)
                updated["case_metadata"] = dict(current["case_metadata"])
                updated["case_metadata"]["case_revision"] = 2
                updated["data"] = "modified"
                return updated, {"status": "ok", "rev": 2}

            result = store.mutate("QMS-0001", update_fn)
            self.assertEqual({"status": "ok", "rev": 2}, result)

            case_path = Path(temp_dir) / "QMS-0001" / "case.json"
            bak_path = Path(temp_dir) / "QMS-0001" / "case.json.bak"
            self.assertTrue(bak_path.is_file())

            loaded = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual(2, loaded["case_metadata"]["case_revision"])
            self.assertEqual("modified", loaded["data"])

            bak_loaded = json.loads(bak_path.read_text(encoding="utf-8"))
            self.assertEqual(1, bak_loaded["case_metadata"]["case_revision"])
            self.assertEqual("initial", bak_loaded["data"])

    def test_mutate_restores_on_write_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = CaseStore(Path(temp_dir))
            init_data = {"case_metadata": {"case_id": "QMS-0001", "case_revision": 1}, "data": "initial"}
            store.init_case("QMS-0001", init_data)

            def bad_update_fn(current: dict) -> tuple[dict, dict]:
                raise ValueError("Simulated unexpected failure during mutation")

            with self.assertRaises(ValueError):
                store.mutate("QMS-0001", bad_update_fn)

            # Original state must be preserved
            loaded = store.load("QMS-0001")
            self.assertEqual(1, loaded["case_metadata"]["case_revision"])
            self.assertEqual("initial", loaded["data"])


if __name__ == "__main__":
    unittest.main()
