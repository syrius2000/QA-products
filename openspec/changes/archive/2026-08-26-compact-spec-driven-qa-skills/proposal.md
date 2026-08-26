# spec-driven-qa 2 Skillコンパクト化提案

## なぜ必要か

`spec-driven-qa-review`と`spec-driven-qa-author-response`は、厳格なQA契約、安全境界、証拠評価、状態遷移を備えている。一方で、スクリプト、参照文書、スキーマ、テンプレート、サンプルが細かく分散し、現行集計では合計130ファイル・5,287行となっているため、エージェントの常駐コンテキスト、保守負担、Skill間の重複を圧縮する。

先行Changeである[`improve-spec-driven-qa-contract-v1-2`](../improve-spec-driven-qa-contract-v1-2/)は、設計・実装候補を含むが、旧版比較、dry-run・rollback、残余リスク記録が未完了である。本Changeではそれを受入済みの正本とは扱わず、「未検証の基準候補」として固定し、圧縮版との比較検証を可能にする。

## 変更内容

- ReviewerとAuthorの役割名・入口を維持し、共有コアと2つの薄いSkill入口へ再構成する。
- digest、契約検証、状態遷移、Evidence、秘密情報検出、リンク検証などの共通処理を共有コアへ集約する。
- Reviewer専用の独立レビュー・handoff・検証・クローズと、Author専用のresponse・提出保存・実行ポリシーを役割境界付きで保持する。
- 現行の機能ID、引数、終了コード、出力形式、拒否条件、副作用を機能台帳として固定する。
- 旧版およびContract v1.2候補のgolden fixture、negative fixture、cross-skill fixtureを作成し、圧縮前後の差分検証を行う。
- `SKILL.md`を役割別の常駐行動規則に整理し、詳細な分類・証拠・状態遷移・安全規則を重複のない仕様文書へ集約する。
- JSON Schema、テンプレート、サンプル、MANIFEST、README、INSTALL、evalの正本と派生物を整理する。
- 旧CLI入口、終了コード、JSON出力、契約フィールドを互換層で維持し、置換前のrollback可能性を確保する。
- 合計行数1,760行以下を第一目標とする。ただし、テスト、必須仕様、最小完全サンプル、安全境界を削って達成しない。
- グローバルSkillへの配置、旧ファイル削除、commit、pushは本Changeの検証完了と別途の明示承認後に行う。

## Capability

### 新規Capability

- `compact-spec-driven-qa-skills`: 共有コアと役割別Skill入口、互換性、機能台帳、差分fixture、サイズ予算、圧縮後の配布構成を定義する。

### 変更する既存Capability

なし。既存QA契約の意味を緩和する変更ではなく、既存契約を維持した実装・配布構成の変更として扱う。Contract v1.2の未検証部分は、別Changeの受入結果へ書き換えない。

## 影響範囲

- `/Users/myamaguchi/.gemini/config/skills/spec-driven-qa-review/`
- `/Users/myamaguchi/.gemini/config/skills/spec-driven-qa-author-response/`
- 本リポジトリのステージング用Skill Bundle、fixture、eval、Manifest、OpenSpec Artifact
- ReviewerとAuthorが利用するCLI入口、JSON出力、テンプレート、スキーマ、参照文書
- 既存QAケースの読み取り互換性と、handoff・Author提出・Reviewer統合の検証フロー

外部Skill配置先への直接変更は、ステージング版の差分QA、役割逸脱のnegative test、rollback確認、残余リスク記録、明示承認が完了するまで行わない。
