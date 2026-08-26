# Spec-Driven QA Contract

## Purpose

ReviewerとAuthorが同じQAケースを安全に引き継ぎ、状態・権限・Evidence・鮮度を機械検証できる共有契約を提供する。Reviewer検証ではhandoff digest、リポジトリ相対Evidence、要求される変更ファイルの実在も確認する。

## Requirements

### Requirement: 公開handoff契約を提供する

QAケースは、Authorが次に実行できる工程、対象Finding、実装許可、基準revision、`contract_version`、`semantic_digest`、`content_digest`、要求Evidenceを含む公開handoffを提供しなければならない。handoffはReviewer正本から生成されなければならず、Authorが直接編集した内容を正本として扱ってはならない。`semantic_digest`は意思決定に影響する正規化済み構造から、`content_digest`は対象文書の内容から、それぞれ独立して決定的に算出しなければならない。これらの条件はMUST（必須）とする。

#### Scenario: Authorが有効なhandoffを受け取る

- **WHEN** handoffの契約version、対象Finding、許可範囲、基準revision、digestが現行QA正本と一致する
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

### Requirement: AuthorとReviewerの責務を分離する

Authorはhandoffから参照される実装・テスト・Evidenceを読み取って回答できるが、Reviewer正本のFinding severity、Finding状態、verification、Owner裁定、events、case closureを変更してはならない。Author提出物は新規`submission_id`の許可された提出先へ記録し、Reviewer側の統合処理だけが正本へ反映できる。Reviewerの受理判定は、宣言されたリポジトリ相対Evidenceパスと要求される`modified_files`の実在を含めて整合していなければならない。これらの責務分離はMUST（必須）とする。

#### Scenario: Authorが未知のFindingを提出する

- **WHEN** Author提出物のFinding IDがhandoffまたはQA正本に存在しない
- **THEN** Author Validatorは提出を拒否し、Reviewer正本を変更しない

#### Scenario: Authorが正本を変更しようとする

- **WHEN** AuthorがFinding、events、closureなどのReviewer所有記録を変更した提出を行う
- **THEN** 統合Validatorは書込み境界違反として拒否する

#### Scenario: Reviewerが欠落参照のある提出を拒否する

- **WHEN** Author提出のリポジトリ相対Evidenceパスまたは要求される`modified_files`のいずれかが実在しない
- **THEN** Reviewer検証は提出を拒否し、正本を変更しない

#### Scenario: Reviewerが提出物を受理する

- **WHEN** `submission_id`、内容ハッシュ、基準revision、対象Finding、Evidenceが正本と整合する
- **THEN** Reviewer側の統合処理だけが変更候補を正本へ反映できる

### Requirement: ケース状態とFinding状態を検証可能にする

ケース直下の永続状態は`case_status`、`next_action`、`case_revision`を持たなければならない。Finding固有の技術状態、Author回答、Owner裁定はFinding内に保持し、`workflow_phase`と`terminal_result`は状態遷移規則から導出しなければならない。ケース終了時は`terminal_result`を記録し、`closed`を技術的修正完了と同義にしてはならない。これらの状態管理はMUST（必須）とする。

#### Scenario: 不正な状態組合せが提出される

- **WHEN** 提出内容が許可されないcase status、Finding状態、next actionの組合せを含む
- **THEN** 状態Validatorは提出を拒否し、正本のrevisionを進めない

#### Scenario: 技術未解決のままワークフローが終了する

- **WHEN** 終了結果が`risk-accepted`、`evidence-gap`、`deferred`、または`not-reproducible`である
- **THEN** Owner、根拠、対象範囲、補償策、再レビュー条件を記録し、技術的なfixed-and-verifiedとは区別する

#### Scenario: cycle上限に到達する

- **WHEN** `lite`は1、標準は2、`strict`は3のreview cycle上限に達する
- **THEN** 自動クローズせず、最終リスク評価とHuman/Owner判断へ遷移する

### Requirement: 実行許可とFast Pathを検証する

コード、設定、データ、外部状態の変更は、リポジトリ規則、ユーザー承認済みスコープ、handoff許可または適格Fast Pathのすべてを満たす場合にだけ実行できる。Fast PathはLowまたは文書のみ、局所的、可逆、非破壊、外部操作なし、事前承認範囲内の場合に限定し、`proportional-home`であることだけを理由に許可してはならない。これらの実行条件はMUST（必須）とする。

#### Scenario: 適格なFast Pathを実行する

- **WHEN** Lowまたは文書のみの局所的・可逆・非破壊変更が、事前承認済み範囲内である
- **THEN** Reviewerの追加Plan Reviewを省略できるが、リポジトリ規則とユーザー承認の検証は維持する

#### Scenario: Mediumまたは範囲外の変更をFast Pathで実行する

- **WHEN** FindingがMedium/High、範囲外、破壊的、外部操作を含む、または承認が不明である
- **THEN** 実装を開始せず、通常のResponse Planまたは`blocked`を返す

### Requirement: Evidenceと参照を安全に記録する

各Findingは要求Evidence、実際のEvidence、検証者、取得時点、検証結果を区別して記録しなければならない。取得不能なEvidenceは成功とみなさず、`unverified`または`evidence-gap`としなければならない。リポジトリ内参照は相対パス、外部参照は外部であることを明示し、秘密値はマスクまたは参照拒否しなければならない。リポジトリ相対パスとして提示されたEvidenceが対象ワークスペースに存在しない場合、成功Evidenceとして記録してはならない。これらのEvidence管理はMUST（必須）とする。

#### Scenario: 実行時Evidenceを取得できない

- **WHEN** 必須の実行環境または外部システムへアクセスできず、結果を再現できない
- **THEN** Validatorは成功判定を補完せず、`unverified`または`evidence-gap`を記録する

#### Scenario: リポジトリ内のEvidenceを参照する

- **WHEN** Evidenceが同一リポジトリ内のファイルを指す
- **THEN** 記録は相対パスを使用し、絶対パスや`file://`を正規の内部参照として受理しない

#### Scenario: 秘密値を含むEvidenceを提出する

- **WHEN** Evidenceにトークン、認証情報、またはマスク不能な秘密値が含まれる
- **THEN** Evidence本体をQA記録へ複製せず、参照を拒否して`evidence-gap`を記録する

#### Scenario: 存在しないリポジトリ相対Evidenceを拒否する

- **WHEN** Evidence参照がリポジトリ相対パスとして解釈できるが対象ファイルが存在しない
- **THEN** ValidatorまたはReviewer検証は成功とみなさず、提出を拒否するか`evidence-gap`として記録する

### Requirement: ContractとCLIの互換性を安全に扱う

handoff、Author提出物、構造化CLI JSONは`contract_version`を必須とし、CLI JSONは`schema_version`、`ok`、`status`、`case_id`、`next_action`、`errors`を共通フィールドとして出力しなければならない。未知のmajor versionは推測変換せず停止し、旧Contractは読み取り専用adapterで扱わなければならない。これらの互換性条件はMUST（必須）とする。

#### Scenario: 旧Contractを読み取る

- **WHEN** v1.0またはv1.1の既存QAケースを参照する
- **THEN** adapterは読み取りを許可するが、既存履歴を自動書換えしない

#### Scenario: 未知のmajor versionを受け取る

- **WHEN** Validatorが対応していないmajor versionのhandoffまたは提出物を受け取る
- **THEN** `blocked: unsupported-contract-version`を返す

#### Scenario: JSON出力を機械処理する

- **WHEN** CLIを`--json`で実行する
- **THEN** 構造化結果はstdout、診断はstderrに出力され、statusとexit codeの対応はContractに従う
