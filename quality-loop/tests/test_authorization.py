from __future__ import annotations

import unittest

from quality_loop.authorization import (
    validate_create_authorization,
    validate_operation_role,
    validate_status_transition_authorization,
    validate_target_modification_authorization,
)
from quality_loop.errors import QualityLoopError


class AuthorizationTest(unittest.TestCase):
    def test_only_owner_can_create_case(self) -> None:
        validate_create_authorization({"role": "owner"})

        for invalid_role in ("reviewer", "implementer", "admin", "guest"):
            with self.assertRaises(QualityLoopError) as ctx:
                validate_create_authorization({"role": invalid_role})
            self.assertEqual("role-not-allowed", ctx.exception.error_code)

    def test_operation_role_must_match_expected_role(self) -> None:
        # Expected reviewer
        validate_operation_role(
            operation="review",
            requested_role="reviewer",
            expected_role="reviewer",
        )

        with self.assertRaises(QualityLoopError) as ctx:
            validate_operation_role(
                operation="review",
                requested_role="implementer",
                expected_role="reviewer",
            )
        self.assertEqual("wrong-role", ctx.exception.error_code)

    def test_implementer_cannot_self_close_or_change_case_status(self) -> None:
        with self.assertRaises(QualityLoopError) as ctx:
            validate_status_transition_authorization(
                role="implementer",
                operation="submit-response",
                target_case_status="accepted",
            )
        self.assertEqual("self-close-not-allowed", ctx.exception.error_code)

        with self.assertRaises(QualityLoopError) as ctx:
            validate_status_transition_authorization(
                role="implementer",
                operation="submit-response",
                target_case_status="closed",
            )
        self.assertEqual("self-close-not-allowed", ctx.exception.error_code)

    def test_reviewer_cannot_modify_artifacts(self) -> None:
        with self.assertRaises(QualityLoopError) as ctx:
            validate_target_modification_authorization(
                role="reviewer",
                changed_targets=["src/app.py"],
                allowed_targets=["src/app.py"],
            )
        self.assertEqual("artifact-modification-not-allowed", ctx.exception.error_code)

    def test_implementer_can_only_modify_allowed_targets(self) -> None:
        # Allowed target modification
        validate_target_modification_authorization(
            role="implementer",
            changed_targets=["src/app.py"],
            allowed_targets=["src/app.py", "src/utils.py"],
        )

        # Unauthorized target modification
        with self.assertRaises(QualityLoopError) as ctx:
            validate_target_modification_authorization(
                role="implementer",
                changed_targets=["src/secret.py"],
                allowed_targets=["src/app.py"],
            )
        self.assertEqual("unauthorized-target-modification", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
