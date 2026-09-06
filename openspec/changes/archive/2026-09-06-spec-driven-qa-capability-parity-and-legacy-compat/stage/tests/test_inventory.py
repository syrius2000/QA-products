import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import inventory


class InventoryTest(unittest.TestCase):
    def test_legacy_public_runtime_inventory_has_43_unique_features(self):
        result = inventory.build_inventory()
        self.assertEqual(result["feature_count"], 43)
        self.assertEqual(result["legacy_compatible_count"], 24)
        self.assertEqual(result["new_contract_feature_count"], 19)
        self.assertEqual(len({row["feature_id"] for row in result["features"]}), 43)
        self.assertTrue(all(row["public_or_runtime_entry"] for row in result["features"]))

    def test_inventory_contains_contract_attributes(self):
        result = inventory.build_inventory()
        required = {"feature_id", "role", "path", "lines", "bytes", "sha256", "notes", "comparison_class", "legacy_presence"}
        self.assertTrue(all(required <= row.keys() for row in result["features"]))

    def test_wrong_inventory_count_is_rejected(self):
        rows = inventory.read_rows(inventory.default_inventory())
        with tempfile.TemporaryDirectory() as directory:
            fake_zip = Path(directory) / "empty.zip"
            import zipfile
            with zipfile.ZipFile(fake_zip, "w"):
                pass
            with self.assertRaisesRegex(ValueError, "expected 43"):
                inventory.validate_rows(rows[:1], fake_zip)


if __name__ == "__main__":
    unittest.main()
