---
case_id: QA-0006
cycle: 1
action: reviewer-verification
performed_by:
  agent_id: "cursor-composer-20260826-2058"
  role: reviewer
  tool: cursor
completed_at: "2026-08-26T20:58:58+09:00"
reviewed_revision: "unverified-no-git"
outcome: partially-fixed-cycle-continue
next_cycle_required: true
---

# Reviewer Verification — Cycle 1

## Revision verified

`unverified-no-git`（git管理外）。pytest再実行 **57 passed**（Author 23 + Reviewer 34）。

## Finding verification

### QA-0006-F01

Result: `partially-fixed`

Evidence:
- `canonical_finding_ids` + CLI `--case-dir`（省略時は handoff.parent）で正本照合する経路を確認。
- プローブ H: findings.yaml が handoff より広い Finding 集合のとき stale 拒否（CONFIRMED）。
- プローブ G: findings.yaml 欠落で CLI 拒否（CONFIRMED）。
- プローブ A: `canonical_case_dir=None` のライブラリ呼び出しでは自己整合 forged handoff が依然 `errors=[]`（FAILED residual）。
- `validate_and_save` が `validate_submission` を **case_dir無し** で再呼び出し（CONFIRMED code）。
- `canonical_finding_ids` は status を見ず全IDを収集。Reviewer lifecycle は open のみ（残差）。

Residual risk:
- 公開CLI以外・case_dir省略APIは正本未照合のまま受理しうる。
- closed Finding 混在時に digest 入力が Reviewer と不一致になりうる。

### QA-0006-F02

Result: `fixed-and-verified`

Evidence: `handoff_finding_ids` は `open_finding_ids` ブロックのみ。プローブ E と `test_finding_in_prose_is_not_an_allowed_finding` で本文F99を拒否。

### QA-0006-F03

Result: `fixed-and-verified`

Evidence: `launcher` に `--case-dir` / `--cycle` / `--save`。`test_cli_save_wires_public_submission_path` 合格。保存先は allowlist パス。

Residual: save 時の再検証が case_dir 無し（F01残差と同一）。SKILL.md に `--save` 未記載（文書遅延・Low）。

### QA-0006-F04

Result: `fixed-and-verified`

Evidence: `write_submission` に allowlist 検査追加。`test_filesystem_write_allowlist_rejects_reviewer_paths` 合格。

### QA-0006-F05

Result: `fixed-and-verified`

Evidence: `test_file_uri_evidence_is_rejected` 合格。手動でも file:// 拒否を確認済み（Cycle1レビュー時）。

### QA-0006-F06

Result: `deferred`（Author disposition受理。技術解消ではない）

Evidence: Author が共有コア同一値契約を理由に deferred。本Change範囲外として residual `evidence-gap` を維持。`fixed-and-verified` にはしない。

## Cycle outcome

- F02–F05: `fixed-and-verified`
- F01: `partially-fixed` → Cycle 2 の Author 対応が必須
- F06: open + deferred（共有基盤Change待ち）
- Next: `author-response`（Cycle 2）主対象 F01
- ケースはクローズしない
