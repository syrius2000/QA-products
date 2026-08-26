## MODIFIED Requirements

### Requirement: 公開handoff契約を提供する

QAケースは、Authorが次に実行できる工程、対象Finding、実装許可、基準revision、`contract_version`、`semantic_digest`、`content_digest`、要求Evidenceを含む公開handoffを提供しなければならない。handoffはReviewer正本から生成されなければならず、Authorが直接編集した内容を正本として扱ってはならない。`semantic_digest`は意思決定に影響する正規化済み構造から、`content_digest`は対象文書の内容から、それぞれ独立して決定的に算出しなければならない。これらの条件はMUST（必須）とする。

#### Scenario: Authorが有効なhandoffを受け取る

- **WHEN** handoffの契約version、対象Finding、許可範囲、基準revision、両digestが現行QA正本と一致する
- **THEN** Author Validatorは次の回答または許可された実装提出へ進める

#### Scenario: semantic digestが不一致になる

- **WHEN** handoffの意思決定フィールドとQA正本から再計算した`semantic_digest`が一致しない
- **THEN** Validatorは`blocked: inconsistent-qa-state`を返し、Authorの提出を受理しない

#### Scenario: 内容だけが変更される

- **WHEN** `content_digest`だけが不一致で`semantic_digest`は一致する
- **THEN** Validatorは内容変更として識別し、handoffの再生成と人間確認を要求し、意味変更として自動受理しない

#### Scenario: Reviewer検証がstale digestのhandoffを拒否する

- **WHEN** ReviewerがAuthor提出を検証する際、参照handoffの`semantic_digest`または`content_digest`が現行正本と一致しない
- **THEN** Reviewer検証は提出を拒否し、Findingを成功状態へ更新しない

#### Scenario: 旧形式の同値digestを受け取る

- **WHEN** 旧Contractが`semantic_digest`と`content_digest`に同じ値を持ち、両digestの独立検証が必要な処理へ渡される
- **THEN** Validatorは新Contractの有効なhandoffとして受理せず、互換性警告または移行要求を返し、旧履歴の自動書換えは行わない
