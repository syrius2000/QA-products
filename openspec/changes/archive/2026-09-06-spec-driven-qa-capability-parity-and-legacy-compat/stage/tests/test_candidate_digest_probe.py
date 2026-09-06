import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import candidate_digest_probe


class CandidateDigestProbeTest(unittest.TestCase):
    def test_stale_semantic_digest_is_rejected_without_inventing_other_contracts(self):
        report = candidate_digest_probe.build_report(Path(__file__).parents[1])
        self.assertEqual(report["status"], "observed")
        self.assertEqual(report["actual"], "reject")
        self.assertEqual(report["content_digest_contract"], "not-applicable")
        self.assertEqual(report["digest_version_contract"], "not-applicable")


if __name__ == "__main__":
    unittest.main()
