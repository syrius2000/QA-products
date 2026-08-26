---
case_id: QA-0005
cycle: 2
action: author-response
performed_by:
  agent_id: cursor-composer-20260826-1908
  role: implementer
  tool: cursor
base_revision: unverified-no-git
result_revision: unverified-no-git
outcome: fix-submitted
completed_at: "2026-08-26T19:08:49+09:00"
---

# Cycle 02 Author Response

自己クローズなし。Finding 正本の `fixed-and-verified` は設定しない。Reviewer verification へ返却する。

## QA-0005-F01
- Disposition: `fix-submitted`
- 変更:
  - `resolve_in_workspace` / `require_workspace_existing_path` を追加。`modified_files` と相対 `test_evidence` は workspace 相対のみ。絶対パス・`file://`・resolve 後の配下脱出（`../`・symlink）を拒否。
  - cwd フォールバック `p.exists()` を廃止。
  - テスト: `test_verify_rejects_absolute_modified_file_outside_workspace` / `..._dotdot_...` / `..._symlink_...`
- Evidence: `pytest .../stage/tests -q` → **34 passed**（`openspec/changes/reviewer-verification-integrity-hardening/evidence/pytest-after-f01-boundary.txt`）
- 再現: workspace 外絶対パスを `modified_files` に渡すと ValueError（absolute paths are not accepted）。以前の success/verified は出ない想定。

## QA-0005-F02
- Disposition: `fix-submitted`
- 変更:
  - `evidence/c2-c3-digestion.md`: C3 を「部分消化 + evidence-gap。境界は F01 提出・verification 待ち」へ是正。当初の全面「消化」は誤記と明記。
  - lifecycle `tasks.md` 残余、`capability_matrix.md`、`security_qa_report.md` も過大完了を撤回。
- 境界実装の成否は F01 の reviewer-verification に従う。文書だけで C3 完了とはしない。
