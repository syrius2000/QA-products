import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spec-driven-qa-bundle"))


class HandoffGuardsTest(unittest.TestCase):
    def test_current_handoff_passes_and_stale_data_is_rejected(self):
        from shared_core.guards import validate_handoff
        current = {"case_revision": 4, "semantic_digest": "sem-4", "content_digest": "content-4", "case_status": "needs-response"}
        handoff = {"case_revision": 4, "expected_semantic_digest": "sem-4", "expected_content_digest": "content-4"}
        self.assertEqual(validate_handoff(handoff, current), [])
        stale = dict(handoff, case_revision=3)
        self.assertIn("revision_conflict", validate_handoff(stale, current))
        tampered = dict(handoff, expected_content_digest="changed")
        self.assertIn("content_digest_stale_or_tampered", validate_handoff(tampered, current))


if __name__ == "__main__":
    unittest.main()
