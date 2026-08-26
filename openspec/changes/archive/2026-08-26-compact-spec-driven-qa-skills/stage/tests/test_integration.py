import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spec-driven-qa-bundle"))


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        from shared_core.integration import verified_candidate
        self.verify = verified_candidate
        self.handoff = {"case_revision": 3, "semantic_digest": "digest", "finding_ids": ["QA-1-F1"]}

    def test_valid_submission_becomes_candidate(self):
        submission = {"base_revision": 3, "expected_semantic_digest": "digest", "target_findings": ["QA-1-F1"], "responses": {"QA-1-F1": {"disposition": "fix-submitted"}}, "evidence": ["test-1"]}
        candidate = self.verify(self.handoff, submission)
        self.assertEqual(candidate["base_revision"], 3)
        self.assertEqual(len(candidate["submission_digest"]), 64)

    def test_stale_submission_is_rejected(self):
        submission = {"base_revision": 2, "expected_semantic_digest": "digest", "target_findings": ["QA-1-F1"], "responses": {"QA-1-F1": {}}, "evidence": ["test-1"]}
        with self.assertRaisesRegex(ValueError, "base_revision_mismatch"):
            self.verify(self.handoff, submission)


if __name__ == "__main__":
    unittest.main()
