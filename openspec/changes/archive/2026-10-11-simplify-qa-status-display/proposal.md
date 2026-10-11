# QA状態表示の日本語既定化と工程集約

## Why

4つのQAスキルは、状態コードだけでは現在の工程、次の担当、必要な操作、停止理由を一貫して把握できず、機械向けコードと人向け説明も混在している。内部状態・承認条件・QA判定を維持したまま、日本語を既定とする共通の5工程表示と明示的な英語選択を定義する。

## What Changes

- `quality-qa`、`quality-review`、`quality-response`、`blind-qa-cycle`の人向け状況説明に、5工程、詳細、次担当、次操作、該当時の停止理由と再開条件を導入する。
- 表示言語は未指定時に日本語とし、`lang=ja`／`lang=en`または対応CLIの`--lang ja`／`--lang en`で選択できるようにする。英語選択時は既存コード・表示語彙を保つ。
- 進行状態とQA判定・評価勧告を分離し、判定結果には評価対象版とサイクルを関連付ける。結果なし、過去の結果、修正後の未評価を区別する。
- 状態・停止条件から5工程、担当、操作を決定する優先順位を仕様化し、未知状態を推測で正常工程や終了へ割り当てない。
- JSON、保存データ、状態遷移、Role制約、承認条件、QA判定の機械契約を維持する。

## Capabilities

### New Capabilities

- `qa-status-display`: 4つのQAスキルに共通する人向け状態・判定の言語選択、5工程への表示対応、結果の対象版・サイクル表示を定義する。

### Modified Capabilities

なし。既存の統合QAワークフローが持つ日本語での次工程案内を維持し、その詳細な表示規則を新Capabilityで定義する。

## Impact

- 対象Skill: `quality-loop/skills/quality-qa`、`quality-review`、`quality-response`、`blind-qa-cycle`。
- 正本コード: `quality-loop/qa_workflow/`、`quality-loop/quality_loop/`。各Skillの`runtime/`複製も同期対象とする。
- 関連参照文書、CLIの人向け出力、再開用Markdown、`quality-loop/tests/`を更新対象とする。
- 依存関係や保存形式の移行は追加しない。既存のOpenSpec要件、CLI JSON契約、案件データ、状態遷移、判定ロジックへの影響は許容しない。
