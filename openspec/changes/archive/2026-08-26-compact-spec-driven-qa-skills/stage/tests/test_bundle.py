import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "spec-driven-qa-bundle"
sys.path.insert(0, str(ROOT / "scripts"))


class BundleTest(unittest.TestCase):
    def run_launcher(self, role, *args, cwd=None):
        launcher = BUNDLE / ("spec-driven-qa-review" if role == "reviewer" else "spec-driven-qa-author-response") / "launcher.py"
        env = {"PATH": os.environ.get("PATH", "")}
        return subprocess.run([sys.executable, "-S", str(launcher), *args], cwd=cwd, env=env, text=True, capture_output=True)

    def test_valid_bundle_and_role_firewall(self):
        result = self.run_launcher("author", "respond", "--json", '{"request_id":"r1"}', cwd=Path(tempfile.gettempdir()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["role"], "author")
        denied = self.run_launcher("author", "close", cwd=Path(tempfile.gettempdir()))
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(json.loads(denied.stderr)["code"], "operation_not_authorized")
        reviewer_denied = self.run_launcher("reviewer", "submit", cwd=Path(tempfile.gettempdir()))
        self.assertEqual(reviewer_denied.returncode, 2)
        self.assertEqual(json.loads(reviewer_denied.stderr)["code"], "operation_not_authorized")
        secret_denied = self.run_launcher("author", "close", "--json", '{"token":"must-not-echo"}', cwd=Path(tempfile.gettempdir()))
        self.assertEqual(secret_denied.returncode, 2)
        self.assertNotIn("must-not-echo", secret_denied.stdout + secret_denied.stderr)

    def test_standalone_missing_core_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "spec-driven-qa-bundle"
            shutil.copytree(BUNDLE, copy)
            shutil.rmtree(copy / "shared_core")
            launcher = copy / "spec-driven-qa-review" / "launcher.py"
            result = subprocess.run([sys.executable, "-S", str(launcher), "review"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
