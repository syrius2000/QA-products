## Purpose

Quality LoopのReviewer／Implementer Skillを、Python共通基盤込みの自己完結した配布単位として安全にコピーし、グローバルまたは任意リポジトリで同一契約のまま利用できるようにする。

## ADDED Requirements

### Requirement: 自己完結したSkill配布単位
システムは`quality-review`および`quality-response`の各Skillについて、Skill定義、必要な参照資料、`quality_loop` Pythonパッケージ全体、および配置場所に依存しないCLI実行入口を含む自己完結したディレクトリを提供しなければならない（SHALL）。各Skillは、開発リポジトリの`quality-loop/`をPython import pathまたは作業ディレクトリとして要求してはならない（MUST NOT）。

#### Scenario: グローバル配置後のCLI起動
- **WHEN** 完全なSkillディレクトリを`~/.agents/skills/<skill-name>/`へコピーし、同梱CLI実行入口を呼び出す
- **THEN** 外部Python依存を追加せず、同梱された`quality_loop`からCLIを起動できる

#### Scenario: リポジトリローカル配置後のCLI起動
- **WHEN** 完全なSkillディレクトリを任意リポジトリの`.agents/skills/<skill-name>/`へコピーし、別の作業ディレクトリから同梱CLI実行入口を呼び出す
- **THEN** 開発元リポジトリへの相対参照なしで同梱された`quality_loop`からCLIを起動できる

### Requirement: 開発正本と同梱runtimeの一致
システムは`quality-loop/quality_loop/`をPython共通基盤の開発正本として扱い、両Skillへ同梱するruntimeをその正本と一致させなければならない（SHALL）。同梱対象にはPythonソースを含め、`__pycache__`、`.pyc`その他の生成物を含めてはならない（MUST NOT）。

#### Scenario: 配布前のruntime比較
- **WHEN** 配布可能性を確認する
- **THEN** 各Skillの同梱runtimeに必要なPythonソースが存在し、開発正本との差異と不要な生成物の有無を判定できる

### Requirement: グローバル配置とローカル配置
配置手順は、グローバル配置先を`~/.agents/skills/quality-review/`および`~/.agents/skills/quality-response/`、ローカル配置先を`<repo>/.agents/skills/quality-review/`および`<repo>/.agents/skills/quality-response/`として明示しなければならない（SHALL）。グローバルとローカルの両方に同名Skillがある場合、ローカルSkillを優先する運用契約を明示しなければならない（SHALL）。

#### Scenario: グローバル配置先の選択
- **WHEN** 利用者が複数リポジトリから共通利用する配置を選択する
- **THEN** 手順は2つのSkillをそれぞれのグローバル配置先へコピーする対象として示す

#### Scenario: ローカル配置先の選択
- **WHEN** 利用者が指定したリポジトリだけで利用する配置を選択する
- **THEN** 手順は2つのSkillをそのリポジトリの`.agents/skills/`配下へコピーする対象として示す

### Requirement: 同名SkillのFail-Closed保護
配置手順は、配置先に同名Skillが存在しない場合だけ新規コピーを許可しなければならない（SHALL）。既存内容が配布元と同一の場合は配置を省略し、差異がある場合は差分を提示して停止し、明示承認なしに上書きしてはならない（MUST NOT）。

#### Scenario: 同名Skillが存在しない
- **WHEN** 配置先に対象Skillディレクトリが存在しない
- **THEN** 手順は新規コピー可能と判定する

#### Scenario: 同一内容のSkillが存在する
- **WHEN** 配置先の対象Skillが配布元と同一内容である
- **THEN** 手順はコピーを省略し、変更不要であることを示す

#### Scenario: 異なる内容のSkillが存在する
- **WHEN** 配置先の対象Skillが配布元と異なる
- **THEN** 手順は差異を示して停止し、既存Skillを変更しない

### Requirement: Role限定による誤発火防止
`quality-review`は明示されたQuality Loop案件のReviewer工程だけに、`quality-response`は明示されたQuality Loop案件のImplementer工程だけに発火条件を限定しなければならない（SHALL）。各Skillは、一般的なコードレビュー、一般的な回答作成、OpenSpec案件一般、他のQAワークフロー、およびRole外操作を非発火条件として明記しなければならない（SHALL）。

#### Scenario: Reviewer工程の発火
- **WHEN** 明示されたQuality Loop案件で`next_role=reviewer`かつ対応するReviewer操作が要求される
- **THEN** `quality-review`だけが対象Skillとなる

#### Scenario: Implementer工程の発火
- **WHEN** 明示されたQuality Loop案件で`next_role=implementer`かつ`submit-plan`または`submit-response`が要求される
- **THEN** `quality-response`だけが対象Skillとなる

#### Scenario: 一般的なレビュー依頼
- **WHEN** Quality Loop案件、case-root、またはhandoffを伴わない一般的なレビューが要求される
- **THEN** 2つのSkillはQuality Loop操作を開始せず、他のレビューSkillと競合しない

#### Scenario: Role外操作
- **WHEN** Owner裁定、自己クローズ、Reviewerによる修正、Implementerによる独立検証その他のRole外操作が要求される
- **THEN** 対応するSkillは操作を拒否し、正本を変更しない

### Requirement: 最小配置検査
配布可能性の確認は、自動テストスイートを追加または必須化せず、各Skillのfrontmatter、必要ファイル、同梱runtimeのimport、CLI実行入口の安全な起動、および想定配置構成を検査しなければならない（SHALL）。検査できない事項を成功として扱ってはならない（MUST NOT）。

#### Scenario: 最小検査が成功する
- **WHEN** 2つのSkillについてfrontmatter、必要ファイル、runtime import、CLIの`--help`、および配置構成を確認する
- **THEN** 各確認項目の成功結果と対象を記録できる

#### Scenario: 最小検査に失敗する
- **WHEN** 必須ファイル欠落、runtime不一致、import失敗、CLI起動失敗、または配置構成不整合を検出する
- **THEN** 配布可能と判定せず、失敗項目を示す

### Requirement: 利用優先のドキュメント導線
ルート`README.md`は、リポジトリの哲学や開発履歴より先に、利用者がQuality Loopを使い始めるための最短導線、2つのSkillの使い分け、および詳細手順へのリンクを提示しなければならない（SHALL）。専用デプロイガイドは、グローバル配置とローカル配置の選択、手動コピー、衝突確認、更新、最小検査、Rollback、および承認境界をコピー可能な日本語手順として提供しなければならない（SHALL）。

#### Scenario: 初見利用者がREADMEを開く
- **WHEN** Quality Loopをすぐ使いたい利用者がルート`README.md`を上から読む
- **THEN** 現在状態や設計思想の詳細より先に、配置方法、Skill選択、案件開始、詳細ガイドへの導線を確認できる

#### Scenario: グローバルへ手動配置する
- **WHEN** 利用者が複数リポジトリからSkillを利用するため専用デプロイガイドを読む
- **THEN** 対象固定、既存同名Skill確認、手動コピー、配置後検査を順番どおり実行できる

#### Scenario: 指定リポジトリへ手動配置する
- **WHEN** 利用者が一つのリポジトリだけでSkillを利用するため専用デプロイガイドを読む
- **THEN** `<repo>/.agents/skills/`への配置、グローバル配置との関係、衝突時停止を確認できる

### Requirement: 外部配置の承認境界
このChangeの実装および検証はリポジトリ内の配布元整備に限定し、`~/.agents/skills/`、他リポジトリ、その他の外部配置先へ書き込んではならない（MUST NOT）。外部配置は、実装完了、独立QA、および対象を特定した明示承認後の別工程でなければならない（SHALL）。

#### Scenario: Change実装中の配置
- **WHEN** このChangeの実装またはローカル検証を実行する
- **THEN** リポジトリ外および指定されていない他リポジトリを変更しない

#### Scenario: 外部配置の依頼
- **WHEN** 利用者が実際のグローバル配置または他リポジトリへの配置を要求する
- **THEN** 実装完了、独立QA、対象パス、および明示承認を別工程で確認する
