# Reviewer 公開機能ID対応表

created: 2026-08-26
update: 2026-08-26 11:19 (JST)
対象Change: `spec-driven-qa-reviewer-case-lifecycle`
対象ロール: Reviewer

## 公開操作・機能ID対応一覧

| 機能ID / CLI操作 | 共有 operation | action | 主な入力引数 | 終了コード（観測） | JSON必須フィールド（観測） | 主な副作用 | 状態 |
|---|---|---|---|---|---|---|---|
| `REV-INIT-01` | `review` | `init` | `case_id`, `target`, `purpose`, `profile`, `qa_root` | 0 成功 / launcher欠落時 2 | `status`, `case_id`, `action`, `case_dir` | ケースDIR初期化 | 実装・CLI/pytest検証済み |
| `REV-REVIEW-01` | `review` | `review` | `case_id`, `findings`, `cycle` | lifecycle経路で成功/ValueError | `status`, `case_id`, `action`, `findings_count` | findings / cycle / traceability / events | 実装・pytest検証済み |
| `REV-HANDOFF-01` | `handoff` | `handoff` | `case_id`, `cycle`, `case_revision` | 同上 | `status`, `case_id`, `action`, `digest`, `open_findings` | `handoff.md` 生成 | 実装・pytest検証済み |
| `REV-VERIFY-01` | `verify` | `verify` | `case_id`, `submission`, `cycle` | 成功 / 契約違反で ValueError | `status`, `case_id`, `action`, `outcome` | verification cycle / findings status | 実装・pytest検証済み（残余あり※） |
| `REV-CLOSE-01` | `close` | `close` | `case_id`, `terminal_status`, `rationale` | 成功 / 不変条件違反で ValueError | `status`, `case_id`, `action`, `terminal_status` | review terminal / closure event | 実装・pytest検証済み |

※ VERIFY: stale digest 拒否・相対 Evidence パス実在・fix 提出の `modified_files` 必須は hardening 済み。**Workspace 境界（絶対パス/`../`/symlink）は QA-0005-F01 修正提出・verification 待ち。C3 全体消化とは書かない。**

## 欠落評価

- 本Changeスコープ内の Reviewer ライフサイクル公開機能ID欠落: **0件**（台帳上）
- 旧43機能全体・legacy 3版比較: **後続 Change / out-of-scope**
- shared_core アーカイブ完全一致: **evidence-gap**（CLI配線のため意図的改変。schemas は一致）

## Bundle digest（再測 2026-08-26）

| 対象 | digest (sha256) | 備考 |
|---|---|---|
| archive shared_core | `82380f7b8ae672fdd0340fc64585c323b467142bef91e5c494abac49152f75d4` | compact 基盤 |
| current shared_core | `80e492a7c92722d4b61ffa62b7531a11bd1f6f3b85ef17653a44943558817c52` | 不一致=意図的 |
| schemas (両側) | `f95acb52e62f33aaf831282725dafdf71d629d60eeaf62cc41ed613c4ac84d64` | 一致 |
