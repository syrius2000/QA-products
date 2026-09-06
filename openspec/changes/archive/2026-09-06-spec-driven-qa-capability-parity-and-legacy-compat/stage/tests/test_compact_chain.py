import tempfile
import sys
import unittest
from pathlib import Path

COMPACT = Path(__file__).parents[1] / "spec-driven-qa-bundle"
sys.path.insert(0, str(COMPACT))

from shared_core.chain import ChainError, chain_review, chain_submit, chain_verify, run_chain


class CompactChainTest(unittest.TestCase):
    def test_reviewer_author_reviewer_chain_persists_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = str(Path(directory) / "workspace")
            review = chain_review({"case_id": "QA-1001", "workspace": workspace})
            submission = chain_submit({
                "case_id": "QA-1001", "workspace": workspace, "submission_id": "submission-test",
                "base_revision": review["case_revision"],
                "expected_semantic_digest": review["semantic_digest"],
                "expected_content_digest": review["content_digest"],
                "target_findings": review["finding_ids"],
                "responses": {"QA-1001-F01": {"disposition": "accepted"}},
            })
            verification = chain_verify({
                "case_id": "QA-1001", "workspace": workspace, "submission_id": submission["submission_id"],
            })
            self.assertEqual(verification["verification"], "verified")
            self.assertNotEqual(review["semantic_digest"], review["content_digest"])
            case_dir = Path(workspace) / "qa-cases" / "QA-1001"
            self.assertTrue((case_dir / "handoff.md").is_file())
            self.assertTrue((case_dir / "submissions/submission-test.json").is_file())
            self.assertTrue((case_dir / "verification.json").is_file())

    def test_stale_digest_and_reviewer_owned_fields_are_rejected_without_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = str(Path(directory) / "workspace")
            review = chain_review({"case_id": "QA-1002", "workspace": workspace})
            base = {
                "case_id": "QA-1002", "workspace": workspace, "submission_id": "submission-rejected",
                "base_revision": review["case_revision"], "expected_semantic_digest": "0" * 64,
                "expected_content_digest": review["content_digest"], "target_findings": review["finding_ids"],
                "responses": {"QA-1002-F01": {"disposition": "accepted"}},
            }
            with self.assertRaisesRegex(ChainError, "semantic_digest_mismatch"):
                chain_submit(base)
            base["expected_semantic_digest"] = review["semantic_digest"]
            base["case_status"] = "closed"
            with self.assertRaisesRegex(ChainError, "reviewer_owned_field_rejected"):
                chain_submit(base)
            self.assertFalse((Path(workspace) / "qa-cases/QA-1002/submissions/submission-rejected.json").exists())

    def test_secret_input_and_unknown_role_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ChainError, "secret-in-chain-input"):
                chain_review({"case_id": "QA-1003", "workspace": str(Path(directory) / "workspace"), "api_key": "do-not-store"})
            with self.assertRaisesRegex(ChainError, "operation_not_authorized"):
                run_chain("author", "chain-verify", {"case_id": "QA-1003", "workspace": str(Path(directory) / "workspace")})

    def test_unknown_digest_version_and_workspace_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = str(Path(directory) / "workspace")
            with self.assertRaisesRegex(ChainError, "unsupported-digest-version"):
                chain_review({"case_id": "QA-1004", "workspace": workspace, "digest_version": "v9"})
            with self.assertRaisesRegex(ChainError, "workspace_boundary_violation"):
                chain_review({"case_id": "QA-1005", "workspace": workspace, "fixture_path": "/tmp/outside-fixture.json"})


if __name__ == "__main__":
    unittest.main()
