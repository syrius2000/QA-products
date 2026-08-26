# QA Profiles

## Lite

Use for clearly low-risk, non-behavioral or very localized changes.

Minimum:

- explicit target
- short `review.md`
- unresolved `REQUIRED` marker check
- obvious Spec conflict check
- test/evidence status

Do not create heavy cycle machinery unless a finding requires it.

## Proportional Home

Use when all of the following are confirmed:

- the system is limited to a home or similarly closed LAN;
- it is non-safety-critical and non-regulated;
- it has no hard real-time or external SLA requirement;
- the operator accepts bounded availability or data-loss limitations appropriate to the device;
- resource constraints materially affect feasible controls.

Prioritize:

- preservation of observation meaning and schema integrity;
- duplicate, missing, and corrupted data behavior;
- bounded loss visibility, recovery source, and operator alerts;
- restart, overflow, migration, and failure behavior that affects the stated Purpose;
- controls that prevent secrets from entering the repository or being exposed beyond the agreed boundary.

Do not require production-grade redundancy, persistent queues, passwordless administration, or repository-wide credential refactoring solely because they are generally recommended. Record them as operational hygiene or a decision request when they are not Purpose/Spec requirements.

This profile does not make the following acceptable by default: unbounded data destruction, misleading measurements, real secrets committed to source control, external exposure beyond the stated boundary, or a failure that defeats the stated Purpose. If any profile condition is unknown, use `standard` or record `INSUFFICIENT-CONTEXT` until clarified.

For this profile, distinguish:

- `unverified`: the environment or evidence was unavailable;
- `failed`: the behavior was observed to violate a requirement or fail reproducibly;
- `risk-accepted`: an owner explicitly accepted a residual risk with rationale, controls, and a review trigger.

## Standard (default)

Use for ordinary feature work and module changes.

Required:

- baseline
- `review.md`
- `findings.yaml`
- `traceability.yaml`
- `events.jsonl`
- cycle records
- independent reviewer
- author response + reviewer verification for blocking findings

## Strict

Use for high-impact areas such as:

- authentication/authorization
- data deletion or irreversible migrations
- financial/payment logic
- transaction/idempotency boundaries
- regulated or submission-facing data
- statistical estimation logic
- missing-data transformation
- safety-critical decisions
- security-sensitive code
- high-cost or externally destructive automation

Additional expectations:

- stronger baseline integrity (revision + hashes when practical)
- execution evidence for important claims
- explicit rollback/containment review
- human adjudication for unresolved Critical/High findings
- High findings cannot be silently auto-risk-accepted
- environment reproducibility details
