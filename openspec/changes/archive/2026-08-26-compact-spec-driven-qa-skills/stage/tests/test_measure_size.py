#!/usr/bin/env python3
"""measure_size.pyの決定論的集計fixture。標準ライブラリのみ。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from measure_size import measure


class MeasureSizeTest(unittest.TestCase):
    def test_counts_lines_bytes_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "included.txt").write_bytes(b"one\ntwo\n")
            (root / "no_final_newline.txt").write_bytes(b"one\ntwo")
            (root / "empty.txt").write_bytes(b"")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
            (root / ".pytest_cache").mkdir()
            (root / ".pytest_cache" / "ignored.txt").write_text("ignored", encoding="utf-8")
            result = measure(root)
            self.assertEqual(result["counts"], {"files": 3, "bytes": 15, "lines": 4})
            self.assertEqual(result["resident_files"], [])
            self.assertEqual([item["path"] for item in result["files"]], [
                "empty.txt", "included.txt", "no_final_newline.txt"
            ])

    def test_manifest_is_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            (root / "b.txt").write_text("b\n", encoding="utf-8")
            manifest = root / "MANIFEST.txt"
            manifest.write_text("a.txt\n", encoding="utf-8")
            result = measure(root, manifest)
            self.assertEqual(result["counts"], {"files": 1, "bytes": 2, "lines": 1})


if __name__ == "__main__":
    unittest.main()
