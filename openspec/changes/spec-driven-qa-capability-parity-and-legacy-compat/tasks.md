# QA機能完全互換性とLegacy互換性の実装タスク

created: 2026-08-27 00:12 (JST)
update: 2026-08-27 05:20 (JST)
author: Codex (GPT-5)

## 1. 三版Bundleと実行境界の固定

- [x] 1.1 Legacy Reviewer／Author、Contract v1.2候補、compactの入力ルートを明示し、各BundleのManifest・SHA-256・版識別子を保存して相互参照が混入しないことを確認する
- [x] 1.2 各Bundleを読み取り専用基準として扱う比較ハーネスの版選択を実装し、存在しない版・Manifest不一致・digest不一致で非ゼロ終了することを確認する
- [x] 1.3 実行前後のキャッシュ、`.pyc`、`__pycache__`、シンボリックリンクによるBundle外参照を検査し、混入時に比較を停止するテストを通す

## 2. 公開機能台帳の作成

- [x] 2.1 旧130ファイルを棚卸しし、Reviewer／Authorの公開または実行可能な入口を43機能IDへ対応付け、Legacy互換24件と新規Contract機能19件を区別した入口・役割・版・Evidence列を持つ台帳を保存する
- [x] 2.2 各機能IDへ引数、期待終了コード、JSON必須項目、状態変化、副作用、比較クラスを記録し、台帳スキーマの構造検証を通す
- [x] 2.3 台帳とLegacy Bundleの公開入口を双方向照合し、Legacy互換24件の欠落・未登録入口・重複ID・根拠のない43件との差異をエラーとして報告するテストを通す。新規19件のLegacy不在はエラーではなく明示的な新規分類とする

## 3. 共通fixtureと比較ハーネス

- [x] 3.1 機能台帳の全比較クラスに対応するgolden、negative、cross-skill、Legacy互換、サイズ計測fixtureを作成し、fixture一覧と機能IDの対応検証を通す
- [x] 3.2 同一fixtureを三版へ投入し、入力、stdout、stderr、終了コード、構造化出力、状態、副作用スナップショットを版別Runディレクトリへ保存する
- [x] 3.3 Reviewerの独立判定とAuthorの提出・検証を連続利用するcross-skill fixtureを実行し、版ごとのhandoff、submission、digest、revisionの受け渡しと適用可能性を比較Evidenceで確認する
  - `stage/cross_skill.py` が三版の連鎖結果を分離保存し、Candidateとcompactはhandoff、submission、digest、revisionを観測済み。Legacyはhandoff・Author回答まで観測できるが後発のsubmission・digest・revision契約がないため、`intentional-noncompatibility`として分離記録した。Legacy完全互換の合格には集約していない。

## 4. 互換性と差分判定

- [x] 4.1 旧CLI引数、終了コード、JSON必須項目、契約フィールド、旧QAケースの読み取り互換を機能ID単位で比較し、合格・不合格・未検証を構造化出力する
  - `stage/diff_classifier.py` が機能台帳、Bundle Manifest、Run Evidenceを読み、機能ID単位の比較結果を`stage/evidence/compatibility-report.json`へ保存する。機能ID単位の契約突合が未定義の場合は`missing-or-unverified`として保持する。
- [x] 4.2 Candidate／compactの差分を「未実装・欠落」「仕様上の意図的非互換」「診断文・表示形式のみ」に分類し、各非互換へ仕様・理由・Evidenceが必要なことをnegativeテストで確認する
  - `compatible`、`intentional-noncompatibility`、`presentation-only`、`missing-or-unverified`の4分類と、仕様・理由・Evidence参照を必須とする判断データを追加した。未知分類は拒否される。
- [x] 4.3 Legacyと安全契約が衝突するケースを実行し、Candidate／compactが安全契約を優先しつつ意図的非互換として記録することを確認する
  - Legacyの連鎖契約欠落を`stage/evidence/compatibility-decisions.json`へ記録し、Candidate／compactの拒否境界を`stage/evidence/safety-regression.json`で確認した。Legacyの安全でない挙動をCandidate／compactの合格条件にはしていない。
- [x] 4.4 未分類差分または未説明の欠落が1件でもある場合、全体互換性を合格に集約しない終了コードとレポートを確認する
  - `missing-or-unverified`を含む場合は全体`evidence-gap`、CLI終了コード2となることをテストで確認した。

## 5. 既存安全契約の回帰検証

- [ ] 5.1 各版に存在する契約について、自己クローズ、Reviewer正本書込み、未知Finding、空または欠落Evidence、Workspace外パスの拒否をCandidate／compactで実行し、正本無変更と非ゼロ終了を確認する。版に契約がない項目は`not-applicable`または`evidence-gap`として記録し、合格扱いにしない
  - `stage/evidence/candidate-contract-probe.json`でCandidateが空Evidenceを受理する観測違反（expected reject / actual accept）を固定し、`contract-applicability.json`ではLegacyの後発契約不在を`not-applicable`として分離した。Candidate修正または人間裁定が残るため未完了とする。
- [x] 5.2 各版に存在するdigest契約について、staleなsemantic/content digest、旧同値digest、未知digest versionを投入し、提出拒否・再生成要求・正本無更新を確認する。版に契約がない項目は非互換または`evidence-gap`として分離する
  - Candidateの実在semantic digestに対するstale拒否を`candidate-digest-probe.json`でObserved確認し、content digest／digest versionは`not-applicable`として分離した。compactの分離digest・未知version・旧同値digest、Legacyの契約不在も分離記録した。Lunaがfixed-and-verifiedを確認した。
- [x] 5.3 QA-0006のAuthor提出境界とQA-0007のdigest分離プローブを回帰fixtureへ取り込み、既存Evidenceと同じ境界結果になることを確認する
  - `stage/fixtures/contract-regression.json`へ両QAの参照と期待チェックを登録し、`stage/evidence/safety-regression.json`で全回帰ケースをObserved確認した。

## 6. Evidenceと複数Agent集計

- [ ] 6.1 各Agent／RunにPrompt、出力、条件、開始終了時刻、実行件数、Bundle digest、結果、未実行項目を保存し、manifestとresultsの整合性を検証する
  - `stage/agent_aggregator.py` は5 Agent／Runを識別子単位で分離し、manifest/resultsの識別子整合性を検証した。ただしAgentごとにmanifest形式とPrompt・出力の保存粒度が異なり、必須項目の全件充足は未検証のため未完了とする。
- [x] 6.2 複数AIの結果を別Runとして集計し、Agent・モデル・設定・Prompt suiteを混同しない集計レポートを生成するテストを通す
  - 5 Agent／Runを`stage/evidence/agent-aggregate.json`へ別エントリとして集計し、識別子不一致・重複・入れ子results形式をテストした。
- [x] 6.3 Token、Latency、外部LLM正答率が取得不能な場合に`unverified`または`evidence-gap`を維持し、推定値をObservedへ変換しないことを確認する
  - 集計レポートは全AgentのToken・Latencyを`unverified`として保持し、フェルミ推定値による補完を行わない。未取得状態を確認するテストを通した。
- [x] 6.4 Evidenceおよびdigest入力の秘密値を検出し、保存・集計を拒否または安全な欠測状態へ遷移させるテストを通す
  - 秘密値検出時に集計を`evidence-gap`へ遷移させ、検出値をレポートへ保存しないテストを通した。安全回帰レポートのsecret policyとも整合する。

## 7. サイズ、総合判定、独立QA

- [x] 7.1 Bundle別のファイル数・行数・バイト数を決定論的に計測し、1,760行以下の目安と安全機能・テスト・仕様を削っていないことを同時にレポートする
  - `stage/measure_size.py` によりLegacy 3,407行／Candidate 5,953行／compact 878行を実測し、compactの目安内と必須安全機能・仕様・テストの存在を`stage/evidence/size-report.json`へ保存した。
- [x] 7.2 G0からG2の自動検証結果を統合し、未検証・欠落・意図的非互換・残余リスクを分離した総合レポートを保存する
  - `stage/overall_report.py` がBundle境界、互換性、安全回帰、契約適用可能性、Agent集計、サイズ、cross-skillを統合した。全体は`evidence-gap`、意思決定は`human-adjudication-required`、外部配備は不許可としている。
- [x] 7.3 Reviewerによる独立QAを実施し、機能台帳、三版比較、差分分類、安全境界、Evidence隔離を`docs/ADR/QA/`へ記録する
  - 別コンテキストのLunaサブエージェントが読み取り専用レビューを実施し、`docs/ADR/QA/QA-0008-spec-driven-qa-capability-parity/cycles/cycle-01-independent-review.md`へ記録した。5件の未解決Findingを人間裁定へ送った。
- [x] 7.4 人間裁定用に未解決Finding、`unverified`、`evidence-gap`、意図的非互換、残余リスク、配備可否を明示したhandoffを作成する
  - `docs/ADR/QA/QA-0008-spec-driven-qa-capability-parity/handoff.md` にF01〜F05、残余リスク、配備不可、裁定事項を記録した。
- [x] 7.5 独立QAと人間裁定が完了するまで外部Skill配置、旧版削除、commit、pushを行っていないことを確認し、OpenSpec検証と実装完了報告を分離する
  - Cycle 4の独立検証とCycle 5の人間裁定で、外部Skill配置、Legacy削除、commit、pushが未実施であることを確認した。QA-0008は`closed / accepted-with-residual-risk`だが、外部配備は別Changeと明示承認が必要である。
