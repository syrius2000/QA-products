# QA-products 作業ロードマップ

このファイルは、複数のOpenSpec Changeを忘れずに進めるためのルートチェックリストである。実装前に対象Changeのstatusとtasksを確認し、完了条件を満たした項目だけを消し込む。

## 基本ルール

- 応答、Artifact、見出し、説明は日本語で記載する。
- リポジトリ内リンクは相対パスを使用する。
- 外部Skill配置、旧版削除、commit、pushは、対象Changeの完了・独立QA・明示承認が揃うまで実行しない。
- OpenSpecの`valid: true`は構造検証であり、実装・runtime evidence・独立QAの完了を意味しない。
- 未検証の機能は`unverified`または`evidence-gap`として残し、完了扱いにしない。
- 作業開始時と編集ラウンド終了時に、既存変更を保持した状態で差分と対象範囲を確認する。

## 全体ロードマップ

```text
契約v1.2検証 ───────┐
                    ├─ 共有基盤の再利用確認
Reviewer lifecycle ─┤
Author response ────┘
          ↓
機能ID完全互換・legacy比較
          ↓
配備dry-run・backup・rollback
          ↓
明示承認後の限定配備
```

## 1. 先行するContract v1.2 Change

対象: `openspec/changes/improve-spec-driven-qa-contract-v1-2/`

- [x] 設計・実装候補・既存QAの基盤を確認
- [ ] 6.3 旧版との同一prompt比較、誤実装開始・自己クローズ・未知Finding受理0件、評価指標を記録
- [ ] 6.4 staging dry-run、全差分、backup、rollbackを既存Skill無変更で確認
- [ ] 6.5 Evidence、評価結果、残余リスク、配備差分を記録し、明示承認なしの配備禁止を確認
- [ ] 独立QAでContract v1.2の技術判定を完了

完了条件: 未検証候補を受入済みと誤記せず、6.3〜6.5と独立QAのEvidenceが揃うこと。

## 2. アーカイブ済み共有基盤Change

対象: `openspec/changes/archive/2026-08-26-compact-spec-driven-qa-skills/`

- [x] 共有コア、Schema、Launcher、Firewall、legacy Adapter、差分evalを実装
- [x] 34/40タスクを完了
- [x] 未完了6タスクを保持した条件付きアーカイブを確認
- [x] 外部Skill配置先を変更していないことを確認

未完了項目は後続Changeへ引き継ぐ。アーカイブ済みChangeを完了済み本番Skillと扱わない。

## 3. Reviewer機能Change

対象: `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/`

- [x] ChangeディレクトリをOpenSpec CLIで作成
- [x] proposal.mdを作成
- [x] spec.mdでReviewerのケース作成、Finding、handoff、イベント、検証、closeを定義
- [x] design.mdで共有基盤との境界と正本書込み権限を定義
- [x] tasks.mdを作成
- [x] Reviewer機能IDを実装
- [x] Reviewer独立QAを実施
- [x] reviewer-verification-integrity-hardeningを実施・独立検証し、accepted-with-residual-riskでアーカイブ

完了条件: Reviewer固有の公開機能ID、正常系、拒否系、role firewall、履歴不変性が独立Evidenceで確認できること。

## 4. Author機能Change

予定名: `spec-driven-qa-author-response-submission`

- [x] Reviewer Changeの共有契約を確認
- [x] OpenSpec Changeを作成
- [ ] handoff読取、Finding別Response、Disposition、submission、Evidence整合性を定義
- [ ] Reviewer正本・events・closureへの直接書込み拒否を実装
- [x] Author機能IDを実装
- [ ] Author独立QAを実施

Reviewer Changeと並行可能だが、Schema・digest・revision契約を共有基盤から変更しない。

## 5. 完全互換・Legacy検証Change

予定名: `spec-driven-qa-capability-parity-and-legacy-compat`

- [ ] Reviewer／Author Changeの完了を確認
- [x] OpenSpec Changeを作成
- [x] 旧130ファイルから抽出した43公開・実行機能IDの対応表を作成
- [x] 旧版、Contract v1.2候補、圧縮版を同一fixtureで比較
- [x] 終了コード、JSON必須フィールド、状態、副作用、拒否差分を分離
- [ ] 未対応機能0件または明示された非互換理由を記録（1件の`missing-or-unverified`が残る）
- [x] 独立QAを実施
- [x] A（条件付き受入）を人間裁定として記録（QA-0008）

現在の残作業:

- [ ] Candidateの空Evidence受理（QA-0008-F01）を修正または意図的非互換として人間裁定する
- [ ] Agent／Run必須メタデータの未充足項目を追加取得するか、残余リスクとして裁定する
- [ ] 人間裁定完了後にのみ、後続の配備Changeへ進む

完了条件: 43機能IDの対応Evidence、golden・negative・cross-skill・legacy比較、未説明差分0件が揃うこと。

## 6. 配備・Rollback Change

予定名: `spec-driven-qa-deployment-dry-run-rollback`

- [ ] 完全互換Changeの独立QA acceptedを確認
- [ ] OpenSpec Changeを作成
- [ ] 対象外パスを含まないManifestを固定
- [ ] 既存Skillのファイル一覧とSHA-256をbackup
- [ ] dry-runで全差分、追加・変更・削除予定を表示
- [ ] 一時配置後のLauncher、Manifest、Firewall、互換性を検証
- [ ] 対象限定rollbackを実行し、復元後の構成を検証
- [ ] ユーザーの明示承認を取得
- [ ] 初回配備では旧版削除・commit・pushを実施しない

完了条件: backup、dry-run、配置後検証、rollback、明示承認の全Evidenceが揃うこと。

## Change管理手順

各作業開始時に次を実行する。

```bash
openspec list --json
openspec status --change "<change-name>" --json
openspec instructions apply --change "<change-name>" --json
```

各Changeの完了報告には、次を必ず含める。

- Change名とSchema
- `N/M tasks complete`
- 実行したテストと未検証項目
- 独立QAの状態
- 外部配置・旧版削除・commit・pushの実施有無
- 次に進めるChangeと依存関係

詳細計画: [implementation_plan_007_0826.md](docs/Artifacts/implementation_plan_007_0826.md)
