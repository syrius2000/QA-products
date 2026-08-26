# spec-driven-qa-author-response-submission

Reviewerが公開した`handoff.md`を読み、AuthorとしてFinding別の回答または修正提出を作成する。

## 手順

1. `handoff.md`のcase ID、contract version、対象Finding、基準revision、semantic/content digestを読む。
2. FindingごとにDisposition、具体的な理由、Evidence、必要なら`modified_files`を記録する。
3. `submission_id`を付けた提出を検証し、stale digest、未知Finding、欠落Evidence、Workspace外参照を拒否する。
4. `cycles/cycle-NN-author-response.md`と`cycles/cycle-NN-submission.json`だけへ保存する。
5. `next_action: reviewer-verification`としてReviewerへ返却する。

AuthorはReviewerの`review.md`、`findings.yaml`、`handoff.md`、`events.jsonl`、closureを変更しない。`closed`や`fixed-and-verified`を自己設定しない。技術的に確認できない事項は`unverified`または`evidence-gap`として記録する。
