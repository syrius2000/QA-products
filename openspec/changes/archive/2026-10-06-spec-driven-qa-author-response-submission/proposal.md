## Why

ReviewerからhandoffされたFindingに対し、Authorが役割を逸脱せず、回答・修正提出・Evidenceを再現可能な形式で返す公開契約が必要である。既存のReviewer側ライフサイクルと共有Contract v1.2を再利用し、正本の自己変更や自己クローズを防ぎながらAuthor工程を独立して実装・検証する。

## What Changes

- handoff.mdを読み取り、対象Findingごとの回答を作成するAuthor機能を提供する
- `accepted`、`fix-submitted`、`rejected-with-evidence`、`deferred`、`risk-accepted`等のDispositionを検証する
- `submission_id`、基準revision、digest、Evidence、変更ファイルを含む提出記録を作成する
- Reviewer正本、events、closureへのAuthor直接書込みを拒否する
- 未知Finding、stale handoff、欠落Evidence、Workspace外参照を拒否する
- Author回答の正常系・拒否系・依存欠落時の動作を標準ライブラリ中心のテストで確認する

## Capabilities

### New Capabilities

- `spec-driven-qa-author-response-submission`: Reviewer handoffを受けたAuthor回答と修正提出を扱う機能

### Modified Capabilities

- `spec-driven-qa`: Author提出のEvidence整合性、Reviewer正本との責務境界、submissionの検証要件を追加する

## Impact

- `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/`の共有契約・digest・権限境界を参照する
- Author用のSkill入口、共有コアまたはCLIアダプタ、Validator、テスト、fixtureを追加する
- Reviewer正本のスキーマ、既存case履歴、外部Skill配置先は変更しない
- 新規依存パッケージは追加せず、可能な限りPython標準ライブラリで動作させる
