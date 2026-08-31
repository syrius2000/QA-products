# TODO — Principal Engineer Repair v1.4.0

> Codexはこのファイルを進捗正本として更新すること。

---

# Phase 0 — Baseline

- [x] current archive / git revision記録
- [x] full tests実行
- [x] `109 tests` baseline確認
- [x] compileall確認
- [x] examples/schema確認
- [x] target files hash記録

### Log

```text
Date: 2026-08-31 (JST)
Agent: Codex (GPT-5)
Revision: f585ced + uncommitted Plan 016 worktree
Tests: unittest 115 passed; pytest 115 passed, 25 subtests passed; compileall success; examples/schema success
Target hashes:
  quality_loop/engine.py 13230e63a34cde93f9276a3598a9977d811e1ab5db59b3fe2ba2c4088a042889
  FUNCTIONAL_SPEC.md ef51cf13412654879c6d3cfed4fd5f395b5ddb5a0dcdfbe96235f9aa0667b909
  tests/test_v1_4_repair.py d2f3a6d4963cb36dc680d001905c24b120c7543c4ef064d4a8a337fdd79b3efa
Notes: 109 baseline tests plus 6 targeted v1.4.0 tests. Original v1.4.0 ZIP was preserved unchanged.
```

---

# Phase 1 — Shared Routing Logic

- [x] required Plan Finding helper確認
- [x] approved Plan Finding helper確認
- [x] pending Plan Finding helper作成/整理
- [x] duplicate routing logicを増やさない
- [x] unit test helper logic

### Checkpoint

- [x] unresolved caseからsubmit-plan/submit-responseを決定可能

---

# Phase 2 — verify() 全体解決判定

- [x] payload-local `all_resolved`を除去
- [x] canonical updated findingsでmaterial unresolved算出
- [x] all resolved → owner
- [x] cycle limit/early risk → final assessment
- [x] pending Plan-required → submit-plan
- [x] no pending Plan-required → submit-response
- [x] new High routing維持
- [x] Critical early risk guard維持

### Tests

- [x] F1 resolved / F2 open → Ownerへ行かない
- [x] F2 High → submit-plan
- [x] F2 Low → submit-response
- [x] F1/F2 resolved → Owner

---

# Phase 3 — Owner Rework Routing

- [x] `rework-requested`無条件submit-responseを削除
- [x] pending Plan-required判定
- [x] High residual → submit-plan
- [x] Low residual → submit-response
- [x] returned handoff open_items確認
- [x] submit-planを実行して成功
- [x] review-planへ進む

### Deadlock reproduction

- [x] 修正前reproduction testを追加
- [x] 修正後PASS

---

# Phase 4 — FUNCTIONAL_SPEC

- [x] reviewer-verification → implementer-plan記載
- [x] reviewer-verification → implementer-action条件記載
- [x] all material resolved → owner記載
- [x] owner rework → implementer-plan条件記載
- [x] owner rework → implementer-action条件記載
- [x] stale state description 0

---

# Phase 5 — Regression

- [x] Plan Gate
- [x] implementation_status
- [x] Final Risk coverage
- [x] Role Firewall
- [x] Evidence boundary
- [x] atomic write
- [x] idempotency
- [x] CAS/stale handoff
- [x] adaptive Medium
- [x] finding withdrawal
- [x] early Final Risk
- [x] Owner adjudication
- [x] schema/examples
- [x] compileall

---

# Phase 6 — Optional Cleanup

- [ ] old templates reference search
- [ ] unusedなら削除
- [ ] usedなら変更しない
- [x] cleanupがCore repairを遅らせていない

---

# FINAL CHECKPOINT

- [ ] QA-IND-001 closed（独立Reviewer verification待ち）
- [ ] QA-IND-002 closed（独立Reviewer verification待ち）
- [ ] QA-IND-003 closed（独立Reviewer verification待ち）
- [x] High deadlock 0
- [x] premature Owner handoff 0
- [x] Human負担増加 0
- [x] Skill Context増加 0
- [x] new architecture 0
- [x] formal FIX candidate（実装者側の候補判定。正式FIXは未判定）

## Verification Record

- Targeted tests: 6 passed
- Full regression: 115 passed
- `python -B -m compileall -q quality_loop tests`: success
- `python -B -m pytest -q --assert=plain -p no:cacheprovider`: 115 passed, 25 subtests passed
- Official Draft 2020-12 schema validation through the schema test: success
- AppleDouble: 0
- Package generation, external Skill placement, commit, and push: not performed

Technical implementation is locally verified. Formal closure and Owner disposition remain pending independent Reviewer verification.
