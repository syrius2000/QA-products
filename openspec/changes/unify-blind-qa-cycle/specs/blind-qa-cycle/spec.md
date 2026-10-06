# Spec Delta

## Purpose

独立QAを監査ブランチ上で安全に開始し、固定された対象へのレビュー、実装側のFinding対応、再QA、サイクル終結まで追跡する。終結時に担当者自身がQAから学んだ設計理解を短く記録できるようにする。

## ADDED Requirements

### Requirement: blind QAサイクルの用途と他QA経路を区別する
システムは固定SHAと監査ブランチ上のYip commitを用いた独立QAを`blind-qa-cycle`で扱い、通常QAおよび正式Quality Loop caseと用途を区別しなければならない（MUST）。既存の`quality-qa`、`quality-review`、`quality-response`の成果物、case正本、CLI状態をblind cycleへ自動変換・書込みしてはならない（MUST NOT）。

#### Scenario: 監査ブランチ上の独立QAを開始する
- **WHEN** 利用者が固定SHAを使う独立レビューと監査ブランチ上のQA往復を明示する
- **THEN** システムは`blind-qa-cycle`の手順とcycle成果物を用い、対象QA方式、branch、開始基準を記録する

#### Scenario: 通常QAまたは正式caseの依頼を受ける
- **WHEN** 利用者が通常QA、またはQuality Loop caseのReviewer／Implementer操作を求める
- **THEN** システムは既存の`quality-qa`または`quality-review`／`quality-response`を案内し、blind cycleの成果物・case正本へ移し替えない

### Requirement: QA開始時点と対象コミットを固定する
システムは実装前の`00_plan.md`作成経路を提供し、目的・受入基準・準備前のHEADを記録した計画をYip commitへ固定しなければならない（MUST）。計画commit自身をBaselineとして用い、実装後に完了済み変更をYip Reviewed commitへ固定して最終招待を作成する。事前準備されていない場合も明示的な事後開始を許可し、既存checkpoint commitまたは同じcloud操作で新規topic branchを作る場合はbranch切替前の固定HEADをBaselineとして使える。後者はその完全SHAがbranch開始commitであり、Reviewed前に別commitがない場合に限り、最終招待へbranch-start理由を記録する。最終招待は開始方式、対象branch、BaselineとReviewedの完全SHAを記録し、指定SHAが取得できない場合は別のcommitで代用してはならない（MUST NOT）。

#### Scenario: 実装前にQA計画をYip commitへ固定する
- **WHEN** cleanな非default topic branchで実装前にQAサイクルを準備する
- **THEN** システムは目的・受入基準・準備前HEADを`00_plan.md`へ保存して計画だけのYip commitを作り、そのcommit SHAを後続レビューのBaselineとして記録する

#### Scenario: 計画commit後に実装とレビューを行う
- **WHEN** `00_plan.md`が固定された後に実装側が対象変更を完成し、Reviewed Yip commitを作る
- **THEN** 最終招待は計画commitをBaseline、実装commitをReviewedとして記録し、Reviewer向けdiffから計画commit以前の履歴とQA計画を除外する

#### Scenario: 実装後にQAを開始する
- **WHEN** 事前計画がない状態で実装後の対象変更をQAへ出す
- **THEN** 現行checkpoint規則を満たすBaselineと、対象変更を固定するReviewed SHAを使い、最終招待に事後開始であることを記録する

#### Scenario: 完了済み変更から新しいQA branchを作る
- **WHEN** 利用者が完成済み変更のQA用に新しいtopic branchを明示し、操作前のbranch HEADが記録される
- **THEN** そのbranch-start SHAをBaselineとして使い、そこからの変更をReviewed commitに固定して、招待へ元branchとBaseline選定理由を記録する

#### Scenario: 指定SHAが取得できない
- **WHEN** Reviewerの環境でBaselineまたはReviewed SHAを解決できない
- **THEN** GateをHOLDとし、別SHA・HEAD・既定ブランチでレビューを続けない

### Requirement: LocalとCloudで同じ独立レビュー契約を使う
システムはLocalとCloudの双方で同じ対象SHA、受入基準、Reviewer独立性、出力契約を適用しなければならない（MUST）。Localはpushせず、Cloudは明示されたCloud QAフローで必要なtopic branch上のcommitだけを扱わなければならない（MUST）。

#### Scenario: Local reviewerへ渡す
- **WHEN** Audienceが`local`で別のローカル担当へレビューを依頼する
- **THEN** 固定SHAと相対Output DIRを共有し、対象branchのpushを行わず、指定されたQA成果物を同じclone上に保存する

#### Scenario: Cloud reviewerへ渡す
- **WHEN** Audienceが`cloud`でレビューを依頼する
- **THEN** cloudから固定SHAと依頼を取得できることを確認し、取得できない場合はHOLDまたはingest可能な結果返却とし、別の対象へ切り替えない

#### Scenario: 実装担当が同一対象をレビューする
- **WHEN** 実装を行った担当がその同じ対象を独立QAとしてレビューしようとする
- **THEN** システムは独立レビューとして受理せず、別担当へのhandoffを求める

### Requirement: レビュー結果をcycle単位で保存する
Reviewerは固定対象と全受入基準に対する評価、根拠付きFinding、対応が必要なFindingごとの修正タスク、必須checkの実行結果または未実施理由を所定のcycle DIRへ保存しなければならない（MUST）。既存cycleの成果物を上書きしてはならない（MUST NOT）。

#### Scenario: 指摘と修正依頼を返す
- **WHEN** 固定対象に要求未達または不具合が見つかる
- **THEN** ReviewerはEvidenceと期待動作を記録し、対応が必要なFindingごとにpath、action、観察可能な完了条件、検証方法を含むtaskを作成する

#### Scenario: 必須checkを実行できない
- **WHEN** 必須checkが実行不能または未実施である
- **THEN** Reviewerは状態と理由を記録し、実行済み成功として扱わない

#### Scenario: 過去cycleが存在する
- **WHEN** 同じtopicで次のレビューを作る
- **THEN** 新しいcycle DIRを使い、以前の招待・レビュー・task・機械可読状態を変更しない

### Requirement: Finding対応後の再QAを追跡する
システムは実装側のFinding別対応と修正Yip commitを記録し、再QA時に前回Reviewedを新cycleのBaselineとして引き継がなければならない（MUST）。Reviewerの再確認なしにFindingを解決済みと記録してはならない（MUST NOT）。

#### Scenario: 実装側がFindingへ対応する
- **WHEN** 実装側がレビュー結果に基づく修正を行う
- **THEN** 対応したFinding IDと修正範囲をYip commitおよび後続依頼へ結び付ける

#### Scenario: 修正後に再QAする
- **WHEN** 修正対象がReviewerへ再提出される
- **THEN** 新cycleを作り、前回ReviewedをBaselineとして、対象Findingと元の受入基準を再確認する

#### Scenario: 前回の指摘が再QA結果から欠落する
- **WHEN** 再QA結果に前回の未解決Findingの確認がない
- **THEN** Findingを未解決または未検証のまま保持し、欠落を解消とみなさない

### Requirement: Human Understanding Noteを人が作成する
サイクル終結支援はHuman Understanding Noteの空テンプレートをcycle DIRに作成し、担当者が約5分で自分の言葉で記入できるよう促さなければならない（MUST）。NoteにはQA cycleと関連SHA・最終Gateを追跡できる出典情報を付け、Note本文をAIが人の理解として代筆または採点してはならない（MUST NOT）。

#### Scenario: サイクル終結時にNoteを作る
- **WHEN** Findingsの処置と最終QA結果を確認し、担当者がサイクルを終結しようとする
- **THEN** システムは`04_human_understanding.md`を作成し、cycle ID、Repository/branch、Baseline/Reviewed SHA、最終Gateを既存記録から付与して、担当者に記入を促す

#### Scenario: 人が理解内容を記入する
- **WHEN** 担当者がNoteを記入する
- **THEN** テンプレートはsystem boundary、守るinvariant、最も危険だったfailure mode、防止mechanism、AIなしで説明できる設計、まだ理解していない点を尋ね、未理解点をそのまま記録できる

#### Scenario: Noteが既に存在する
- **WHEN** 指定cycle DIRにNoteが既にある
- **THEN** システムは既存本文を上書きせず、読取りまたは別の新規cycleでの作成を案内する

#### Scenario: Noteが未記入または理解が不十分である
- **WHEN** 担当者が空欄や未理解点を残す
- **THEN** システムはNoteをQA Gate、Findingの処置状態、Owner受入の証明として扱わず、未理解を可視化した記録として保存する

### Requirement: サイクル終結をGit統合とOwner判断から分離する
システムは全Findingの状態、残余リスク、最終QA Gate、Human Understanding Note、関連SHAをcycle内で追跡して監査サイクルを終結できなければならない（MUST）。終結だけを根拠として既定ブランチへのmerge、配備、Owner受入、外部Skill変更を実行してはならない（MUST NOT）。

#### Scenario: 監査サイクルを終結する
- **WHEN** QA結果、Finding処置、残余リスク、関連SHAとHuman Understanding Noteの保存先が確認される
- **THEN** cycleを監査ブランチ上で終結した状態として記録し、必要ならOwner判断へ渡す

#### Scenario: 既定ブランチへ統合する
- **WHEN** QAサイクル終結後にmain/masterへのmergeや配備が検討される
- **THEN** システムはそれを別のOwner判断・承認工程として案内し、QA終結操作では実行しない

### Requirement: QA Skill間の既存境界を保つ
システムは`blind-qa-cycle`を独立ブランチQAに限定し、`quality-qa`、`quality-review`、`quality-response`の既存利用方法・保存データ・CLI動作を変更してはならない（MUST NOT）。

#### Scenario: 他のQA Skillが必要な依頼
- **WHEN** 依頼が通常QAまたは正式Quality Loop caseのRole操作に該当する
- **THEN** 適切な既存Skillへ案内し、その正本データをblind cycle用DIRへ複製または移動しない
