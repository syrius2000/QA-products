# spec-driven-qa 完全互換化のChange分割計画

created: 2026-08-26 02:00 (JST)
update: 2026-08-26 02:00 (JST)
author: Codex (GPT-5)

## 1. 目的

現在の`compact-spec-driven-qa-skills`を共有基盤Changeとして整理し、旧Skillの公開・実行機能を複数の後続OpenSpec Changeへ分割する。各Changeを独立QAできる単位にし、未実装機能を隠したまま本番配備しない。

## 2. 現状認識

- `compact-spec-driven-qa-skills`: 34/40タスク。共有コア、Schema、Firewall、互換Adapter、差分evalまで実装済み。
- 残タスクの中心は、43件の旧公開・実行エントリとの完全機能対応、全機能IDの欠落検証、dry-run・backup・rollbackである。
- 現在のBundleは完全な本番Skillではなく、完全互換化の基盤である。
- 外部Skill配置先への書込み、旧版削除、commit、pushは実施しない。

## 3. 推奨するChange分割

```text
compact-spec-driven-qa-skills
        │
        ├── reviewer-case-lifecycle
        │       └── capability-parity-and-legacy-compat
        │
        ├── author-response-submission
        │       └── capability-parity-and-legacy-compat
        │
        └── deployment-dry-run-rollback
                ▲
                └── capability-parity-and-legacy-compat
```

### Change A: `spec-driven-qa-reviewer-case-lifecycle`

Reviewer側の完全機能を実装する。

- ケース作成、目的・対象・正本仕様の登録
- 独立レビュー記録、Finding、traceabilityの生成
- handoff生成、origin・digest・revisionの記録
- cycle制限、イベント追記、Reviewer検証、close
- Reviewer専用CLIの引数・終了コード・JSON互換
- Reviewer旧スクリプトとの機能ID対応表

完了条件は、Reviewer固有の公開機能IDについて欠落0件、正常系・拒否系・自己クローズ防止・未知major停止の独立QA合格とする。

### Change B: `spec-driven-qa-author-response-submission`

Author側の完全機能を実装する。

- handoff読み取りと公開契約の検証
- Finding別Author Response
- `accepted`、`fix-submitted`、`rejected-with-evidence`等のDisposition
- submission保存、base revision、semantic/content digest、Evidence整合性
- 実装許可範囲とReviewerへの返却条件
- Author旧スクリプトとの機能ID対応表

Change Aと並行実装できるが、共有Schemaと共有コアのインターフェースを固定した後に開始する。Reviewer正本・イベント・closureへの直接書込み拒否を必須ゲートとする。

### Change C: `spec-driven-qa-capability-parity-and-legacy-compat`

Change A/Bの機能を旧版と比較し、完全互換性を証明する。

- 現行130ファイルから抽出した43公開・実行機能IDの対応表
- 旧版、Contract v1.2候補、圧縮版の3版比較
- 旧CLI引数、終了コード、JSON必須フィールド、副作用の比較
- golden、negative、cross-skill、legacy、size fixtureの一括実行
- 未実装、意図的非互換、診断文差分の分離レポート
- `valid: true`だけでなく、実行結果と機能ID対応Evidenceを確認

Change A/Bの完了後に開始する。ここで未対応機能が1件でも残る場合は、本番配備へ進めない。

### Change D: `spec-driven-qa-deployment-dry-run-rollback`

完全互換性が確認されたBundleを、外部Skill環境へ安全に配置するための別Changeとする。

- 対象パスの再確認
- 既存Skillのファイル一覧・SHA-256バックアップ
- Manifest限定のdry-runと全差分表示
- 一時配置、Launcher、Manifest、権限Firewallの配置後検証
- 対象限定rollbackと復元後検証
- 旧版削除は最後の別承認操作とし、初回配備では実行しない

Change Cの独立QA、ユーザーの明示承認、バックアップ検証が完了するまで実装・実行しない。

## 4. 依存関係と並行性

| Change | 依存 | 並行実装 |
|---|---|---|
| 基盤整理 | 現在のcompact Change | 先にScope確定 |
| Reviewer lifecycle | 基盤 | Authorと並行可能 |
| Author response/submission | 基盤 | Reviewerと並行可能 |
| Capability parity/legacy | Reviewer・Author | 両方完了後 |
| Deployment/rollback | Capability parity | 最後のみ |

ReviewerとAuthorを別Changeに分ける理由は、役割境界、テスト責務、QA担当を独立させるためである。1つに統合すると、Authorの提出権限とReviewerの正本更新権限が同じChangeへ混ざり、Findingの責任追跡が難しくなる。

## 5. 現在のChangeの扱い

次の順序で、現在のChangeのScopeを更新する。

1. `proposal.md`を「完全互換実装」から「共有基盤と検証基盤」へ更新する。
2. `spec.md`に、Reviewer／Authorの業務機能本体は後続Changeで実装する依存境界を追記する。
3. `design.md`に4つの後続Changeと依存関係を記録する。
4. `tasks.md`の7.3、8.1〜8.5を、後続Changeへの引き継ぎEvidence作成と基盤側の完了条件へ再分割する。
5. Scope変更をユーザーが再承認した後、現在のChangeを基盤ChangeとしてQAし、後続ChangeをOpenSpec CLIで作成する。

Scope変更前に現在のtasksを完了扱いにしたり、未実装43機能を対象外扱いにしたりしない。

## 6. 推奨する作成順

1. 現在のChangeのScope更新と再承認
2. `spec-driven-qa-reviewer-case-lifecycle`作成
3. `spec-driven-qa-author-response-submission`作成
4. A/Bの独立QA
5. `spec-driven-qa-capability-parity-and-legacy-compat`作成
6. 全機能ID・3版比較・実行EvidenceのQA
7. `spec-driven-qa-deployment-dry-run-rollback`作成
8. 配備計画の明示承認後にdry-runのみ実施

## 7. 完了判定

完全互換化の完了は、次の全条件を満たした場合だけとする。

- 43公開・実行機能IDの対応Evidenceがある
- Reviewer／Authorの役割逸脱が0件
- 旧CLIの必須引数・終了コード・JSON必須フィールドの未説明差分が0件
- negative、legacy、cross-skill、rollbackの検証が完了
- Contract v1.2候補の未検証状態を受入済みと誤記していない
- 外部配置前に独立QAがacceptedとなっている
- ユーザーの明示承認なしに外部配置・旧版削除・commit・pushを行っていない
