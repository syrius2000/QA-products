## 1. 対象と共有契約の固定

- [x] 1.1 Reviewer lifecycleのhandoff、digest、revision、Write Allowlistを参照するAdapter境界を固定し、既存Reviewerテストが変更なしで通ることを確認する
- [x] 1.2 Author入口と提出先のstageディレクトリを作成し、Manifestに対象ファイルだけが含まれることを検証する

## 2. Author回答とsubmission

- [x] 2.1 handoffから対象Findingと契約versionを読み取り、Finding別Dispositionと根拠を保持するsubmission形式を実装し、accepted回答のgoldenテストを通す
- [x] 2.2 `submission_id`、`base_revision`、digest、Evidence、`modified_files`を出力し、再読み込み可能な構造化形式であることをテストする
- [x] 2.3 accepted、fix-submitted、rejected-with-evidence、deferred、risk-acceptedのDispositionを検証し、無効値を拒否するnegativeテストを追加する

## 3. 契約整合性とEvidence検証

- [x] 3.1 handoffのsemantic/content digestを正本から再計算して照合し、stale digestを正本非更新で拒否するテストを通す
- [x] 3.2 base revisionとFinding IDを検証し、未知Findingまたはrevision競合を拒否するnegativeテストを通す
- [x] 3.3 相対Evidenceの存在、絶対パス、`file://`、Workspace外解決を検証し、欠落参照を拒否するテストを通す
- [x] 3.4 技術修正提出の`modified_files`を必須化し、空・欠落・不存在・symlink脱出を拒否するテストを通す

## 4. 権限境界と依存欠落

- [x] 4.1 AuthorのWrite Allowlistを提出先に限定し、review、findings、handoff、events、closureへの書込みを拒否するテストを通す
- [x] 4.2 Authorによる`closed`または`fixed-and-verified`の自己設定を拒否し、Reviewer検証待ち状態を返すテストを通す
- [x] 4.3 PyYAML等の任意依存がない標準ライブラリ環境で検証を実行し、安全なフォールバックまたは明示的非成功結果を確認する

## 5. Skill入口と実例

- [x] 5.1 `spec-driven-qa-author-response-submission`のSkill入口を作成し、Authorの役割、handoff入力、許可提出先、Reviewerへの返却手順を明記する
- [x] 5.2 正常系・拒否系・依存欠落を含む最小完全fixtureを作成し、CLIまたはSkill実行例から再現できることを確認する
- [x] 5.3 旧版SkillやReviewer正本を変更せず、stage Bundleのファイル数・サイズ・Manifestを計測する

## 6. QAと完了境界

- [x] 6.1 Author側の全テストとReviewer側の回帰テストをキャッシュなしで実行し、全件合格のログを保存する
- [ ] 6.2 別Agentによる独立QAでAuthorの自己クローズ、未知Finding、stale digest、Evidence境界を検証し、結果を`docs/ADR/QA/`へ保存する
- [x] 6.3 不明なLLM実測値、外部Skill配備後の動作、Git revisionなどは`unverified`／`evidence-gap`として記録し、根拠なく完了扱いにしない
- [x] 6.4 外部Skill配置、旧版削除、commit、pushを行わずにstage完了を確認し、本番配備は別Changeへ引き継ぐ
