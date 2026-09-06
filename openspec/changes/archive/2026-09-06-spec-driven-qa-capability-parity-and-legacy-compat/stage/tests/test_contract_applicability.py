import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import contract_applicability


class ContractApplicabilityTest(unittest.TestCase):
    def test_contract_applicability_is_explicit(self):
        report = contract_applicability.build_report(Path(__file__).parents[1])
        rows = {(row["version"], row["control"]): row["status"] for row in report["rows"]}
        self.assertEqual(rows[("legacy", "digest-contract")], "not-applicable")
        self.assertEqual(rows[("candidate", "empty-or-missing-evidence")], "observed")
        self.assertEqual(rows[("compact", "unknown-digest-version")], "observed")


if __name__ == "__main__":
    unittest.main()
