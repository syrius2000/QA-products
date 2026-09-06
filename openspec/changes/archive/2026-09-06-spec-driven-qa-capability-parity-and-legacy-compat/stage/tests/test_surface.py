import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import inventory
import surface


class SurfaceInventoryTest(unittest.TestCase):
    def test_surface_has_all_contract_fields(self):
        result = surface.build_surface(inventory.build_inventory())
        self.assertEqual(result["feature_count"], 43)
        for row in result["features"]:
            self.assertEqual(set(row["contract_surface"]), set(surface.SURFACE_FIELDS))
            self.assertTrue(all(item["status"] in surface.STATUS_VALUES for item in row["contract_surface"].values()))

    def test_documentation_is_not_applicable_and_python_is_unverified(self):
        result = surface.build_surface(inventory.build_inventory())
        docs = [row for row in result["features"] if row["surface_type"] == "documentation"]
        scripts = [row for row in result["features"] if row["surface_type"] == "executable"]
        self.assertTrue(docs)
        self.assertTrue(scripts)
        self.assertTrue(all(item["status"] == "not_applicable" for row in docs for item in row["contract_surface"].values()))
        self.assertTrue(all(item["status"] == "unverified" for row in scripts for item in row["contract_surface"].values()))

    def test_invalid_surface_schema_is_rejected(self):
        result = surface.build_surface(inventory.build_inventory())
        result["features"][0]["contract_surface"].pop("side_effects")
        with self.assertRaisesRegex(ValueError, "incomplete contract surface"):
            surface.validate_surface(result)


if __name__ == "__main__":
    unittest.main()
