# machine_schema — `03_machine.json`

Required schema name: `blind-qa-cycle-v1`

```json
{
  "schema": "blind-qa-cycle-v1",
  "topic": "string",
  "cycle": 1,
  "start_mode": "prepared",
  "preparation_plan": {
    "path": "docs/Artifacts/qa_cycles/<topic>/c<N>/00_plan.md",
    "sha": "<full-sha>"
  },
  "baseline": "<full-sha>",
  "reviewed": "<full-sha>",
  "audience": "cloud",
  "remote_visibility": "pushed",
  "requirements_fingerprint": "<sha256>",
  "gate": "HOLD",
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "text": "exact text from 00_invite.md",
      "result": "UNVERIFIED",
      "evidence": "path:line or reason not executed"
    }
  ],
  "reviewer_materials": [
    {
      "path": "quality-loop/skills/blind-qa-cycle/SKILL.md",
      "expected_sha256": "<sha256>",
      "observed_sha256": "<sha256 or unavailable>",
      "read": true
    }
  ],
  "focus_packs": ["math-definitions"],
  "findings": [
    {
      "id": "QA-MATH-H01",
      "severity": "High",
      "status": "OPEN",
      "title": "short title",
      "repair_surface": "docs"
    }
  ],
  "tasks": [
    {
      "id": "T-01",
      "closes": "QA-MATH-H01",
      "done": false,
      "verify": "how to verify"
    }
  ]
}
```

## Field rules

| Field | Rule |
| :--- | :--- |
| `audience` | `local` \| `cloud` (required on new cycles) |
| `start_mode` | `prepared` \| `post-change` \| `re-qa` (required on new cycles); must match invite. |
| `preparation_plan` | Required for prepared cycles: exact repo-relative plan path and full plan commit SHA. Omit for post-change and re-qa cycles. |
| `remote_visibility` | `local-only` \| `pushed` (must match audience) |
| `gate` | `PASS` \| `HOLD` \| `FAIL` \| `INCONCLUSIVE` only |
| `severity` | `High` \| `Medium` \| `Low` \| `PASS` (notes) |
| `status` | `OPEN` \| `CLOSED` |
| `repair_surface` | `docs` \| `code` \| `spec` \| `plan` |
| `closes` | Must equal a `findings[].id` |
| `requirements_fingerprint` | Must equal the invite value |
| `acceptance_criteria` | New cycles: exact ordered copy of every invite criterion, including ID, text, result, and evidence |
| `reviewer_materials` | New cycles: all pinned files; any unreadable or hash-mismatched file requires Gate `HOLD` |
| `00_plan.md` | Optional implementation-side preparation artifact. It is already in the prepared Baseline tree and is not part of Baseline..Reviewed diff or Reviewer output. |
| SHAs | Full 40-char preferred; never ambiguous short-only without resolve |

Additional keys are allowed; do not remove required keys.
