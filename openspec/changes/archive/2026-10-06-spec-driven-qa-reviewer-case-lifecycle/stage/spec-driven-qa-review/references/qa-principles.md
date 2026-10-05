# QA Principles

## 1. Purpose is highest-level intent, not unquestionable truth

Purpose frames why the work exists. QA may still identify a Purpose as ambiguous, contradictory, infeasible, unmeasurable, or incomplete.

## 2. Mutually criticizable evidence

Evaluate both directions, not only top-down traceability:

- Purpose ↔ Spec
- Spec ↔ Plan / Tasks
- Plan ↔ Implementation
- Implementation ↔ Evidence
- Evidence ↔ Purpose

An implementation may reveal defects in the Spec. A test may reveal that a stated Purpose cannot be operationalized. A Plan may introduce constraints not justified by the Spec.

## 3. Claimed is not observed

Keep four layers distinct:

1. **Intended** — Purpose / Spec
2. **Planned** — Plan / Tasks
3. **Claimed** — Implementation Report / author explanation
4. **Observed / Verified** — code, runtime behavior, tests, measurable evidence

## 4. Do not confuse existence with sufficiency

Evidence exists ≠ evidence is relevant ≠ evidence is sufficient ≠ claim is proven.

## 5. Make uncertainty explicit

Valid outcomes include:

- `not-assessable`
- `insufficient-context`
- `insufficient-evidence`
- `conflicting-sources`
- `outside-scope`

## 6. Independent review before reconciliation

AI-2 should create an independent view before reading AI-1's self-justification. Reconciliation occurs only after the first findings are frozen.

## 7. Author cannot self-close findings

AI-1 may accept, reject with evidence, fix, defer, or request risk acceptance. AI-2 verifies. A human or AI-3 adjudicates unresolved disagreements when required.

## 8. Preserve history

Never overwrite prior review cycles just to make the latest state look clean. The review case is an audit trail.

## 9. Risk-based burden

Do not apply a Strict process to every trivial change. Excessive process becomes ritual and reduces signal.

## 10. Human accountability is explicit

This Skill can support review and evidence management. It does not certify that a person understood the code, and it does not replace regulatory, security, safety, or clinical accountability.

## 11. Match assurance burden to the Purpose

Start by recording the deployment boundary, criticality, timing requirements, tolerated loss, recovery source, resource constraints, and operating model. Do not apply a stricter profile merely because a generic best practice exists. If a missing assumption could change the outcome, record `INSUFFICIENT-CONTEXT` rather than guessing.

## 12. Separate obligation source from severity

Classify each Finding as `spec-required`, `purpose-critical`, `operational-hygiene`, or `out-of-scope` before assigning severity. Severity describes impact; classification describes why the Finding belongs in the review. Security recommendations without a Purpose, Spec, or agreed threat-model basis are not automatic Critical or High findings.

## 13. Separate observation from disposition

`unverified` means the evidence could not be obtained. `failed` means a requirement violation or reproducible failure was observed. An owner may record `risk-accepted` for a residual risk, but this does not change the technical observation to `fixed-and-verified`.

## 14. Preserve data meaning under proportional QA

Even in a home or resource-constrained profile, prioritize schema integrity, duplicate suppression, bounded loss visibility, migration provenance, and recovery behavior. Fixed or synthetic values must not be presented as measured values without an explicit quality marker or documented analytical treatment.

## 15. Make risk acceptance auditable

A risk acceptance record must name the owner, explain the rationale, state scope and assumptions, list compensating controls, and define an expiry date or review trigger. Without these fields, the risk remains unresolved and cannot satisfy a closure rule.
