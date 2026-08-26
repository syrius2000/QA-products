## MODIFIED Requirements

### Requirement: 公開handoff契約を提供する

QAケースは、Authorが次に実行できる工程、対象Finding、実装許可、基準revision、`contract_version`、`semantic_digest`、`content_digest`、要求Evidenceを含む公開handoffを提供しなければならない。handoffはReviewer正本から生成されなければならず、Authorが直接編集した内容を正本として扱ってはならない。Author提出のReviewer検証経路でも、入力handoffのdigest鮮度は正本再計算と一致しなければならない。これらの条件はMUST（必須）とする。

#### Scenario: Authorが有効なhandoffを受け取る

- **WHEN** handoffの契約version、対象Finding、許可範囲、基準revision、digestが現行QA正本と一致する
- **THEN** Author Validatorは次の回答または許可された実装提出へ進める

#### Scenario: semantic digestが不一致になる

- **WHEN** handoffの意思決定フィールドとQA正本から再計算した`semantic_digest`が一致しない
- **THEN** Validatorは`blocked: inconsistent-qa-state`を返し、Authorの提出を受理しない

#### Scenario: 内容だけが変更される

- **WHEN** `content_digest`だけが不一致で`semantic_digest`は一致する
- **THEN** Validatorはhandoffの再生成と人間確認を要求し、意味変更として自動受理しない

#### Scenario: Reviewer検証がstale digestのhandoffを拒否する

- **WHEN** ReviewerがAuthor提出を検証する際、参照handoffの`semantic_digest`または`content_digest`が現行正本と一致しない
- **THEN** Reviewer検証は提出を拒否し、Findingを成功状態へ更新しない

### Requirement: AuthorとReviewerの責務を分離する

Authorはhandoffから参照される実装・テスト・Evidenceを読み取って回答できるが、Reviewer正本のFinding severity、Finding状態、verification、Owner裁定、events、case closureを変更してはならない。Author提出物は新規`submission_id`の許可された提出先へ記録し、Reviewer側の統合処理だけが正本へ反映できる。Reviewerの受理判定は、宣言されたリポジトリ相対Evidenceパスと要求される変更ファイルの実在を含めて整合していなければならない。これらの責務分離はMUST（必須）とする。

#### Scenario: Authorが未知のFindingを提出する

- **WHEN** Author提出物のFinding IDがhandoffまたはQA正本に存在しない
- **THEN** Author Validatorは提出を拒否し、Reviewer正本を変更しない

#### Scenario: Authorが正本を変更しようとする

- **WHEN** AuthorがFinding、events、closureなどのReviewer所有記録を変更した提出を行う
- **THEN** 統合Validatorは書込み境界違反として拒否する

#### Scenario: Reviewerが提出物を受理する

- **WHEN** `submission_id`、内容ハッシュ、基準revision、対象Finding、Evidenceが正本と整合し、リポジトリ相対Evidenceパスおよび要求される`modified_files`が実在する
- **THEN** Reviewer側の統合処理だけが変更候補を正本へ反映できる

#### Scenario: Reviewerが欠落参照のある提出を拒否する

- **WHEN** Author提出のリポジトリ相対Evidenceパスまたは要求される`modified_files`のいずれかが実在しない
- **THEN** Reviewer検証は提出を拒否し、正本を変更しない

### Requirement: Evidenceと参照を安全に記録する

各Findingは要求Evidence、実際のEvidence、検証者、取得時点、検証結果を区別して記録しなければならない。取得不能なEvidenceは成功とみなさず、`unverified`または`evidence-gap`としなければならない。リポジトリ内参照は相対パス、外部参照は外部であることを明示し、秘密値はマスクまたは参照拒否しなければならない。リポジトリ相対パスとして提示されたEvidenceが対象ワークスペースに存在しない場合、成功Evidenceとして記録してはならない。これらのEvidence管理はMUST（必須）とする。

#### Scenario: 実行時Evidenceを取得できない

- **WHEN** 必須の実行環境または外部システムへアクセスできず、結果を再現できない
- **THEN** Validatorは成功判定を補完せず、`unverified`または`evidence-gap`を記録する

#### Scenario: リポジトリ内のEvidenceを参照する

- **WHEN** Evidenceが同一リポジトリ内のファイルを指す
- **THEN** 記録は相対パスを使用し、絶対パスや`file://`を正規の内部参照として受理しない

#### Scenario: 存在しないリポジトリ相対Evidenceを拒否する

- **WHEN** Evidence参照がリポジトリ相対パスとして解釈できるが対象ファイルが存在しない
- **THEN** ValidatorまたはReviewer検証は成功とみなさず、提出を拒否するか`evidence-gap`／同等の非成功として記録する

#### Scenario: 秘密値を含むEvidenceを提出する

- **WHEN** Evidenceにトークン、認証情報、またはマスク不能な秘密値が含まれる
- **THEN** Evidence本体をQA記録へ複製せず、参照を拒否して`evidence-gap`を記録する
