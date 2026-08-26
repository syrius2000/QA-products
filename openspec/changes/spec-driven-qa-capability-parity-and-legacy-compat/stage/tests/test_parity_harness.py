import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import parity_harness


class ParityHarnessTest(unittest.TestCase):
    def test_manifest_contains_three_distinct_bundles(self):
        manifest = parity_harness.build_manifest()
        self.assertEqual(manifest["schema_version"], "parity-manifest-1")
        bundles = {item["name"]: item for item in manifest["bundles"]}
        self.assertEqual(set(bundles), {"legacy", "candidate", "compact"})
        self.assertEqual(len({item["source_sha256"] for item in bundles.values()}), 3)
        for item in bundles.values():
            self.assertGreater(item["file_count"], 0)

    def test_cache_and_bytecode_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.txt").write_text("ok\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "bad.pyc").write_bytes(b"bad")
            records = parity_harness.directory_records(root)
            self.assertEqual([item["path"] for item in records], ["keep.txt"])

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("outside\n", encoding="utf-8")
            (root / "link.txt").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink is not allowed"):
                parity_harness.directory_records(root)

    def test_manifest_is_json_serializable(self):
        manifest = parity_harness.build_manifest()
        json.dumps(manifest, ensure_ascii=False, sort_keys=True)

    def test_saved_manifest_detects_changes_and_unknown_bundle(self):
        manifest = parity_harness.build_manifest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(parity_harness.validate_saved_manifest(path, "legacy")["schema_version"], "parity-manifest-1")
            with self.assertRaisesRegex(ValueError, "unknown bundle"):
                parity_harness.validate_saved_manifest(path, "missing")
            tampered = json.loads(path.read_text())
            tampered["bundles"][0]["source_sha256"] = "0" * 64
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                parity_harness.validate_saved_manifest(path)


if __name__ == "__main__":
    unittest.main()
