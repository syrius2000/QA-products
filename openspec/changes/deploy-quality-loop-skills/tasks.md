## 1. 実装境界と配布対象の固定

- [x] 1.1 `docs/Artifacts/implementation_plan_NNN_MMDD.md`に対象、方式、非対象、検証、Rollback境界を日本語で記録し、コード変更前に明示承認を得たことを確認する
- [x] 1.2 `quality-loop/quality_loop/`のPythonソース相対パスとSHA-256を記録し、`__pycache__`、`.pyc`、テストキャッシュを配布対象外として識別できることを確認する
- [x] 1.3 変更前の`quality-review`と`quality-response`のファイル一覧、frontmatter、CLI呼出し記述を記録し、既存差分を実装変更と区別できることを確認する

## 2. 自己完結runtimeとCLI実行入口

- [x] 2.1 `quality-review/runtime/quality_loop/`へ開発正本のPythonソース全体を同梱し、相対パスとSHA-256が正本と一致し生成物が含まれないことを確認する
- [x] 2.2 `quality-response/runtime/quality_loop/`へ開発正本のPythonソース全体を同梱し、相対パスとSHA-256が正本および`quality-review`同梱runtimeと一致することを確認する
- [x] 2.3 `quality-review/bin/quality-review-cli`を追加し、Skill配置場所からruntimeを解決して引数を変更せず`quality_loop.cli`へ渡すことを、開発元Bundleルート外からのimportと`--help`で確認する
- [x] 2.4 `quality-response/bin/quality-response-cli`を追加し、Skill配置場所からruntimeを解決して引数を変更せず`quality_loop.cli`へ渡すことを、開発元Bundleルート外からのimportと`--help`で確認する

## 3. Skill発火境界と実行手順

- [x] 3.1 `quality-review/SKILL.md`のdescriptionと本文をReviewer Role、明示案件、対象4操作に限定し、一般レビュー、OpenSpec一般、他QA、実装、回答代筆、Owner裁定、自己クローズが非発火または拒否対象として読めることを確認する
- [x] 3.2 `quality-response/SKILL.md`のdescriptionと本文をImplementer Role、明示案件、対象2操作に限定し、一般回答、OpenSpec一般、他QA、レビュー、独立検証、Owner裁定、自己クローズが非発火または拒否対象として読めることを確認する
- [x] 3.3 両SkillのCLI例を同梱ラッパー経由へ変更し、開発元`quality-loop/`への`cd`、import path、相対参照を要求していないことを検索で確認する
- [x] 3.4 両Skillのfrontmatterを構文確認し、Skill名が維持され、正の発火条件と負の非発火条件が相互排他的に記載されていることを確認する

## 4. 配置・更新・衝突時の手順

- [x] 4.1 グローバル配置先`~/.agents/skills/<skill-name>/`とローカル配置先`<repo>/.agents/skills/<skill-name>/`へのコピー手順を日本語で記載し、リポジトリ外リンクは絶対パス、リポジトリ内リンクは相対パスであることを確認する
- [x] 4.2 配置前の対象固定、ファイル一覧・SHA-256比較、不存在時の新規コピー、同一時のスキップ、差異時の停止を記載し、自動上書き・暗黙の削除・未承認Rollbackを含まないことを確認する
- [x] 4.3 開発正本から2つの同梱runtimeを手動更新する手順と最小配置検査を記載し、インストーラー、同期CLI、npm、PyPI、pipxを前提としていないことを確認する
- [x] 4.4 グローバルとローカルの同時配置時はローカル優先を運用契約として明記し、実環境で優先順位を確認できない場合は`unverified`として扱うことを確認する
- [x] 4.5 `quality-loop/SKILL_DEPLOYMENT_GUIDE.md`にグローバル／ローカル選択、衝突確認、手動コピー、更新、最小検査、Rollbackを番号付き日本語手順で記載し、コピー可能なコマンドと期待結果が揃うことを確認する
- [x] 4.6 ルート`README.md`を利用開始、Skill選択、案件開始、現在状態、設計思想、評価・開発情報の順へ再編し、既存の現行情報と正本リンクを失っていないことを確認する

## 5. リポジトリ内最小検査とEvidence

- [x] 5.1 2つのSkillについてfrontmatter、必須ファイル、runtime import、ラッパーの`--help`、想定配置構成を検査し、項目別結果を記録する
- [x] 5.2 開発正本と両同梱runtimeのPythonソース一覧・SHA-256を比較し、不一致、欠落、余分な生成物が0件であることを記録する
- [x] 5.3 自動テストスイートおよび実案件E2Eを実行していないこと、未検証事項を`unverified`または`evidence-gap`として実装報告に明記する
- [x] 5.4 編集ラウンド終了時の`git diff`で変更が承認対象内に限定され、`~/.agents/skills/`、他リポジトリ、旧版、commit、pushを変更していないことを確認する
- [x] 5.5 ルートREADMEから専用デプロイガイド、Quality Loop README、機能仕様、Templateへ相対リンクで到達でき、ガイド内コマンドが承認境界を越えないことを確認する

## 6. 独立QAと外部配置ゲート

- [x] 6.1 独立QAで仕様追跡、自己完結性、runtime一致、誤発火防止、衝突時停止、READMEとデプロイガイドの利用導線、最小検査Evidenceを確認し、未検証事項と残余リスクを記録する
- [x] 6.2 Ownerが独立QA結果と残余リスクを裁定し、外部配置可否を実装完了とは別に記録したことを確認する
- [x] 6.3 外部配置を行う場合は別工程で対象パスと配置内容の明示承認を取得し、このChangeの実装または検証中には配置、旧版削除、commit、pushを行っていないことを確認する
