# stale digestエラー分類厳密化実施計画

created: 2026-09-06 15:25 (JST)
update: 2026-09-06 15:25 (JST)
author: Codex (GPT-5)

## 1. 目的

`spec-driven-qa-author-response-submission` のstale semantic/content digest拒否を、仕様が定める `blocked: inconsistent-qa-state` として機械的に識別できるようにする。既存の具体的な原因説明は保持し、利用者が安定した分類と詳細原因の両方を取得できる状態にする。

## 2. 対象範囲

- `stage/spec_driven_qa_author_response_submission/submission.py`
  - submission側のsemantic/content digest不一致
  - handoffと正本のsemantic/content digest不一致
  - handoff本文のcontent digest不一致
- `stage/spec_driven_qa_author_response_submission/launcher.py`
  - digest不整合時のJSON分類
- `stage/tests/test_submission.py`
  - `blocked: inconsistent-qa-state` のValidator結果
  - CLI結果の分類と終了コード
- `docs/ADR/QA/QA-0011.../review.md` およびEvidence
  - Warning解消結果の追記

## 3. 実施方式

1. 既存の詳細エラーを維持しつつ、digest不整合時に安定分類 `blocked: inconsistent-qa-state` を追加する。
2. CLI拒否JSONに分類を明示し、非digestエラーの既存分類は変更しない。
3. semantic digest不一致、content digest不一致、handoff本文不一致の正常な拒否と、通常の入力不備を分けてテストする。
4. キャッシュなしのAuthor全テスト、Reviewer回帰テスト、OpenSpec検証、`git diff --check`を実行する。

## 4. 完了条件

- 仕様記載の `blocked: inconsistent-qa-state` が該当するstale digest結果に含まれる。
- 詳細原因（semantic/content、handoff stale等）が失われない。
- digest以外の拒否分類・成功状態・書込み境界に回帰がない。
- AuthorとReviewerのテストが全件合格する。
- 外部配置、アーカイブ、pushは実施しない。

## 5. 承認境界

本計画の作成・読み取り調査・テスト設計は承認前に実施できる。コード、テスト、QA記録の変更は、ユーザーの明示承認後に限る。commitとpushは本計画の対象外とする。
