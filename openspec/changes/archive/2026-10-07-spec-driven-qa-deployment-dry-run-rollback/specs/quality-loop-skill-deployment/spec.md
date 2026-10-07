# Spec Delta

## MODIFIED Requirements

### Requirement: 開発正本と同梱runtimeの一致
システムは`quality-loop/qa_workflow/`を`quality-qa` runtimeの開発正本、`quality-loop/quality_loop/`を`quality-review`および`quality-response` runtimeの開発正本として扱い、各Skillに同梱するruntimeをそれぞれ対応する正本と一致させなければならない（SHALL）。同梱対象にはPythonソースを含め、`__pycache__`、`.pyc`その他の生成物を含めてはならない（MUST NOT）。

#### Scenario: 配布前のruntime比較
- **WHEN** 配布可能性を確認する
- **THEN** 各Skillの同梱runtimeに必要なPythonソースが存在し、対応する開発正本との差異と不要な生成物の有無を判定できる

### Requirement: 自己完結したSkill配布単位
システムは`quality-qa`、`quality-review`、`quality-response`の各Skillについて、Skill定義、必要な参照資料、Skill固有のruntime全体、および配置場所に依存しないCLI実行入口を含む自己完結したディレクトリを提供しなければならない（SHALL）。各Skillは開発リポジトリの`quality-loop/`をPython import pathまたは作業ディレクトリとして要求してはならない（MUST NOT）。

#### Scenario: グローバル配置後のCLI起動
- **WHEN** 完全なSkillディレクトリを`~/.agents/skills/<skill-name>/`へコピーし、同梱CLI実行入口を呼び出す
- **THEN** 外部Python依存を追加せず、各Skillに同梱されたruntimeからCLIを起動できる

#### Scenario: リポジトリローカル配置後のCLI起動
- **WHEN** 完全なSkillディレクトリを任意リポジトリの`.agents/skills/<skill-name>/`へコピーし、別の作業ディレクトリから同梱CLI実行入口を呼び出す
- **THEN** 開発元リポジトリへの相対参照なしで各Skillの同梱runtimeからCLIを起動できる

### Requirement: グローバル配置とローカル配置
配置手順は、グローバル配置先を`~/.agents/skills/quality-qa/`、`~/.agents/skills/quality-review/`、`~/.agents/skills/quality-response/`、ローカル配置先を`<repo>/.agents/skills/`配下の同名3ディレクトリとして明示しなければならない（SHALL）。グローバルとローカルの両方に同名Skillがある場合、ローカルSkillを優先する運用契約を明示しなければならない（SHALL）。

#### Scenario: グローバル配置先の選択
- **WHEN** 利用者が複数リポジトリから共通利用する配置を選択する
- **THEN** 手順は3つのSkillをそれぞれのグローバル配置先へコピーする対象として示す

#### Scenario: リポジトリローカル配置先の選択
- **WHEN** 利用者が指定したリポジトリだけで利用する配置を選択する
- **THEN** 手順は3つのSkillをそのリポジトリの`.agents/skills/`配下へコピーする対象として示す

#### Scenario: ローカル配置先の選択
- **WHEN** 利用者が指定したリポジトリだけで利用する配置を選択する
- **THEN** 手順は3つのSkillをそのリポジトリの`.agents/skills/`配下へコピーする対象として示す

### Requirement: 最小配置検査
配布可能性の確認は、自動テストスイートを追加または必須化せず、各Skillのfrontmatter、必要ファイル、同梱runtimeのimport、CLI実行入口の安全な起動、および想定配置構成を検査しなければならない（SHALL）。検査できない事項を成功として扱ってはならない（MUST NOT）。

#### Scenario: 最小検査が成功する
- **WHEN** 3つのSkillについてfrontmatter、必要ファイル、runtime import、CLIの`--help`、および配置構成を確認する
- **THEN** 各確認項目の成功結果と対象を記録できる

#### Scenario: 最小検査に失敗する
- **WHEN** 必須ファイル欠落、runtime不一致、import失敗、CLI起動失敗、または配置構成不整合を検出する
- **THEN** 配布可能と判定せず、失敗項目を示す

### Requirement: 利用優先のドキュメント導線
ルート`README.md`は、リポジトリの哲学や開発履歴より先に、利用者がQuality Loopを使い始めるための最短導線、3つのSkillの使い分け、および詳細手順へのリンクを提示しなければならない（SHALL）。専用デプロイガイドは、グローバル配置とローカル配置の選択、手動コピー、衝突確認、更新、最小検査、Rollback、および承認境界をコピー可能な日本語手順として提供しなければならない（SHALL）。

#### Scenario: 初見利用者がREADMEを開く
- **WHEN** Quality Loopをすぐ使いたい利用者がルート`README.md`を上から読む
- **THEN** 現在状態や設計思想の詳細より先に、配置方法、3 Skillの用途、案件開始、詳細ガイドへの導線を確認できる

#### Scenario: グローバルへ手動配置する
- **WHEN** 利用者が複数リポジトリからSkillを利用するため専用デプロイガイドを読む
- **THEN** 対象固定、既存同名Skill確認、手動コピー、配置後検査を順番どおり実行できる

#### Scenario: 指定リポジトリへ手動配置する
- **WHEN** 利用者が一つのリポジトリだけでSkillを利用するため専用デプロイガイドを読む
- **THEN** `<repo>/.agents/skills/`への配置、グローバル配置との関係、衝突時停止を確認できる

### Requirement: 外部配置の承認境界
外部配置は、対象Skillの実装・独立QAの確認、対象パスを固定したmanifest、既存先backupまたは不存在記録、dry-run、配置後検証、検証済みrollback手順、および対象パスを明記したOwnerの明示承認が揃う場合に限り実行できる（SHALL）。承認されていないパス、同名既存Skill、またはmanifest不一致を検出した場合は停止し、上書きしてはならない（MUST NOT）。

#### Scenario: 承認済み対象だけを配置する
- **WHEN** Ownerがmanifestに記録された3つのグローバルSkillパスを明示承認し、配置前条件が全て成功する
- **THEN** 手順はその3パスだけを作成し、配置後のファイル一覧・ハッシュ・CLI起動結果を記録する

#### Scenario: 配置条件または範囲が不一致
- **WHEN** 既存Skill、manifest不一致、失敗した検査、未検証rollback、または範囲外パスを検出する
- **THEN** グローバル配置を開始または継続せず、既存ファイルを変更しない

#### Scenario: Change実装中の配置
- **WHEN** このChangeの実装またはローカル検証を実行する
- **THEN** Ownerが明示承認した対象3パスだけを作成し、それ以外のリポジトリ外パスおよび指定されていない他リポジトリを変更しない

#### Scenario: 外部配置の依頼
- **WHEN** 利用者が実際のグローバル配置または他リポジトリへの配置を要求する
- **THEN** 実装完了、独立QA、manifest、対象パス、および明示承認を確認し、条件を満たす指定先だけへ配置する

## ADDED Requirements

### Requirement: 通常QA Skillの発火範囲
`quality-qa`は通常のQA依頼、独立レビュー結果の確認、明示承認後の修正と再QA、状況確認を対象にし、Quality Loop formal case専用SkillのReviewer／Implementer roleを代行してはならない（MUST NOT）。

#### Scenario: 通常QA依頼
- **WHEN** 利用者が対象リポジトリのQA依頼またはQA結果確認を明示する
- **THEN** `quality-qa`が対象となり、formal caseの正本を作成・変更しない

#### Scenario: Formal caseのRole操作
- **WHEN** 既存Quality Loop caseでReviewerまたはImplementerの操作が要求される
- **THEN** `quality-review`または`quality-response`を該当Roleに応じて使い、`quality-qa`はformal case操作を開始しない

### Requirement: 配置rollbackの限定性
配置rollbackは本Changeで新規作成したSkillディレクトリだけを対象にし、配置前manifestに存在したファイルを削除または変更してはならない（MUST NOT）。

#### Scenario: 新規配置のrollback
- **WHEN** 配置後検査が失敗し、rollbackを実行する
- **THEN** 本Changeで作成した対象Skillだけを撤去し、配置前manifestの状態が復元されたことを確認する

#### Scenario: 配置前から存在したSkill
- **WHEN** rollback対象のいずれかが配置前manifestに存在する
- **THEN** そのSkillを削除せず停止し、手動判断へ返す
