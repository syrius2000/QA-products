import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import fixture_index


class FixtureIndexTest(unittest.TestCase):
    def test_all_comparison_classes_cover_all_features(self):
        inventory = Path(__file__).parents[1] / "evidence" / "feature-surface-inventory.json"
        index = fixture_index.build_index(inventory)
        fixture_index.validate_index(index)
        self.assertEqual(set(index["classes"]), set(fixture_index.CLASSES))
        self.assertEqual(index["feature_count"], 43)

    def test_incomplete_index_is_rejected(self):
        inventory = Path(__file__).parents[1] / "evidence" / "feature-surface-inventory.json"
        index = fixture_index.build_index(inventory)
        index["classes"].pop("negative")
        with self.assertRaisesRegex(ValueError, "classes are incomplete"):
            fixture_index.validate_index(index)


if __name__ == "__main__":
    unittest.main()
