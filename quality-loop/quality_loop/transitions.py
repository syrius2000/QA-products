from __future__ import annotations


EXPECTED_STATE = {
    "review": "reviewer-action",
    "submit-response": "implementer-action",
    "verify": "reviewer-verification",
    "adjudicate": "owner-adjudication",
}

EXPECTED_ROLE = {
    "review": "reviewer",
    "submit-response": "implementer",
    "verify": "reviewer",
    "adjudicate": "owner",
}

COMMON_UPDATE_FIELDS = {
    "operation_id",
    "actor_id",
    "role",
    "invocation_id",
    "previous_handoff_id",
    "expected_case_revision",
}

ALLOWED_FIELDS = {
    "review": COMMON_UPDATE_FIELDS | {"findings", "rereviews", "evidence"},
    "submit-response": COMMON_UPDATE_FIELDS
    | {"changed_targets", "responses", "evidence"},
    "verify": COMMON_UPDATE_FIELDS
    | {"verifications", "new_findings", "change_observation", "evidence"},
    "adjudicate": COMMON_UPDATE_FIELDS
    | {
        "decision",
        "rationale",
        "conditions",
        "residual_risks",
        "review_trigger",
        "baseline_update",
        "implementation_authorization",
        "additional_cycles",
        "dry_run",
        "confirm",
    },
}
