import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import candidate_contract_probe


class CandidateContractProbeTest(unittest.TestCase):
    def test_empty_evidence_acceptance_is_explicitly_observed(self):
        report = candidate_contract_probe.build_report(Path(__file__).parents[1])
        self.assertEqual(report["status"], "observed-violation")
        self.assertEqual(report["expected"], "reject")
        self.assertEqual(report["actual"], "accept")
        self.assertTrue(report["accepted"])


if __name__ == "__main__":
    unittest.main()
