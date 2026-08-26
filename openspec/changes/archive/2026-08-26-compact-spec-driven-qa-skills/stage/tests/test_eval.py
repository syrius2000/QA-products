import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvalTest(unittest.TestCase):
    def test_batch_report_separates_compatibility_and_diagnostic_differences(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/run_eval.py"), "--output", str(output)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["fixture_layers_complete"])
            self.assertIn("contract_differences", report)
            self.assertIn("legacy_compatibility_differences", report)
            self.assertIn("diagnostic_differences", report)


if __name__ == "__main__":
    unittest.main()
