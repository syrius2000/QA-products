# Focus pack: provenance-plans

Use when the invite lists `provenance-plans`.

## Audit criteria

1. **Plan ID immutability:** `implementation_plan_NNN_*.md` must not be overwritten by a different case. New work uses NNN = max existing + 1 under `docs/Artifacts/plans/` (legacy flat plans remain readable).
2. **Source-of-truth file lists** in plans must name modules that exist in the reviewed tree (no hallucinated paths).
3. Portal docs (`AGENTS.md`, root `README.md`, `docs/reference/README.md`) must not contradict newly added “P0 satisfied / missing” status within the same reviewed commit.
4. Repair surface for provenance breaks is usually `plan` or `docs`, not silent history rewrite.

## Placement contract

See [`docs/Archives/README.md`](../../../../docs/Archives/README.md) for the repository's document/archive map. New Artifacts remain in the location and naming contract stated by the current repository instructions; do not infer that a historical plan was archived unless its copy exists at the stated path.
