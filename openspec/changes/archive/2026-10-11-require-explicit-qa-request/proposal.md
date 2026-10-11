# 提案

## 背景・理由

QA関連Skillの説明が会話内容に広く一致すると、QAの相談、結果の共有、OpenSpec作業だけでもSkillが選ばれる可能性がある。QA関連Skillは、ユーザーが実行を明示的に依頼した場合だけ選ばれる共通境界を持つ必要がある。

## 変更内容

- 管理対象の4つのQA Skill（`quality-qa`、`quality-review`、`quality-response`、`blind-qa-cycle`）のdescriptionに、明示的な実行依頼を起動条件として記載する。
- QAの話題を含むだけの質問・状況説明・結果共有、一般的なコードレビュー、QA Skillの説明依頼、OpenSpecのverify/apply依頼は起動条件にならないことを明記する。
- 各Skill固有のQuality Loop案件、Reviewer／Implementer Role、独立QAサイクルの条件は維持する。
- 各Skillの評価例に明示依頼の正例と、誤発火を避ける負例を追加する。

## 対象仕様

### 新規capability

なし。

### 変更するcapability

- `quality-loop-skill-deployment`: 管理対象QA Skill共通の明示依頼条件と非発火条件を追加する。

## 影響範囲

対象は`quality-loop/skills/`にある4つのQA Skill定義と各Skillの評価例、および評価例を確認する既存テストである。Quality Loop runtime、CLI、保存データ、Role遷移、QA案件正本、グローバルSkill配置は変更対象に含めない。
