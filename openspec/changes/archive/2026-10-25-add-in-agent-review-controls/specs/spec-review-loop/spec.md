## ADDED Requirements

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

## MODIFIED Requirements

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
