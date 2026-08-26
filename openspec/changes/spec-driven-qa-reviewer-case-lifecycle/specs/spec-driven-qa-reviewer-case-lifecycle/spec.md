## Purpose

Defines the complete lifecycle of a QA review case managed by the Reviewer agent, encompassing review case initialization, blind-first independent review recording, finding and traceability management, deterministic handoff generation, author submission verification, cycle limit control, and terminal case closure.

## ADDED Requirements

### Requirement: Review Case Initialization
The Reviewer SHALL initialize a QA review case directory with unique identifier and required metadata (target scope, purpose, risk profile, and baseline revisions) in a reproducible manner.

#### Scenario: Successful review case initialization
- **WHEN** user or caller requests initializing a review case with valid target path, purpose document, and profile ('standard' or 'proportional-home')
- **THEN** system SHALL create the case directory structure under docs/ADR/QA/ with initialized review.md, findings.yaml, traceability.yaml, and events.jsonl recording the initialization event

#### Scenario: Reject initialization when target or purpose is missing
- **WHEN** caller requests initializing a review case without an explicit file or directory target, or without a resolvable purpose
- **THEN** system SHALL reject the initialization request with a non-zero exit code and an explanatory error message

### Requirement: Independent Review and Finding Management
The Reviewer SHALL perform a blind-first independent evaluation against Purpose and Spec, recording findings with mandatory classification, severity rationale, and claim-to-evidence traceability.

#### Scenario: Record independent review findings with proportionality classification
- **WHEN** Reviewer records findings for an evaluated target
- **THEN** system SHALL require each finding to have a unique ID, category, severity, evidence references, and purpose classification ('spec-required', 'purpose-critical', 'operational-hygiene', or 'out-of-scope')

#### Scenario: Reject finding lacking evidence or classification
- **WHEN** Reviewer attempts to record a finding without evidence references or without a purpose classification
- **THEN** system SHALL reject the finding record as invalid and preserve the existing review state

### Requirement: Deterministic Handoff Generation
The Reviewer SHALL generate a deterministic handoff.md derived strictly from canonical review metadata and open findings to pass to the Author agent.

#### Scenario: Generate valid Contract v1.2 handoff
- **WHEN** Reviewer initiates a handoff to the Author after completing an independent review cycle
- **THEN** system SHALL generate handoff.md containing origin metadata, case revision, content digest, active open finding IDs, and scoped implementation permissions

### Requirement: Reviewer Verification and Submission Ingestion
The Reviewer SHALL validate Author responses and fix submissions against the handoff contract, verifying revisions and evidence before updating the canonical review case.

#### Scenario: Verify valid author fix submission
- **WHEN** Author submits a fix referencing valid open finding IDs, base revision, result revision, and test evidence
- **THEN** Reviewer SHALL verify that the base revision matches, modified files exist, and record the verification outcome in cycle verification artifacts and review summary

#### Scenario: Reject author self-close or unknown finding injection
- **WHEN** Author submission attempts to set status to 'closed' or 'fixed-and-verified' directly, or references finding IDs not present in handoff
- **THEN** Reviewer SHALL reject the submission and flag a protocol contract violation

### Requirement: Cycle Limit Control and Escalation
The Reviewer SHALL enforce maximum automated cycle limits based on the configured QA profile and transition unresolved cases to adjudication-required.

#### Scenario: Enforce cycle limit and escalate to human adjudication
- **WHEN** automated author-reviewer review cycles reach the profile limit (e.g. 2 for standard, 3 for strict) with unresolved material findings remaining
- **THEN** system SHALL transition the review case state to 'adjudication-required' and halt automated iterative cycling

### Requirement: Terminal Close and Result Determination
The Reviewer SHALL evaluate case closure invariants and assign an authoritative terminal status.

#### Scenario: Close case successfully with accepted status
- **WHEN** all REQUIRED blocking markers are resolved, all Critical findings are verified fixed, and High findings are verified or adjudicated with complete 5-element risk acceptance metadata
- **THEN** Reviewer SHALL update case status to a valid terminal outcome ('accepted' or 'accepted-with-residual-risk') and append a final closure event to events.jsonl

#### Scenario: Prevent closure when blocking markers or unresolved critical findings remain
- **WHEN** closure is requested while unresolved REQUIRED markers or unadjudicated Critical findings remain
- **THEN** Reviewer SHALL reject the closure request and keep the case in an active non-terminal state
