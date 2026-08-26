import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import contract_applicability


class ContractApplicabilityTest(unittest.TestCase):
    def test_gaps_are_explicit_and_not_pass_eligible(self):
        report = contract_applicability.build_report(Path(__file__).parents[1])
        self.assertEqual(report["status"], "evidence-gap")
        self.assertFalse(report["pass_eligible"])
        rows = {(row["version"], row["control"]): row["status"] for row in report["rows"]}
        self.assertEqual(rows[("legacy", "digest-contract")], "not-applicable")
        self.assertEqual(rows[("candidate", "empty-or-missing-evidence")], "failed")
        self.assertEqual(rows[("compact", "unknown-digest-version")], "observed")


if __name__ == "__main__":
    unittest.main()
