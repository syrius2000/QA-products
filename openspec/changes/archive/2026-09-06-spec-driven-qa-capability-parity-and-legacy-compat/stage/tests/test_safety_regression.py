import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import safety_regression


class SafetyRegressionTest(unittest.TestCase):
    def test_compact_checks_pass(self):
        checks = safety_regression.compact_checks(Path(__file__).parents[1] / "spec-driven-qa-bundle")
        self.assertTrue(checks)
        self.assertTrue(all(item["status"] == "passed" for item in checks))

    def test_candidate_checks_pass(self):
        root = Path(__file__).parents[4] / "changes/archive/2026-08-26-improve-spec-driven-qa-contract-v1-2/stage"
        checks = safety_regression.candidate_checks(root)
        self.assertTrue(checks)
        self.assertTrue(all(item["status"] == "passed" for item in checks))

    def test_report_has_no_secret_values(self):
        with tempfile.TemporaryDirectory() as directory:
            report = safety_regression.build_report(Path(__file__).parents[1])
            rendered = str(report)
            self.assertNotIn("synthetic", rendered)
            self.assertEqual(report["status"], "observed")
            self.assertEqual(report["contract_regression"]["status"], "observed")


if __name__ == "__main__":
    unittest.main()
