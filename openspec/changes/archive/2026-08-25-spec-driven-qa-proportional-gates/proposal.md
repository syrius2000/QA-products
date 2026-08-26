# Why

現行の`spec-driven-qa-review`は、仕様・目的・脅威モデルに明記されていないセキュリティ要求まで高い重大度で扱う可能性があり、家庭内LAN・非安全系・非リアルタイムのIoTプロジェクトに対して過剰な是正を要求し得る。目的に直結するデータ品質と信頼性を優先し、運用上受容可能な残余リスクを明確に裁定できる比例的なQA契約へ改善する。

## What Changes

- レビュー開始時に配置範囲、重要度、リアルタイム性、許容データ損失、リソース制約、運用形態を確認する。
- Findingを`spec-required`、`purpose-critical`、`operational-hygiene`、`out-of-scope`に分類する。
- 仕様にないセキュリティ要求を、根拠なくCriticalまたはHighへ格上げしない。
- 技術判定と所有者によるリスク裁定を分離する。
- 家庭用・非安全系・非リアルタイム向けの比例的QAプロファイルを追加する。
- `unverified`と`failed`を明確に分離する。
- `risk-accepted`に所有者、理由、管理策、期限または見直しトリガーを要求する。

## Capabilities

### New Capabilities

- `proportional-qa-gates`: プロジェクト目的と運用リスクに応じてFindingの重大度・裁定・証拠要求を調整するQAゲート。

### Modified Capabilities

なし。既存のアプリケーション仕様の要件は変更せず、QAスキルのレビュー契約を更新する。

## Impact

- `spec-driven-qa-review`のSKILL.mdとQA原則・リスクプロファイル参照資料を変更する。
- QA記録のFindingに分類と技術判定・リスク裁定の項目を追加する可能性がある。
- 既存のQAケース履歴や対象プロジェクトのアプリケーションコードは変更しない。
- 実行時依存関係は追加しない。既存の標準ライブラリのみの実行制約を維持する。
