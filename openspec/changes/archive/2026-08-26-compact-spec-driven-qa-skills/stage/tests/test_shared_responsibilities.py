import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spec-driven-qa-bundle"))


class SharedResponsibilitiesTest(unittest.TestCase):
    def test_state_evidence_links_secrets_and_io_are_standard_library_modules(self):
        from shared_core.evidence import can_mark_fixed_and_verified, status_is_valid
        from shared_core.io import EXIT_OK, EXIT_REJECTED, encode_result
        from shared_core.links import classify_link, validate_link
        from shared_core.secrets import contains_secret, safe_diagnostic
        from shared_core.state import can_transition

        self.assertTrue(can_transition("needs-response", "submit"))
        self.assertFalse(can_transition("closed", "close"))
        self.assertTrue(status_is_valid("evidence-gap"))
        self.assertFalse(can_mark_fixed_and_verified("evidence-gap"))
        self.assertTrue(can_mark_fixed_and_verified("risk-accepted", owner_decision=True))
        self.assertTrue(validate_link("docs/handoff.md"))
        self.assertFalse(validate_link("file:///tmp/secret"))
        self.assertFalse(validate_link("../outside.md"))
        self.assertEqual(classify_link("https://example.invalid/spec"), "external")
        self.assertEqual(classify_link("file:///tmp/secret"), "rejected")
        self.assertTrue(contains_secret("token=hidden"))
        self.assertNotIn("hidden", encode_result(safe_diagnostic("secret", "token=hidden")))
        self.assertEqual((EXIT_OK, EXIT_REJECTED), (0, 2))


if __name__ == "__main__":
    unittest.main()
