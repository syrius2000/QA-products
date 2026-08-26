# spec-driven-qa 移行ロードマップ & 引き継ぎメモ

- **作成日時**: 2026-08-26 07:35 (JST)
- **ステータス**: Active
- **対象**: `spec-driven-qa` スキル群の完全互換化と本番配備

---

## 1. 概要と背景

`compact-spec-driven-qa-skills` を共有基盤・検証基盤Changeとして一区切りにし、**未完了6タスクを後続Changeへ引き継ぐ警告付きアーカイブ** を実施した。

- **アーカイブ先**: [openspec/changes/archive/2026-08-26-compact-spec-driven-qa-skills/](../../openspec/changes/archive/2026-08-26-compact-spec-driven-qa-skills/)
- **達成状況**: 34/40タスク完了（共有コア、Schema、Firewall、互換Adapter、差分eval、20 tests passed）
- **方針**: 能力維持を損なう黙った機能縮小を避け、未完了の機能実装・完全互換性検証・本番配備を独立したChangeへ分割して段階的に進める。

---

## 2. 引き継ぎ未完了タスク（計6件）

| タスクID | タスク内容 | 引き継ぎ先Change |
| :--- | :--- | :--- |
| **7.3** | 機能ID欠落、必須Schema・Template欠落、終了コード変更、JSON必須フィールド欠落、未説明の拒否差分が0件であることを確認する | **Phase 2: 完全互換性検証** |
| **8.1** | stagingからのdry-runで全差分、対象パス、backup対象、rollback対象を表示し、Manifest外のパスを変更しないことを確認する | **Phase 3: 本番配備** |
| **8.2** | backupから限定対象を復元するrollbackを実行し、復元後のSkill構成、Manifest、読み取り互換性を確認する | **Phase 3: 本番配備** |
| **8.3** | 実装結果、fixture/eval結果、サイズ測定、残余リスク、未検証項目、配備差分をChange Evidenceへ記録する | **Phase 3: 本番配備** |
| **8.4** | Contract v1.2候補の未完了検証を受入済みと誤記せず、圧縮Changeの技術判定とOwnerのリスク判断を分離して記録する | **Phase 3: 本番配備** |
| **8.5** | すべての仕様・差分QA・rollbackゲートが合格した後、明示承認を取得するまで外部配置、旧版削除、commit、pushを実行しないことを確認する | **Phase 3: 本番配備** |

---

## 3. 後続Change ロードマップ

```text
[完了] 2026-08-26-compact-spec-driven-qa-skills (共有基盤・Firewall・Schema)
       │
       ├── 【Phase 1】 機能実装（必要に応じて分割）
       │       ├── spec-driven-qa-reviewer-lifecycle (ケース作成・独立レビュー・handoff・close等)
       │       └── spec-driven-qa-author-submission (Author Response・Disposition・提出保存等)
       │
       ├── 【Phase 2】 完全互換性検証
       │       └── spec-driven-qa-capability-parity (旧43機能IDの完全網羅・差分ゼロ証明)
       │
       └── 【Phase 3】 本番配備と安全ゲート
               └── spec-driven-qa-deployment-and-release (dry-run・backup・rollback・明示承認)
```

---

## 4. 各Phaseのスコープと完了条件

### Phase 1: コア機能実装（Reviewer / Author）
- **目的**: 共有基盤の上で、ReviewerおよびAuthorの全公開機能を実装する。
- **主な実装内容**:
  - **Reviewer**: ケース作成、目的・正本仕様登録、独立レビュー記録、Finding生成、handoff生成、cycle制限、イベント追記、close処理。
  - **Author**: handoff読み取り、Disposition（`accepted`, `fix-submitted`, `rejected-with-evidence`等）、submission保存、base revision検証。
- **完了条件**: 各役割の単体・統合テスト合格、権限分離（Authorからの正本直接変更拒否）の維持。

### Phase 2: 完全互換性検証（Parity Verification）
- **目的**: 旧Skill（130ファイル・公開43機能エントリ）との完全機能同等性を証明する（Task 7.3の達成）。
- **主な作業内容**:
  - 旧機能ID・引数・終了コード・JSON出力フィールド・拒否条件の全件照合。
  - 差分レポート作成、未説明の非互換・欠落0件の確認。
- **完了条件**: 43機能エントリの互換性テスト全件パス、機能欠落ゼロの証明。

### Phase 3: 本番配備と安全ゲート（Deployment & Release）
- **目的**: グローバルSkill配置先への安全な配備とロールバック体制の確立（Task 8.1〜8.5の達成）。
- **主な作業内容**:
  - `dry-run` による全差分・対象パス・Manifest外変更なしの確認。
  - `backup` からの限定復元（`rollback`）テスト。
  - Evidence記録（サイズ・残余リスク・未検証項目）。
  - 明示承認（Approval Gate）の取得確認。
- **安全不変条件**: 明示承認なしに外部配置・旧版削除・commit・pushを行わない。

---

## 5. 関連ファイル・参照リンク

- **アーカイブ済みChange**: [2026-08-26-compact-spec-driven-qa-skills](../../openspec/changes/archive/2026-08-26-compact-spec-driven-qa-skills/)
- **Change分割計画書**: [implementation_plan_007_0826.md](implementation_plan_007_0826.md)
- **アクティブChange**: [improve-spec-driven-qa-contract-v1-2](../../openspec/changes/improve-spec-driven-qa-contract-v1-2/)
