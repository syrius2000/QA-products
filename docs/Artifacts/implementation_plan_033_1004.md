# QAループ統合計画：Phase 0から独立再QAまで

created: 2026-10-04 17:43 (JST)
update: 2026-10-05 05:24 (JST)
author: Codex (GPT-6)

## 目的と位置付け

QA依頼前のGit基準点づくりから、ローカル／クラウドQA、別AIによる独立レビュー、承認後の修正、再QA、人による終了判断までを一つの運用契約として実現する。本書を計画024〜032の内容を引き継ぐ唯一の現行計画とし、旧計画は承認後に履歴としてアーカイブする。

ユーザーは、QA依頼のたびに計画承認を挟むことで独立性と速度を損なわず、例外時だけ人が判断するQAループを希望している。QAの定型実行と成果物作成は既存AGENTS.mdの限定委任に従う。製品変更・仕様変更、Findingの処置、Owner裁定、merge、deploymentなどの独立した判断は、人の明示承認を維持する。

この計画は、承認済み計画031の未完了実装と、未承認の計画032の追加範囲をまとめ直す改訂案である。計画032で追加されたPhase 0とクラウド実行検証契約を本計画へ引き継ぐため、本計画の承認後に本書を実装境界とする。既存のdirtyなcheckout、無関係な差分、隔離worktreeの途中成果は保持する。

## 完了像

1. 実装に入る前に目的、全受入基準、対象パス、必須検証、QA方式、Git基準点を固定できる。
2. 固定SHAのQA依頼は、ローカルまたはクラウドの独立Reviewerが実施する。クラウド依頼は対象commitから固定版Skillを読む指示、全受入基準、許可出力先、検証手順を含む。
3. Reviewerが受入基準をレビュー成果物にすべて列挙し、依頼原文との集合・本文一致を検査する（QA-F01）。
4. 修正提出後の再QAは、承認済み修正の提出snapshotだけを対象とする。提出後に追加された別製品ファイルは自動採用せず、範囲拡張として停止する（QA-F02）。
5. クラウドでPython等の検証が可能な場合は、依頼に固定した検証を実行してEvidenceを保存する。不能時は理由を記録し、必須項目が未実施なら総合PASSにしない。
6. 実施側は、固定されたFinding・根拠・タスクを受け取り、別途承認された範囲だけを修正する。実施側はReviewerの記録を選別・書換えしない。
7. 独立再QAの結果、実行Evidence、未検証項目、残余リスクを追跡可能な状態で提示し、人が残余リスク・受入・終了を裁定する。

## 一本化した運用フロー

### Phase 0 — QA依頼前の基準点づくり

- branch、HEAD、tracked／untracked／staged差分、remote情報、AGENTS.md・Skill規則、関連検証入口を読み取り専用で確認する。
- 目的、全受入基準、製品対象、必須／任意検証、QA方式・宛先を整理する。取得済み情報は聞き直さず、不足・曖昧な点だけを人へ尋ねる。
- dirty checkoutは自動でcleanにしない。今回対象、無関係な既存変更、未追跡物を分類し、自動stage・stash・reset・clean・restoreを禁止する。
- 対象WIPをGitで監査する必要がある場合、既存の非main topic branch上で対象パスだけを選び、`blind-qa-cycle checkpoint`のstaged-only手順でbaseline commitを作る。対象外staged変更、unstaged／untracked混在、branch不明、共有基点の不明があれば止まり、整理方法を提示する。
- 実装開始前に、対象branch、baseline SHA、目的、全受入基準、対象範囲、必須検証を記録する。作業treeは独立・cleanなものを使い、基準点からの差分を監査可能にする。

### Phase 1 — 変更・QA対象の固定

- 実装作業は承認済み計画・仕様・対象範囲に限る。対象範囲または方式の変更が必要なら、計画を更新し再承認を得る。
- QA依頼時にbaseline SHA、reviewed SHA、対象差分、全受入基準、QA Skill／出力契約の識別情報、書込み許可pathを固定する。
- 明示されたクラウドQA依頼の事前委任は、AGENTS.md記載の固定差分QAと必要なQA公開・依頼packet作成に限る。branch衝突、remote不整合、機密・個人パス、範囲外path、検証失敗・不明があれば公開せず人へ戻す。

### Phase 2 — 独立レビューと検証

- Reviewerには自己完結した依頼を渡し、対象commit内の指定Skillと手順を読ませる。対象SHAまたはSkill・契約のhashを確認できなければHOLD相当とする。
- QA依頼は全受入基準を順序付きで保持する。レビュー成果物は基準ごとにID・原文・判定・根拠を持ち、欠落・追加・改変を依頼と照合する。
- 実行契約は必須／任意、argv、cwd、環境、timeout、前提を対象ごとに固定する。実行時は実際の環境・コマンド・終了code・stdout／stderr・時刻を記録する。製品検証に必要なPython等のツールは使える範囲で実行し、QA管理CLI導入の要否とは分ける。
- 必須検証のNOT_RUN／ERROR、取得不能、環境不足は成功扱いにしない。PASS／FAIL／INCONCLUSIVE／HOLDを区別し、任意検証の未実施も残す。
- Reviewerは独自にFindingの根拠を記録し、実施AIはFindingの作成・判定・削除を操作しない。単一の許可Markdown内にレビュー、監査記録、実施側タスクリストを含める契約を維持する。

### Phase 3 — 結果確認・修正計画・承認

- ローカル側はSHA、全受入基準、FindingとEvidence、検証ログ、許可出力path、STATUSの整合を機械確認する。欠落・矛盾時はQA完了扱いにせず確認待ちとする。
- 実施側はFindingごとに対応・反証案、対象path、完了条件、検証方法を提案する。製品コード・仕様の修正は、修正計画と対象範囲を人が明示承認してから行う。
- 承認時に修正対象path集合と期待snapshotを固定する。

### Phase 4 — 提出・独立再QA

- 修正提出時に承認済みpath、提出snapshot、commit/SHA、Evidenceを関連付ける。
- 再QAの対象は提出済みsnapshotと、初回QAからの差分に限定する。提出後の別製品ファイル変更・追加を新snapshotへ取り込まない。範囲外変更を見つけたら停止し、再承認または新規QA依頼へ戻す。
- 再QAも別Reviewerが同じ全受入基準を照合し、修正Findingごとに解消・未解消・未検証を根拠付きで記録する。実装者側テスト成功は独立QAを代替しない。

### Phase 5 — 人による最終判断

- 通常時の人の関与は、開始時の目的・対象・受入基準確定、製品修正計画の承認、最後の残余リスク・受入・終了判断とする。
- 範囲不明、基準変更、Git競合、機密情報、必須検証不能、重大Finding、判定矛盾など例外時だけ、該当する判断へ人を呼び戻す。
- QAの技術判定とOwnerの受入・リスク裁定を混同しない。commit・push・merge・外部配置・deploymentは、AGENTS.mdの委任範囲を越える場合に別途明示承認を得る。

## 実装・検証対象

- 正本: `openspec/changes/unify-qa-skill-workflow/`のproposal/spec/design/tasksと、必要な正本Spec・機能仕様。
- 追跡配布物: `quality-loop/skills/quality-qa/`、`quality-loop/skills/blind-qa-cycle/`、`quality-loop/qa_workflow/`、README／配布説明、同期dry-run定義。
- 管理runtime・テスト・eval: 全基準照合、提出snapshot境界、Git authorization、Cloud実行Evidence、クラウド成果物、ローカル結果回収、再QAの受入／拒否fixture。
- Phase 0: dirty checkoutの検出と分類、staged-only checkpoint前提、対象外変更保持、main/master拒否、baseline記録、独立worktree開始条件。
- QA-F01: 基準欠落・重複・改変・余計な基準、指紋同一でも本文不一致、複数形式、レビュー判定とEvidenceの対応。
- QA-F02: 複数製品pathの承認集合、提出snapshot固定、提出後の別path変更、path追加・改名、別SHA、範囲外変更拒否。
- Cloud実行: 固定SHA・Skill hash・check ID、必須項目省略、argv/cwd/env逸脱、古いログ、pass誤判定、必須未実施の総合判定。
- 既存回帰、OpenSpec strict validation、パッケージ完全性・同期dry-run、Markdown相対リンクを検証する。実Cloud再QA、Python版・特定OSでの実機確認はfixture／ローカルテストと区別して記録する。

## 現在地・作業保全

- 開発用隔離worktree: このリポジトリの専用worktree。計画031に基づく途中実装を保持して引き継いだ。実装開始HEADは`ad6ca1ee196bd75bed026858c2de9586ca49c85c`で、開始時点の差分・hash・テスト状態を[実装baseline](qa_implementation_baseline_001_1004.md)に固定した。
- 元checkoutには作業前から多数の削除・未追跡Artifact・OpenSpec変更があり、`AGENTS.md`にも変更がある。今回の計画作成ではそれらを変更していない。clean/reset/stash/restore、元checkoutへの実装、未追跡ファイルの整理を行わない。
- 計画031の既存承認で始めた隔離worktree作業と計画032の追加契約を照合し、既存作業を壊さず本書に適合させる。仕様追加または既存承認範囲との矛盾があれば、その箇所を分離して再承認を求める。
- GitHubへのpush、PR、実Cloud QAの発行、merge、外部Skill配置、Owner裁定は本計画の実装対象外とする。ただしAGENTS.mdの限定委任範囲内のQA公開は、実装完了後の独立QA依頼段階で別途扱う。

## 完了条件

- Phase 0から終了判断までの契約と各AI・人の責務が、Skill、OpenSpec、runtime、Artifact間で一致する。
- QA-F01／F02とPhase 0、クラウド実行検証の正常・拒否系が自動テストとEvalsで確認される。
- 全受入基準の保存・照合、提出snapshot境界、必須検証のEvidenceと総合判定が機械・独立Reviewerの両方で追跡できる。
- 関連回帰・OpenSpec strict validation・リンク・パッケージ整合が完了し、未実施のCloud／OS／Python環境は明示的に`unverified`で残る。
- 独立QAの技術判定、Ownerの最終裁定、外部公開等の状態を混同しない。

## 計画書の所在（2026-10-05 対象SHA照合後の訂正）

以前の記録は計画024〜032の9文書すべてを`docs/Archives/qa_workflow/plans/`へ移動し、復元可能と述べていた。しかしQA-003 Reviewed SHA `d9bad5c125791306e38bca8830b4082f7f38fc6b`のGit treeにはそのディレクトリがなく、記録と実体は一致しない。計画024〜028は対象treeで原文・退避先とも確認できず、計画029・030・032は`docs/Artifacts/`直下に存在する。計画031も同所に存在するが、統合履歴に記録された原文hashとは一致しない。所在不明分の復元可能性は未検証である。

| 計画 | 対象SHAで確認した状態 |
|---|---|
| 024〜028 | 原文・記載された退避先とも対象treeに存在しない。復元未検証。 |
| 029、030、032 | `docs/Artifacts/`直下にあり、統合履歴の記録hashと一致。Archiveへの移動は確認できない。 |
| 031 | `docs/Artifacts/`直下にあるが、統合履歴の記録hashと不一致。原文同一性・復元可否は未検証。 |

リンク検査で見つかった欠落参照は個別に修正する。履歴文書の記述だけから原文の退避・復元可能性を断定しない。`AGENTS.md`、Skill、runtime、OpenSpecの実装ファイルの移動有無はこの訂正対象外である。

## 承認ゲート

計画033はユーザーが明示承認し、隔離worktreeで実装中である。OpenSpecタスク39項目中11項目がEvidence付きで完了。全テスト150件と30 subtests、配布runtimeテスト23件と5 subtests、OpenSpec strict、Skill一時配置、runtime同期、9文書リンク検査が成功した。実装・統合fixtureの残項目、Python 3.10実行、独立QA、Owner裁定は未完了であり、進捗と制限は[実装報告](implementation_report_001_1004.md)に記録した。2026-10-04、ユーザーがcommit・pushを明示指示した。公開先は新規topic branch `codex/unify-qa-skill-workflow` に限定し、既定branchへのpush・PR・merge・外部配置・削除は含めない。
