import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NegativeEvalTest(unittest.TestCase):
    def test_negative_fixture_has_zero_violations(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "negative.json"
            result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/run_negative_eval.py"), "--output", str(output)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["violations"], [])


if __name__ == "__main__":
    unittest.main()
