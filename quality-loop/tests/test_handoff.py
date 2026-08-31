from __future__ import annotations

import unittest

from quality_loop.errors import QualityLoopError
from quality_loop.handoff import issue_handoff, validate_handoff_receipt


class HandoffTest(unittest.TestCase):
    def test_issue_handoff_creates_complete_contract(self) -> None:
        handoff = issue_handoff(
            case_id="QMS-0001",
            issued_revision=2,
            next_role="implementer",
            next_action="submit-response",
            purpose="Findingへの回答と修正Evidenceの提出",
            inputs=["artifact/app.py"],
            open_issues=["F-001: ゼロ除算エラー"],
            expected_deliverables=["submit-response payload with Evidence"],
        )

        self.assertEqual("QMS-0001", handoff["case_id"])
        self.assertEqual(2, handoff["issued_revision"])
        self.assertEqual("implementer", handoff["next_role"])
        self.assertEqual("submit-response", handoff["next_action"])
        self.assertEqual("issued", handoff["status"])
        self.assertTrue(handoff["handoff_id"].startswith("hnd-"))
        self.assertEqual(["artifact/app.py"], handoff["inputs"])
        self.assertEqual(["F-001: ゼロ除算エラー"], handoff["open_issues"])

    def test_validate_handoff_receipt_success(self) -> None:
        current_handoff = {
            "handoff_id": "hnd-rev-1-001",
            "issued_revision": 1,
            "next_role": "reviewer",
            "next_action": "review",
            "status": "issued",
        }

        # Valid Check-Back receipt
        validate_handoff_receipt(
            current_handoff=current_handoff,
            received_handoff_id="hnd-rev-1-001",
            expected_case_revision=1,
            caller_role="reviewer",
        )

    def test_validate_handoff_receipt_mismatch_raises_error(self) -> None:
        current_handoff = {
            "handoff_id": "hnd-rev-1-001",
            "issued_revision": 1,
            "next_role": "reviewer",
            "next_action": "review",
            "status": "issued",
        }

        # Wrong handoff ID
        with self.assertRaises(QualityLoopError) as ctx:
            validate_handoff_receipt(
                current_handoff=current_handoff,
                received_handoff_id="hnd-wrong-id",
                expected_case_revision=1,
                caller_role="reviewer",
            )
        self.assertEqual("handoff-mismatch", ctx.exception.error_code)

        # Stale revision
        with self.assertRaises(QualityLoopError) as ctx:
            validate_handoff_receipt(
                current_handoff=current_handoff,
                received_handoff_id="hnd-rev-1-001",
                expected_case_revision=0,
                caller_role="reviewer",
            )
        self.assertEqual("revision-conflict", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
