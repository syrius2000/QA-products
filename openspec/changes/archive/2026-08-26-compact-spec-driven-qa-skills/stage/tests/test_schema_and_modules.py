import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SchemaAndModulesTest(unittest.TestCase):
    def test_contract_fixture_is_accepted_and_invalid_is_rejected(self):
        accepted = ROOT / "fixtures/schema/accepted-contract.json"
        rejected = ROOT / "fixtures/schema/rejected-contract.json"
        result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/validate_schema.py"), str(accepted)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/validate_schema.py"), str(rejected)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)

    def test_shared_modules_import_without_external_dependency(self):
        sys.path.insert(0, str(ROOT / "spec-driven-qa-bundle"))
        from shared_core.authorization import allowed
        from shared_core.contract import validate_contract
        from shared_core.digest import content_digest
        self.assertTrue(allowed("author", "submit"))
        self.assertFalse(allowed("author", "close"))
        self.assertEqual(validate_contract({"case_id": "x", "case_revision": 0, "case_status": "open", "next_action": "review", "findings": [], "evidence": [], "digest_target": {"paths": []}}), [])
        self.assertEqual(len(content_digest({"x": 1})), 64)


if __name__ == "__main__":
    unittest.main()
