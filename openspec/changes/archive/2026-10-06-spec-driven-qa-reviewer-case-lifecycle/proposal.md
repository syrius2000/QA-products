## Why

共有基盤Change（`compact-spec-driven-qa-skills`）で整備された契約・Firewall・Schema基盤の上に、Reviewerの完全な業務ライフサイクル（ケース作成、独立レビュー記録、Finding/traceability管理、handoff生成、Reviewer検証、サイクル制御、close）を実装・検証し、能力維持と権限分離を両立するため。

## What Changes

- **ケース作成・初期化**: レビュー目的、対象ファイル、正本仕様（Spec/Plan/Tasks等）、リスクプロファイルを登録したQAケースの初期化機能を実装する。
- **独立レビューとFinding管理**: 独立レビュー結果の記録、Findingの分類・severity・traceabilityの正本管理機能を実装する。
- **handoff生成**: Authorへ引き渡す`handoff.md`の生成（origin, case revision, semantic/content digest, 要求Evidenceの出力）を実装する。
- **Reviewer検証と統合**: Author提出物（submission）の検証・整合性突合、Reviewer検証（verification）の記録、正本候補への反映を実装する。
- **サイクル制御とクローズ**: cycle制限（lite: 1, 標準: 2, strict: 3）の遵守、イベント追記、terminal result（`accepted`, `risk-accepted`, `evidence-gap`, `deferred`）のクローズ処理を実装する。
- **Reviewer CLI/API互換**: Reviewer専用CLIサブコマンドの引数・終了コード・JSON出力を旧機能と互換化する。

## Capabilities

### New Capabilities

- `spec-driven-qa-reviewer-case-lifecycle`: ReviewerによるQAケースのライフサイクル全体（ケース初期化、独立レビュー記録、Finding・traceability管理、handoff生成、Reviewer検証、サイクル制御、close判定）を定義する。

### Modified Capabilities

<!-- なし（新規Capabilityとして定義） -->

## Impact

- **対象コード**: `stage/spec_driven_qa_reviewer/` 配下のスクリプト、CLI Facade、Renderer、Validator。
- **共有基盤連携**: 共有コア（`shared_core`）の契約検証・Firewall・digest計算を利用し、正本（`review.md`）、イベント履歴、closureへの書込み権限をReviewerのみに限定。
- **依存性**: `compact-spec-driven-qa-skills` でアーカイブされた共有基盤およびContract v1.2 Schema仕様。
