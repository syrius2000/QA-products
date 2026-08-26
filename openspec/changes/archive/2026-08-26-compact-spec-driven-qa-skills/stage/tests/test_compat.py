import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CompatibilityTest(unittest.TestCase):
    def invoke(self, role, operation, payload):
        return subprocess.run([sys.executable, "-S", str(ROOT / "scripts/compat_cli.py"), role, operation, "--json", json.dumps(payload)], text=True, capture_output=True)

    def test_legacy_success_preserves_comparable_fields(self):
        result = self.invoke("reviewer", "handoff", {"contract_version": "v1.1", "state": "needs-response", "side_effects": ["handoff"]})
        self.assertEqual(result.returncode, 0)
        value = json.loads(result.stdout)
        self.assertEqual({key: value[key] for key in ("exit_code", "contract", "state", "side_effects")}, {"exit_code": 0, "contract": "v1.1", "state": "needs-response", "side_effects": ["handoff"]})

    def test_unknown_major_and_forbidden_operation_are_rejected(self):
        unknown = self.invoke("author", "respond", {"contract_version": "v2.0"})
        self.assertEqual(unknown.returncode, 2)
        denied = self.invoke("author", "close", {"contract_version": "v1.0"})
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(json.loads(denied.stdout)["state"], "unchanged")

    def test_v10_and_v11_legacy_fixture_are_read_only_compatible(self):
        fixture = json.loads((ROOT / "fixtures/legacy/legacy-contracts.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["expected"]["mode"], "read-only-adapter")
        for version in fixture["versions"]:
            result = self.invoke("reviewer", "review", {"contract_version": version, "state": "unchanged", "side_effects": []})
            self.assertEqual(result.returncode, 0)
            expected = version if version.startswith("v") else "v" + version
            self.assertEqual(json.loads(result.stdout)["contract"], expected)
        self.assertFalse(fixture["expected"]["history_rewritten"])


if __name__ == "__main__":
    unittest.main()
