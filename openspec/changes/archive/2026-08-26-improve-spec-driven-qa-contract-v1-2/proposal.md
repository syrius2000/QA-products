# Spec-Driven QA Contract v1.2 改善提案

## なぜ必要か

現在のReviewer Skill、Author Response Skill、QMS v1.1.0は、それぞれ有用な機能を持つ一方、QA正本とAuthor提出物の責務境界、handoffの鮮度、状態遷移、権限、Evidenceの扱いが一つの検証可能な契約に統合されていない。これにより、偽Finding、古いhandoff、Authorによる正本変更、自己クローズ、Skill間の実行不整合が発生し得る。

`Codex.md`で合意した設計判断をContract v1.2として仕様化し、ステージング版の2 SkillをE2E評価できる状態にする。既存のグローバルSkillの置換や実装コードの変更は、このChangeの検証後に別途承認する。

## 変更内容

- Authorは公開契約である`handoff.md`と許可された実装・Evidenceを参照し、QA正本を更新しない契約へ変更する。
- Author提出物を`submission_id`単位の追記専用提出として扱い、Reviewer側の統合ValidatorだけがQA正本へ反映できるようにする。
- `semantic_digest`、`content_digest`、`case_revision`、`expected_semantic_digest`によるhandoff鮮度と同時更新検証を追加する。
- ケースの永続状態を`case_status`、`next_action`、`case_revision`へ簡約し、Finding固有状態をFinding内へカプセル化する。
- Reviewerの追加Plan Reviewを省略できる条件付きFast Pathを、リポジトリ規則とユーザー承認の範囲内に限定して定義する。
- Quality Intent、Evidence、cycle上限、`risk-accepted`、`evidence-gap`、`deferred`の扱いを明確化する。
- `contract_version`、構造化CLI JSON、旧Contract読み取り互換、未知major versionの安全停止を追加する。
- YAML正本を維持しつつ、digest入力は安定したJSONへ変換する契約を追加する。
- ReviewerとAuthorの共通モジュール衝突、Schema・Template・Validatorのenum不一致、配布cache混入を解消する。
- 固定fixtureによる契約・回帰・negative・cross-skill評価と、旧版比較の性能計測をBundleゲートにする。
- ステージング評価、dry-run、差分表示、バックアップ、明示承認を経た配備手順を定義する。

## 対象Capability

### 新規Capability

- `spec-driven-qa-contract`: ReviewerとAuthorが共有するQAケース、handoff、Finding、Evidence、状態遷移、権限、Validator、構造化CLIの契約。

### 変更する既存Capability

- なし。既存のOpenSpec Capabilityの要求を変更するものではなく、新しいQA契約Capabilityを追加する。

## 影響範囲

- `/Users/myamaguchi/.agents/skills/spec-driven-qa-review/`を基準とするReviewer Skillの契約・Validator・Renderer・Schema・Template・テスト。
- `/Users/myamaguchi/.agents/skills/spec-driven-qa-author-response/`を基準とするAuthor SkillのResponse Validator・提出形式・テスト。
- ステージング用Skill Bundle、固定fixture、`run_evals.py`、Manifest、配布検証。
- QAケースのhandoff、Finding、events、Evidence参照、Contract version。
- OpenSpec Bridgeは指定Changeのbaseline取り込みに対応するが、OpenSpecのtask完了や`valid: true`を実装Evidenceとは扱わない。
- 既存v1.0/v1.1 QAケースは読み取り互換を維持し、履歴を自動変換しない。
- グローバルSkill配置先への反映は対象外とし、Change完了後の明示承認付き配備工程へ分離する。
