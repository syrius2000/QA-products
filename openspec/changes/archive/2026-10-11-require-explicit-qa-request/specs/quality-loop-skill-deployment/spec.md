# Spec Delta

## ADDED Requirements

### Requirement: 明示的なユーザー依頼をQA Skill起動条件とする

管理対象の4つのQA Skillは、ユーザーの現在のメッセージが、そのSkillの説明に定めるQA操作の実行を明示的に求める場合に限り発火候補とならなければならない（MUST）。QAの話題・成果物・Skill名への言及、相談・説明依頼、結果の報告だけから実行依頼を推測してはならない（MUST NOT）。各descriptionは適用範囲、明示依頼の例、非発火の例を示さなければならない（MUST）。この条件は各Skill固有の案件、Role、操作条件を緩和しない。

#### Scenario: QA操作を明示的に依頼する
- **WHEN** ユーザーが対象を示し、QA、独立レビュー、再QA、またはQA状況確認の実行を依頼する
- **THEN** 該当Skillの固有条件も満たす場合に限り、そのSkillが発火候補となる

#### Scenario: QA成果物または結果を共有する
- **WHEN** ユーザーがQA結果やQA関連文書を提示するだけで、確認・対応・再QAを依頼しない
- **THEN** QA Skillは発火候補にならない

#### Scenario: QAに関する説明や相談を求める
- **WHEN** ユーザーがQAの仕組み・進め方の説明や相談を求め、QA操作の実行を依頼しない
- **THEN** QA Skillは発火候補にならない

#### Scenario: 別用途の依頼にQA用語が含まれる
- **WHEN** ユーザーが一般的なコードレビュー、OpenSpec verify/apply、またはQA Skillの説明だけを依頼する
- **THEN** QA Skillはその依頼だけを理由に発火候補にならない

#### Scenario: 明示依頼がSkill固有条件を満たさない
- **WHEN** QA操作は明示依頼されているが、案件・Role・操作など該当Skill固有の条件を満たさない
- **THEN** 明示依頼条件だけでそのSkillを発火させず、既存の適用条件を保つ
