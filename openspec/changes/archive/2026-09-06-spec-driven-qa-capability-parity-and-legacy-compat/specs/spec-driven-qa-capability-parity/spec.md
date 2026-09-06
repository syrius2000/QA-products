## Purpose

ReviewerとAuthorの公開・実行可能なQA機能が、Legacyから候補版・コンパクト版へ移行しても欠落なく利用できることを、同一入力・同一判定基準・再現可能なEvidenceによって確認する。

## ADDED Requirements

### Requirement: 公開機能台帳を正本として提供する

システムは、Legacy Bundleから抽出したすべての公開または実行可能な機能を一意な機能IDで管理しなければならない。機能台帳は少なくとも対象版、役割、入口、引数、終了コード、構造化出力の必須項目、状態変化、副作用、対応Evidenceを記録し、対象範囲を43機能IDとして明示しなければならない。機能IDの件数または定義に変更がある場合は、理由と差分を記録しなければならない。

#### Scenario: 43機能IDを台帳へ登録する

- **WHEN** Legacy Bundleの公開入口と実行可能入口を棚卸しする
- **THEN** ReviewerとAuthorの機能が重複なく一意な機能IDへ対応付けられ、各IDに検証可能な属性とEvidence参照が付与される

#### Scenario: 台帳にない公開入口を検出する

- **WHEN** 比較対象Bundleに台帳未登録の公開または実行可能入口が存在する
- **THEN** 比較結果は欠落または未台帳項目として非合格候補に分類し、説明なしに互換とみなさない

### Requirement: 三版を同一条件で比較する

比較ハーネスは、明示的に隔離されたLegacy、Contract v1.2候補、コンパクト版の各Bundleへ同一のPrompt、fixture、実行環境条件を適用しなければならない。各実行はBundleのパス、Manifest、digest、版、Agent、Runを識別できなければならず、別版の出力やキャッシュを混入させてはならない。

#### Scenario: 同一fixtureを三版へ投入する

- **WHEN** 機能台帳に対応するgolden、negative、cross-skill、Legacy互換fixtureを実行する
- **THEN** 三版それぞれの入力、終了コード、構造化出力、状態、副作用、実行結果が版別Evidenceとして保存される

#### Scenario: Bundleの同一性を確認できない

- **WHEN** BundleのManifest、digest、版識別子、または実行記録が欠落する
- **THEN** 比較結果は`unverified`または`evidence-gap`となり、互換性合格を宣言してはならない

### Requirement: 互換性判定を観測可能な契約で行う

比較判定は、少なくとも旧CLI引数、終了コード、JSON必須フィールド、契約フィールド、既存QAケースの読み取り、Reviewer／Authorの権限境界を対象にしなければならない。Candidateまたはコンパクト版がLegacyと異なる場合、差分を「未実装・欠落」「仕様上の意図的非互換」「診断文または表示形式のみの差分」に分類し、各差分へ正本仕様、移行理由、検証Evidenceを関連付けなければならない。

#### Scenario: 互換な終了コードと出力を観測する

- **WHEN** 同一機能IDへ同一fixtureを投入し、版ごとの終了コードとJSON必須項目を比較する
- **THEN** 互換条件を満たす場合は機能ID単位で合格Evidenceを記録し、診断文の差だけでは機能非互換としない

#### Scenario: 説明のない機能欠落がある

- **WHEN** Legacyに存在する機能IDがCandidateまたはコンパクト版で実行不能、未出力、または未登録である
- **THEN** その機能IDは非互換または未検証として報告され、全体合格へ自動集約されない

#### Scenario: 意図的な非互換を受け入れる

- **WHEN** 非互換がContract v1.2または後続仕様により意図的に定義され、移行理由と代替動作がEvidenceで確認できる
- **THEN** 未実装・欠落とは別分類で記録できるが、Legacy完全互換の件数には含めない

### Requirement: 安全境界と既存契約を回帰検証する

比較対象のCandidateおよびコンパクト版は、当該版に存在するReviewerの独立判定、Authorの自己クローズ拒否、未知Finding拒否、stale digest拒否、Evidenceの存在・相対パス・Workspace境界、semantic/content digest分離を満たさなければならない。版に契約が存在しない場合は`not-applicable`または`evidence-gap`として記録し、安全契約の合格へ昇格させてはならない。Legacyが安全境界を満たさない場合でも、その挙動をCandidateの合格条件へ引き下げてはならない。

#### Scenario: Authorが自己クローズを要求する

- **WHEN** Author相当の入力がReviewer正本またはケースの`closed`状態を直接更新しようとする
- **THEN** Candidateとコンパクト版は非ゼロ終了または構造化拒否を返し、正本を変更しない

#### Scenario: 古いdigestを含む提出を検証する

- **WHEN** handoffのsemantic digestまたはcontent digestが現行正本と一致しない
- **THEN** Candidateとコンパクト版は提出を拒否し、`fixed-and-verified`へ進めない

#### Scenario: 既存の安全契約とLegacy互換が衝突する

- **WHEN** Legacyの許容動作がContract v1.2の安全要件と異なる
- **THEN** 安全要件を優先し、差分を意図的非互換または残余リスクとして記録する

### Requirement: 版別適用可能性を明示する

比較ハーネスは、各機能・契約について版ごとの適用可能性を`observed`、`not-applicable`、`evidence-gap`のいずれかで記録しなければならない。`not-applicable`は、対象版の正本Bundleに契約または入口が存在しないことをManifestまたは仕様で確認できる場合に限り使用できる。`evidence-gap`は、契約の存在は示せるが実行、突合、外部測定の証拠が不足する場合に使用する。どちらもLegacy完全互換の合格とはみなしてはならない。

#### Scenario: Legacyに新契約が存在しない

- **WHEN** Legacy Bundleにsubmission、digest、revisionなど後発契約の入口が存在しない
- **THEN** Candidate／compactのObserved結果と分離して`intentional-noncompatibility`または`not-applicable`を記録し、全体をLegacy完全互換に集約しない

#### Scenario: Candidateまたはcompactの証拠が不足する

- **WHEN** 対象版に契約入口は存在するが、機能ID単位の実行結果または必須フィールド突合が不足する
- **THEN** `evidence-gap`を記録し、推測値や他版の結果で補完しない

#### Scenario: compactの契約を実観測する

- **WHEN** compactの連鎖API、提出、digest、revisionを正常系・拒否系fixtureで実行する
- **THEN** 版識別子、Run、終了コード、正本不変性、Evidence参照を付与して`observed`として記録する

### Requirement: Evidenceと未検証状態を正確に記録する

比較結果は、入力Prompt、出力、終了コード、状態、実行時刻、所要時間、Token情報、Bundle識別情報、digest、実行者、Run識別子を、再現可能なAgent単位・Run単位で保存しなければならない。取得不能な外部LLMの正答率、Latency、Token量、外部配備後の挙動は推定値で補完せず、`unverified`または`evidence-gap`として記録しなければならない。

#### Scenario: 外部AIで動的測定を実行する

- **WHEN** 同一Prompt suiteを複数の外部AIへ投入し、各AIが分離されたEvidenceディレクトリへ結果を保存する
- **THEN** CoordinatorはAgent／Run単位の結果を混同せず集計し、モデル名、条件、未実行項目、Observed値を明示する

#### Scenario: TokenまたはLatencyを取得できない

- **WHEN** 実行環境がTokenまたはLatencyの信頼できる実測値を提供しない
- **THEN** 該当指標は`unverified`のまま保持され、フェルミ推定値をObserved Evidenceや完了判定として扱わない

#### Scenario: Evidenceに秘密値が含まれる

- **WHEN** 結果またはdigest入力にAPIキー、Token、パスワードなどが含まれる
- **THEN** 秘密値を保存・集計せず、検証を拒否するか`evidence-gap`として安全に記録する
