# spec-review-loop Specification

## Purpose
OpenSpec changeの目的・Scenario・タスクを受入基準として固定し、実装担当と別系統のAI Reviewerによる独立レビューを数roundで自動的に往復させてchangeを完成させる。終了時にはround commit群を検証付きで1 commitへ整える。

## Requirements

### Requirement: 明示起動と他QA経路との区別
システムは、利用者が現在のメッセージで対象のOpenSpec changeを示し、`spec-review-loop`によるレビューループの実行を明示的に依頼した場合だけ起動しなければならない（MUST）。QAの相談・説明、結果の共有、一般的なコードレビュー、OpenSpec apply／verifyだけの依頼で起動してはならない（MUST NOT）。`quality-qa`、`blind-qa-cycle`、`quality-review`、`quality-response`の成果物・case正本・CLI状態を作成・変更してはならない（MUST NOT）。

#### Scenario: changeを指定してループを依頼する
- **WHEN** 利用者が`/spec-review-loop <change-id>`、または対象changeを示してレビューループの実行を依頼する
- **THEN** システムは対象changeの存在を確認してから`start`を実行する

#### Scenario: 説明や一般レビューだけを求める
- **WHEN** 利用者がループの仕組みの説明、一般的なコードレビュー、またはOpenSpec applyだけを依頼する
- **THEN** システムはループを起動せず、既存QA経路の記録も変更しない

### Requirement: OpenSpec changeから受入基準を固定する
システムは`start`時に対象changeの`tasks.md`のタスクと検証文、および`specs/**/spec.md`のScenarioから受入基準を抽出し、安定ID・原文・要件指紋を`review/criteria.json`へ保存しなければならない（MUST）。要件指紋はチェックボックスの状態を除いた原文から計算しなければならない（MUST）。必須checkとして`openspec validate --strict <change-id>`を含めなければならない（MUST）。抽出件数が0件の場合は開始してはならない（MUST NOT）。

#### Scenario: タスクとScenarioを抽出する
- **WHEN** tasks.mdに番号付きタスクがあり、spec deltaにScenarioがあるchangeで`start`を実行する
- **THEN** 各タスクに`T-N.M`、各Scenarioに`S-<cap>-<要件番号>.<n>`のIDが原文の順序で付き、一覧が利用者に表示される

#### Scenario: タスクを完了済みにしても指紋が変わらない
- **WHEN** 実装担当がround中にタスクを`[ ]`から`[x]`へ変更する
- **THEN** そのタスクの要件指紋は変わらず、基準ドリフトとして扱われない

#### Scenario: 基準がround途中で書き換わる
- **WHEN** round開始時に再抽出した基準の指紋集合が`criteria.json`と異なる
- **THEN** システムはGateをHOLDとしてループを停止し、変更された基準IDと`refreeze`の必要を示す

#### Scenario: 基準を抽出できない
- **WHEN** 対象changeにtasks.mdもScenarioも見つからない
- **THEN** システムは`start`を拒否し、何もcommitしない

### Requirement: roundごとにcommitでレビュー対象を固定する
システムはmain／master以外のtopic branchでのみ開始し、開始時のHEADをbase SHAとして記録しなければならない（MUST）。各roundの終わりに、実装報告`review/r<N>_report.md`を含むround commitを作り、件名`spec-review: r<N> <change-id>`とtrailer `Spec-Review-Round: <change-id> r<N>`を付けなければならない（MUST）。stage済みの変更と`review/`配下の成果物以外を自動でstageしてはならない（MUST NOT）。

#### Scenario: default branchで開始しようとする
- **WHEN** 現在のbranchがmainまたはmasterで`start`を実行する
- **THEN** システムは開始を拒否し、topic branchへの切替を案内する

#### Scenario: 実装報告なしでroundを閉じようとする
- **WHEN** `review/r<N>_report.md`が存在しない状態で`commit-round`を実行する
- **THEN** システムはcommitせず、実装報告の作成を求める

#### Scenario: 対象外の変更が残っている
- **WHEN** `commit-round`の時点でunstagedまたはuntrackedの変更がある
- **THEN** システムはそのpathを表示してcommitせず、stageするか除外するかの判断を求める

### Requirement: 別系統のAI Reviewerが読取り専用で独立レビューする
システムはround SHAから作った一時worktreeをcwdとして、実装担当とは別のプロセスでReviewer CLIを起動しなければならない（MUST）。既定のReviewerはCodex CLIとし、Cursor CLI（`agent`）とClaude CLIを選択でき、モデルと推論effortを指定できなければならない（MUST）。Reviewerは読取り専用で実行し、製品コード・作業ツリー・review成果物を変更してはならない（MUST NOT）。Reviewerに過去roundのPASS判定を根拠として渡してはならない（MUST NOT）。

#### Scenario: 既定Reviewerでレビューする
- **WHEN** Reviewerの指定なしで`review`を実行する
- **THEN** システムはround SHAの一時worktreeでCodex CLIを読取り専用で起動し、使用したツール名・バージョン・モデル名を記録する

#### Scenario: Reviewer CLIが見つからない
- **WHEN** 指定されたReviewer CLIが未導入、または必要な読取り専用指定に対応しない
- **THEN** システムはレビューを実行せず、`doctor`の結果と導入・切替の方法を示す

#### Scenario: Reviewerが失敗する
- **WHEN** Reviewerの起動失敗、timeout、またはスキーマ不適合の出力が起きる
- **THEN** システムはそのroundをINCONCLUSIVEとして記録し、PASSにせず、同じReviewerの再試行を1回まで許す

#### Scenario: 失敗したReviewerを別のReviewerへ切り替える
- **WHEN** あるReviewerが同じroundで再試行の上限まで失敗した後、未試行の別Reviewerを`--reviewer`で指定して`review`を実行する
- **THEN** システムは同じround SHAを別のReviewerでレビューし、各attemptのReviewerとエラーを記録し、有効な結果にだけGateを適用する

#### Scenario: 試行済みのReviewerを再実行しようとする
- **WHEN** 上限まで失敗したReviewerを指定して`review`を実行する
- **THEN** システムは起動せず、別のReviewerへの切替を案内する

### Requirement: レビュー結果を構造検証してGateを判定する
システムはReviewer出力が、`criteria.json`の全基準IDを同じ順序でちょうど1回ずつ含み、原文・base SHA・round SHAが一致することを検証しなければならない（MUST）。Gateは、HOLD（provenance不一致・基準ドリフト）、FAIL（いずれかの基準または必須checkがFAIL）、INCONCLUSIVE（FAILがなくUNVERIFIED・NOT_RUN・ERRORがある）、PASS（全基準と全必須checkがPASS）の優先順位で決定論的に判定しなければならない（MUST）。対応する基準のない改善要求は提案として記録し、Gateに数えてはならない（MUST NOT）。

#### Scenario: 基準IDが欠落した結果を受け取る
- **WHEN** Reviewer出力に`criteria.json`の基準IDのいずれかが含まれない、または重複する
- **THEN** システムはその出力をスキーマ不適合として扱い、Gateを判定しない

#### Scenario: FAILと必須checkの未実行が併存する
- **WHEN** ある基準がFAILで、同時に必須checkがNOT_RUNである
- **THEN** GateはFAILとなり、各check状態と理由は個別に記録される

#### Scenario: 範囲外の改善要求が出る
- **WHEN** Reviewerが受入基準に対応しない改善を求める
- **THEN** その指摘は提案として`r<N>_review.md`に記録され、GateとFindingの停滞判定に影響しない

### Requirement: 停止条件に達したら止めて引き継ぐ
システムはGateがPASSになった時点、round上限（既定3）に達した時点、またはFindingが停滞した時点でループを止めなければならない（MUST）。停滞とは、同じFinding IDが2 round連続で未解消のとき、または未解消Findingの数が前roundから減らないときをいう。PASS以外で停止した場合、残ったFindingと、人の判断・`quality-review`の`review-standalone`・`blind-qa-cycle`の選択肢を示さなければならない（MUST）。いずれの場合も`openspec archive`を自動実行してはならない（MUST NOT）。

#### Scenario: 2 round目でPASSする
- **WHEN** 2 round目のGateがPASSになる
- **THEN** システムはループを止め、`finish`による整理と、人による`openspec archive`の判断を案内する

#### Scenario: 同じFindingが解消されない
- **WHEN** Finding `F-002`が2 round連続で未解消と判定される
- **THEN** システムはround上限前でもループを止め、`F-002`の内容と引継ぎの選択肢を示す

#### Scenario: round上限に達する
- **WHEN** 3 round目のGateがPASSにならない
- **THEN** システムは4 round目を開始せず、未解決Findingと選択肢を示す

### Requirement: 終了時にround commitを検証付きでsquashする
システムは`finish`で、dry-runの計画を表示し、利用者の明示確認を受けてからround commit群を1つのcommitへまとめなければならない（MUST）。base..HEADに対象changeのround commit以外が含まれる場合、いずれかのround commitがリモート追跡refから到達可能な場合、または作業ツリーがcleanでない場合はsquashしてはならない（MUST NOT）。squash前のHEADをローカルref `refs/spec-review/<change-id>/<timestamp>`に保存し、squash後のtreeがsquash前のtreeと一致することを検証しなければならない（MUST）。force-pushを行ってはならない（MUST NOT）。

#### Scenario: PASS後に確認してsquashする
- **WHEN** GateがPASSで前提条件を満たし、利用者が計画を確認して`finish --confirm`を実行する
- **THEN** システムは`review/summary.md`を加えたうえでバックアップrefを作り、base以降を1 commitにまとめ、tree一致を検証して、round数・Gate・Reviewer・squash前SHAをtrailerに記録する

#### Scenario: round commitが既にpushされている
- **WHEN** base..HEADのround commitのいずれかがリモート追跡refから到達可能である
- **THEN** システムはsquashせず、force-pushが必要になるため別途の明示承認と手作業が必要であることを示す

#### Scenario: tree一致の検証に失敗する
- **WHEN** squash後の`HEAD^{tree}`がバックアップrefのtreeと一致しない
- **THEN** システムはバックアップrefの状態へ戻し、失敗として報告する

#### Scenario: PASS以外で終了する
- **WHEN** 利用者がPASS以外のGateで`finish`を求める
- **THEN** システムは`--accept-residual`による明示を求め、そのGateと残余Findingを要約とtrailerに記録する

### Requirement: レビュー成果物をchangeとともに残す
システムは基準、実装報告、レビュー結果（JSONとMarkdown）、要約を`openspec/changes/<change-id>/review/`に保存しなければならない（MUST）。バックアップrefの削除は`prune`の明示実行に限り、その際にround SHAへ到達できなくなることを表示しなければならない（MUST）。

#### Scenario: archive後も証跡を参照する
- **WHEN** 利用者がsquash後に`openspec archive`を実行する
- **THEN** `review/`配下の成果物がarchive先のchangeフォルダに含まれ、round SHAとGate推移を`summary.md`で確認できる

#### Scenario: バックアップrefを削除する
- **WHEN** 利用者が`prune`を実行する
- **THEN** システムは対象refとround SHAが到達不能になることを表示し、確認後にだけ削除する

### Requirement: Reviewerの実行中に進行を確認できる
システムはReviewerの出力を実行中に`review/r<N>_reviewer.log`へ逐次書き出し、実行中は`status`でPID・経過時間・ログの末尾を報告しなければならない（MUST）。同じchangeで実行中のreviewがある間は、別のreviewを開始してはならない（MUST NOT）。ログはcommitとsquashの対象にしてはならない（MUST NOT）。

#### Scenario: 実行中にstatusを確認する
- **WHEN** Reviewerの実行中に`status`を実行する
- **THEN** システムは実行中であること、PID、経過時間、ログの末尾を示し、ログはReviewerの出力に応じて増えている

#### Scenario: 実行中に二重にreviewする
- **WHEN** 実行中のreviewがある状態で`review`を実行する
- **THEN** システムは新しいReviewerを起動せず、実行中であることを示して拒否する

#### Scenario: 実行中のプロセスが消えている
- **WHEN** ロックが残っているがそのPIDのプロセスが存在しない
- **THEN** システムは古いロックとして破棄し、reviewを開始できる

### Requirement: 人の指示を原文のまま次のroundへ引き継ぐ
システムは`instruct`で与えられた人の発言を記録し、未消化の指示がある間は、その原文を含まない実装報告でのround commitを拒否しなければならない（MUST）。`start --pause round`が指定されたとき、stopしないreviewの後は、`instruct`で人の指示が記録されるまで次のround commitを拒否しなければならない（MUST）。発言が空の`instruct`は拒否しなければならない（MUST）。

#### Scenario: 指示を報告に転記せずにroundを閉じる
- **WHEN** 未消化の指示があり、`r<N>_report.md`にその原文が含まれない状態で`commit-round`を実行する
- **THEN** システムはcommitせず、欠けている指示の原文を表示して報告への記載を求める

#### Scenario: 指示を転記してroundを閉じる
- **WHEN** 未消化の指示の原文を`r<N>_report.md`に含めて`commit-round`を実行する
- **THEN** システムはcommitし、その指示を消化済みとしてround番号とともに記録する

#### Scenario: round間で一時停止する
- **WHEN** `start --pause round`で開始し、review後にGateが停止条件に達していない状態で`commit-round`を実行する
- **THEN** システムはcommitせず、人に結果を見せて`instruct`で指示を記録するよう求める

#### Scenario: 停止後に指示を記録しようとする
- **WHEN** ループがPASS・停滞・上限・HOLDのいずれかで停止している状態で`instruct`を実行する
- **THEN** システムは記録せず、停止理由と、再固定または判断の明示の方法を示す

#### Scenario: 未消化の指示があるままfinishする
- **WHEN** 実装報告に反映されていない指示がある状態で`finish --confirm`を実行する
- **THEN** システムは拒否し、指示の原文を示す。利用者の判断を`--accept-residual`で明示した場合だけ、指示IDと判断をtrailerに残して終了する

#### Scenario: 空の指示を記録しようとする
- **WHEN** `instruct`を空の`--message`で実行する
- **THEN** システムは記録せず、人の発言を渡すよう求める

### Requirement: 保存したプロンプトと結果の書換えを検知する
システムはReviewerへ渡したプロンプトと`r<N>_review.json`のSHA-256を記録し、保存後に内容が変わった場合は`status`・`commit-round`・`review`・`finish`でHOLDとして扱い、対象ファイルを示して拒否しなければならない（MUST）。

#### Scenario: レビュー結果が保存後に書き換えられる
- **WHEN** `r1_review.json`の内容を変更した後に`status`を実行する
- **THEN** システムはHOLDと、記録したSHA-256と一致しないファイル名を示す

#### Scenario: 書換えがある状態でfinishする
- **WHEN** 記録したSHA-256と一致しないレビュー成果物がある状態で`finish --confirm`を実行する
- **THEN** システムはsquashせず、HOLDの原因を示す
