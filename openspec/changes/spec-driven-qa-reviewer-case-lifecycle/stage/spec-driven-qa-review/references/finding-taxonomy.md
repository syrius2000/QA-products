# Finding Taxonomy

## Categories

## Purpose classification

Every material Finding must identify where its obligation comes from:

- `spec-required`: required by Purpose, Spec, acceptance criteria, or an authoritative contract;
- `purpose-critical`: directly threatens the stated purpose or the meaning/integrity of data;
- `operational-hygiene`: a recommended control or maintainability improvement without a direct stated obligation;
- `out-of-scope`: outside the explicit target, threat model, or agreed review boundary.

This classification is separate from severity. A security recommendation that is not grounded in the Purpose, Spec, or threat model must not become Critical or High merely by convention.

### purpose-gap
Purpose is missing, ambiguous, internally inconsistent, non-measurable, or not represented downstream.

### spec-drift
Observed implementation behavior conflicts with a Specification requirement or acceptance criterion.

### plan-drift
Implementation differs materially from the Plan without an explicit, justified decision update.

### coverage-gap
A requirement, task, or promised behavior has no identifiable implementation.

### evidence-gap
Implementation may exist, but evidence is missing, irrelevant, weak, stale, or insufficient.

### unspecified-implementation
Implementation introduces material behavior not represented in Purpose/Spec/Plan.

### unverified-assumption
Implementation relies on an unstated assumption: ordering, data volume, idempotency, timezone, concurrency, encoding, null semantics, platform behavior, etc.

### contradictory-evidence
Spec, code, test, ADR, report, or runtime evidence disagree.

### maintainability-risk
Responsibilities, boundaries, invariants, or change impact are unclear enough to create maintenance risk.

### security-risk
Security-relevant behavior or unsafe assumptions are identified.

### portability-risk
Behavior depends unexpectedly on OS, filesystem, shell, encoding, locale, line endings, case sensitivity, package environment, or runtime version.

### regression
A previously fixed/verified semantic fingerprint reappears.

## Severity

### Critical
Immediate catastrophic, security, integrity, regulatory, destructive, or unrecoverable risk; or release must not proceed without adjudication.

### High
Material Purpose/Spec failure, significant data integrity issue, unhandled destructive edge case, or evidence gap for a critical requirement.

### Medium
Meaningful correctness, maintainability, testability, observability, or portability deficiency not normally release-blocking by itself.

### Low
Minor issue, clarity improvement, low-impact edge case, or non-blocking maintainability improvement.

## Severity rationale

Severity must include an explicit rationale. Do not infer severity merely from category.

## Finding statuses

- `new`
- `open`
- `accepted`
- `rejected-with-evidence`
- `fix-submitted`
- `fixed-and-verified`
- `partially-fixed`
- `disputed`
- `deferred`
- `risk-accepted`
- `not-applicable`
- `duplicate`
- `reopened`
- `regression`
- `closed`

## Technical disposition and owner disposition

Record technical verification separately from owner disposition:

Technical disposition:

- `fixed-and-verified`
- `partially-fixed`
- `unverified`
- `failed`

Owner disposition:

- `accepted`
- `risk-accepted`
- `deferred`
- `out-of-scope`
- `not-applicable`

`risk-accepted` does not mean `fixed-and-verified`. A risk acceptance record must identify the owner, rationale, scope or assumptions, compensating controls, and expiry or review trigger.
