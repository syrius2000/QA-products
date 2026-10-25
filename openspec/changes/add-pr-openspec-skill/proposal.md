# Proposal

## Why

OpenSpecで進めたchangeをGitHub上の外部Reviewerに監査してもらう場面がある。GitHub側のReviewerはOpenSpec CLIやローカルSkillを使えないため、仕様・実装・テスト・未検証事項を、リポジトリ内のMarkdownだけで監査できる形にする必要がある。既存の`spec-review-loop`は「実装と独立レビューを反復する」ためのもので、PR公開時の監査依頼書と回答の照合を担わない。

## What Changes

- 新Skill `pr-openspec` を `quality-loop/skills/pr-openspec/` に追加する。
- 次を行う: 開発前の状態記録の再利用、Git baselineの確定、OpenSpec資料の網羅確認、要求別対応表を含む監査依頼書の作成、監査対象の実装head Hと公開head Pの対応づけ。
- Reviewer回答を検証する決定的checker `scripts/validate_review_reply.py` を追加する。回答JSONのスキーマ、期待値manifestとの照合、判定値の列挙、終了コード（PASS=0、FAIL=1、INCONCLUSIVE=2、使用法の誤り=3）を定める。
- 起動評価`evals/evals.json`（4ケース）と、checkerの試験`tests/`（最低ケース一覧に対応するフィクスチャを含む）を追加する。
- 既存の`spec-review-loop` CLIは変更しない。`spec-review-loop`の記録（`state.json`、`Spec-Review-Round`、SHA-256）は参照のみ行う。

## Non-goals

- 実装・PR作成・push・レビュー依頼の送信は、利用者の明示的な許可なしに行わない。
- merge、履歴の書き換え、外部Skillディレクトリへの配備は対象外。
- GitHubの現在状態を取得する機能はcheckerに持たせない（Skillが取得して期待値manifestとして渡す）。
- Reviewerの指摘の真偽や、未検証事項の実施を機械的に保証しない。
- 自動監視、自動再依頼、Botへの自動注入は初版に含めない。

## Impact

- 新規: `openspec/changes/add-pr-openspec-skill/`（本change）、`quality-loop/skills/pr-openspec/`（実装時に作成）。
- 既存の`spec-review-loop`、`quality-qa`、`blind-qa-cycle`、`quality-review`、`quality-response`は変更しない。
- 計画の詳細と経緯は `design.md` を参照（計画書 v3、SHA-256 `efa19c2e…`）。
