# 完了済みArtifact整理統合アーカイブ要約（004）

created: 2026-09-06 15:34 (JST)
update: 2026-09-06 15:34 (JST)
author: Codex (GPT-5)

対象期間: 2026-08-24 〜 2026-09-06（JST）

## 1. 位置付け

本書は、`docs/Artifacts/` に残っていた完了済みの計画書、実装報告、QA記録、同期記録、移行資料を、現行の利用導線と分離して保存するための統合要約である。

既存の `archived_summary_001_0825.md`、`archived_summary_002_0828.md`、`archived_summary_003_0831.md` は既存参照を保持するため改名・再採番していない。本書を004として追加し、アーカイブサマリーの採番を001から連続させた。

## 2. アーカイブ対象

次の完了済みArtifactを本書へ統合した。個別ファイルは `docs/Artifacts/` から整理し、詳細な旧内容はGit履歴で追跡できる状態を維持する。

### 2.1 Quality Loop資料整理・配布

- `implementation_plan_017_0831.md`: Quality Loop資料アーカイブ、README整合化、QA結果と実装履歴の分離
- `implementation_plan_018_0831.md`: リポジトリ文書整理、公開Git履歴とArchiveの境界、リンク保護
- `implementation_plan_019_0831.md`: Quality Loop Skillの自己完結配布、runtime同梱、配置検証
- `implementation_plan_020_0901.md`: 開発正本と利用成果物の分離、同期dry-run、backup、rollback方針
- `implementation_report_001_0901.md`: Skill自己完結配布の実装結果
- `implementation_report_002_0901.md`: QA-products配布・開発分離整理の実装結果
- `implementation_report_003_0905.md`: `review-standalone`単発QA入口の正本統合
- `skill_deployment_evidence_001_0901.md`: 配布対象runtime、SHA-256、隔離実行のEvidence
- `skill_deployment_execution_001_0901.md`: `quality-review`と`quality-response`の配置実施記録
- `quality_loop_sync_001_0901.md`: 初回同期結果
- `quality_loop_sync_002_0905.md`: 更新同期結果
- `quality_loop_sync_003_0905.md`: 同期差分なしの確認結果

### 2.2 OpenSpec Changeと独立QA

- `implementation_plan_021_0906.md`: Capability Parity残件の実装計画
- `implementation_report_004_0906.md`: Candidate Evidence拒否、Agent/Run集計、Parity検証の実装報告
- `implementation_plan_022_0906.md`: Author Response提出Change独立QA計画
- `implementation_report_005_0906.md`: Author自己クローズ、未知Finding、digest、Evidence境界の独立QA報告

Parity Changeは独立QAと人間裁定を経て `openspec/changes/archive/2026-09-06-spec-driven-qa-capability-parity-and-legacy-compat/` へ移動した。Author Response提出Changeは19/19タスクと独立QAを完了したが、現在の `implementation_plan_023_0906.md` によるエラー分類の厳密化が後続作業として残っている。

### 2.3 参考・移行・整理候補

- `archive_reorganization_candidates_001_0901.md`: Archive分類と削除禁止境界の候補一覧
- `roadmap_spec_driven_qa_migration_0826.md`: 旧spec-driven-qaから現行Quality Loopへの移行ロードマップ
- `qms_quality_reference_001_0827.md`: QMS思想、Evidence、比例性、Owner責任の参照資料
- `qa_review_modern_iot_data_pipeline_001_0824.md`: 別プロジェクトの実機QAレビュー記録

これらは現行Quality Loopの正本や実装許可ではなく、作成時点の履歴・参考資料として扱う。

## 3. 検証済みの到達点

- Quality Loopは `quality-loop/` を開発正本とし、`quality-review` と `quality-response` はruntime同梱・標準ライブラリ中心で単独配置できる構成になった。
- `review-standalone` は明示対象からcaseとhandoffをbootstrapする入口として追加され、対象成果物を変更せず、正式Reviewer工程へ引き渡す設計になった。
- Author Response提出はFinding単位のDisposition、revision、semantic/content digest、Evidence、`modified_files`、Write Allowlistを検証する。
- Author 27件、Reviewer 40件の回帰テスト、およびAuthor Changeの独立入力10/10ケースが合格している。
- 実測できない外部Agent、外部配置後動作、LLM性能は `unverified` または `evidence-gap` として扱い、完了扱いにしていない。

## 4. 現行導線と未完了範囲

- 現在進行中の計画は `docs/Artifacts/implementation_plan_023_0906.md` のみであり、Artifactから削除していない。
- 同計画はstale digestのエラー分類を `blocked: inconsistent-qa-state` に合わせる修正を対象とする。
- 外部配置、旧版削除、アーカイブ済みChangeの再利用、commit、pushは本書では承認しない。
- 現行仕様・操作手順は `quality-loop/`、履歴は本書と既存の001〜003、最終QA判定は `qa_acceptance_summary_001_0831.md` を参照する。

## 5. Git履歴と復旧境界

今回の整理では既存commitの履歴を書き換えない。個別Artifactの作業ツリー上の整理後も、過去内容は既存Git履歴から復元可能であり、現行Artifactにはアクティブな計画だけを残す。
