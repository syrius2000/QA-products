import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import measure_size


class MeasureSizeTest(unittest.TestCase):
    def test_line_count_is_deterministic_for_final_newline(self):
        self.assertEqual(measure_size.line_count(b"a\nb\n"), 2)
        self.assertEqual(measure_size.line_count(b"a\nb"), 2)
        self.assertEqual(measure_size.line_count(b""), 0)

    def test_all_three_bundles_have_required_paths(self):
        report = measure_size.build_report(Path(__file__).parents[1])
        self.assertEqual(report["status"], "observed")
        self.assertEqual(len(report["bundles"]), 3)
        self.assertTrue(all(item["required_paths_present"] for item in report["bundles"]))
        self.assertTrue(report["integrity_checks"]["safety_functions_and_tests_preserved"])

    def test_compact_is_within_line_target(self):
        report = measure_size.build_report(Path(__file__).parents[1])
        compact = next(item for item in report["bundles"] if item["name"] == "compact")
        self.assertTrue(compact["line_target"]["within_threshold"])


if __name__ == "__main__":
    unittest.main()
