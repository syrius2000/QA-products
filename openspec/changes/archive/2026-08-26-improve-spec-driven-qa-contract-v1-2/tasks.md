# Spec-Driven QA Contract v1.2 実装タスク

## 1. 基準化とステージング

- [x] 1.1 現行Reviewer SkillとAuthor Response SkillのMANIFEST、Schema、Template、Script、Test、Exampleを棚卸しし、ステージング対象一覧と既存差分を記録する
- [x] 1.2 ReviewerとAuthorの共有処理を固有namespaceへ分離し、同一pytestプロセスとsubprocessの両方でimport衝突が起きないことを確認する
- [x] 1.3 QA正本、handoff、Author提出物のContract v1.2用ディレクトリ構成を作成し、Manifestがcache・bytecodeを含まないことを確認する

## 2. ContractとSchema

- [x] 2.1 `contract_version`、`case_status`、`next_action`、`case_revision`、Finding内状態、terminal resultのSchemaを定義し、正常系と不正状態のSchema検証を通す
- [x] 2.2 `semantic_digest`対象フィールドをキー順固定JSONへ変換する正規化仕様として定義し、同一意味データが同一digestになるfixtureを通す
- [x] 2.3 `content_digest`、`expected_semantic_digest`、`case_revision`の鮮度・競合契約を定義し、意味変更と内容だけの変更を区別するfixtureを通す
- [x] 2.4 Evidenceの要求・実体・検証者・取得時点・結果・参照種別・秘密値マスクのSchemaを定義し、`unverified`と`evidence-gap`を成功と区別できることを確認する
- [x] 2.5 旧v1.0/v1.1読み取りadapterと未知major version停止条件を定義し、履歴を書き換えない互換fixtureを通す

## 3. Reviewer側の正本・handoff・状態遷移

- [x] 3.1 Reviewer正本から`handoff.md`を生成するRendererを改修し、Authorが直接編集したhandoffをValidatorが拒否することを確認する
- [x] 3.2 handoff Validatorに契約version、対象Finding、権限、revision、semantic/content digest、要求Evidenceの突合を実装し、stale・改ざんfixtureを拒否する
- [x] 3.3 ケース直下の最小永続状態とFinding内状態からworkflow phase・terminal resultを導出する遷移Validatorを実装し、不正組合せを拒否する
- [x] 3.4 `risk-accepted`、`evidence-gap`、`deferred`、`not-reproducible`の終了記録とOwner・根拠・再レビュー条件を検証する
- [x] 3.5 `lite` 1、標準2、`strict` 3のcycle上限を実装し、上限到達時に自動クローズせず最終リスク評価へ遷移することを確認する
- [x] 3.6 `accept_author_submission`相当のReviewer統合Validatorを実装し、submission hash、base revision、対象Finding、Evidence整合性を検証してから正本候補を生成する

## 4. Author側の提出と権限

- [x] 4.1 Author Validatorをhandoff公開契約基準へ改修し、未知Finding、未許可実装、欠落revision、未回答Findingを拒否するfixtureを通す
- [x] 4.2 `submission_id`単位のAuthor提出形式と書込み許可リストを実装し、受理済み提出物の変更と同一ID再提出を拒否する
- [x] 4.3 AuthorがReviewer正本のFinding、severity、verification、events、closureを変更できないことをnegative testで確認する
- [x] 4.4 実行許可式、repository policy、user authorization、handoff permission、Fast Path適格条件を実装し、Low適格・Medium拒否・範囲外拒否を検証する

## 5. CLI・OpenSpec・リンク・セキュリティ

- [x] 5.1 探索・検証・handoff生成Scriptに`--json`を追加し、共通必須フィールド、stdout/stderr分離、statusとexit codeの対応をfixtureで確認する
- [x] 5.2 `--openspec-change`指定のbaseline収集を実装し、指定Changeの実パス・revision・digestを記録し、task完了や`valid: true`を実装Evidenceにしないことを確認する
- [x] 5.3 リポジトリ内リンクの相対パス強制、`file://`拒否、外部参照の明示をValidatorで確認する
- [x] 5.4 Evidenceの秘密値検出・マスク・参照拒否を実装し、秘密値をJSON、event、handoffへ出力しないfixtureを通す

## 6. Bundle評価と配備準備

- [x] 6.1 固定fixtureの`run_evals.py`を作成し、正常系、negative、競合、cross-skill、旧Contract、Fast Path、Evidence gapを一括実行できることを確認する
- [x] 6.2 Bundle ValidatorへManifest、構文、Schema、Reviewer/Author単体、統合、E2E、`run_evals.py`全件合格を必須ゲートとして組み込む
- [ ] 6.3 旧版と同一promptで比較し、重大な誤実装開始、自己クローズ、未知Finding受理が0件で、正答率・所要時間・token量・追加質問数を記録する
- [x] 6.4 stageからのdry-run、差分表示、backup、rollback手順を作成し、既存Skillへ変更を加えずに再現できることを確認する
- [x] 6.5 実装結果、評価結果、残余リスク、配備差分をChange Evidenceへ記録し、明示承認がなければグローバルSkillへ配備しないことを確認する
