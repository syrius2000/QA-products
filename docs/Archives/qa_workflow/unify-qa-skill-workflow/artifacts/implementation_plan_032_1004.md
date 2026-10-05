# クラウドQAの実行検証契約を追加する改訂計画

created: 2026-10-04 17:18 (JST)
update: 2026-10-04 17:22 (JST)
author: Codex (GPT-6)

## 位置付けと判断

承認済みの[計画031](implementation_plan_031_1004.md)に、クラウドReviewerの実行検証契約を追加する改訂案である。ユーザーが提供したクラウド担当の回答によれば、対象コードを取得でき、ツール・依存関係・実行許可が揃えば、隔離環境でPythonや一般的なCLIを実行できる。ただし、この申告は当該QAでの取得・実行成功のEvidenceではない。案件ごとの実行環境確認と実測記録を必要とする。

従来の「クラウドにQA管理用runtimeを要求しない」と、製品のPythonテストを実行することは両立する。今回の改訂では管理用CLIの導入不要を保持し、対象製品の検証ツールを使う許可・必要環境・必須検証を独立した契約として明記する。

計画031のQA-F01、QA-F02、全基準継承、独立性、履歴保持、対象commitとSkillの固定は継続する。改訂部分の実装は本計画の承認後に開始する。元checkoutの既存変更と、隔離worktreeで途中まで作成した実装は保持する。

## Phase 0: QA依頼前のGit準備と監査基準点

QAスキルはレビュー依頼だけでなく、その前段にある「安全に実装を始め、後から監査できる基準点を作る」ところから支援する。Gitのクリーン状態は自動削除やresetで作らず、意図した対象変更と無関係な既存変更を識別して確保する。

1. **事前確認:** branch、HEAD、tracked・untracked・staged差分、remote、既定branch、AGENTS.md／Skill規則、関連テスト入口を読み取り専用で調べる。目的・受入基準・製品対象・実行検証・QA宛先が不足する場合は、取得済み情報を再質問せず不足分だけ尋ねる。
2. **対象境界の確定:** dirtyなcheckoutでは変更一覧と差分要約を提示し、今回QAする作業、無関係なユーザー変更、未追跡物を分類する。自動stage・stash・reset・clean・restoreは行わない。未分離の変更を安全に保てない場合は実装前に止め、ユーザーの整理、既存staged-only checkpoint、または別worktreeを案内する。
3. **Baseline checkpoint:** QA対象が既存WIPなら、選択済みの非main topic branchでユーザーが意図した対象だけをindexにstageする。`blind-qa-cycle checkpoint`はindexのパス一覧と差分を見せ、明示起動された場合だけindex限定のcheckpoint commitを作成する。unstaged／untrackedが残る、対象外パスが混在する、branchまたは対象が曖昧なら停止する。作成後にHEAD SHAとclean statusを確認してBaselineとして固定する。
4. **実装開始条件:** 対象branch、Baseline SHA、QA予定範囲、目的・基準、必須検証が記録され、対象worktreeがcleanの場合に実装へ進む。branch作成や他人の変更の退避・破棄を自動でしない。必要なら作業用worktreeを使い、元checkoutを保持する。
5. **実装後のQA引継ぎ:** 変更後にレビュー対象を明示し、unstaged／untracked／staged差分の境界を確認する。`cloud`処理ではSkillの既存手順に従いReviewed commitとinvite commitを分け、Baseline..ReviewedだけをQA対象にする。新topicへの切替や通常のQA依頼文作成だけからpushを推定しない。

人の通常関与は、開始時の目的・対象確定、実装計画の承認、終了時の残余リスク判断である。Git上のdirty状態、範囲外変更、branch不明、必須検証の不足など例外がある場合だけ、該当する判断を追加で求める。

## 現在の実装境界

- 作業場所は隔離worktreeであり、対象HEADは`ad6ca1ee196bd75bed026858c2de9586ca49c85c`である。
- `quality-loop/qa_workflow/`、追跡用の2QA Skillパッケージ、全基準照合・提出snapshot検査のコードと初期テストを作成中である。全工程・package同期・回帰検証は未完了である。
- 先行する4テストの成功記録はあるが、その後にもコードを編集したため、現在の差分全体の合格Evidenceとしては扱わない。
- GitHubへのpush、実Cloud QA、外部配置、Owner裁定は未実施である。

## 改訂する実行契約

### 依頼ごとに検証方式を固定する

コード案件では、受入基準とリポジトリの検証手順から必須の実行検証を定義する。文書だけの案件など、実行検証が必要ない場合はその理由を依頼へ記録する。「クラウドなら静的レビューだけ」という既定にはしない。

必須検証がある場合、Reviewerは環境確認と実行を試みる。取得不能や環境不足を理由に、必須検証を黙って任意へ変更してはならない。静的レビューへ切り替えて確認できた事項は保存するが、必須の実行検証が未実施なら総合PASSにしない。

### 検証項目を構造化する

各項目に安定ID、対応する受入基準ID、必須／任意、目的、必要ツールと版条件、作業DIR、argv、環境変数、timeout、期待する終了コード・確認内容、許可する書込先を持たせる。環境変数と引数は構造化した値として渡し、文字列をshellとして自動評価しない。

Reviewerの実行環境を案件ごとに観測し、OS・architecture、Python等の実際の版、依存関係の有無、取得可否を記録する。Python 3.13で成功しても、Python 3.10で試験済みと表示しない。

対象commitは完全SHAで取得・照合し、Skillと出力契約も依頼に固定された版から読む。取得できなければ別のHEAD・過去ログ・実装側のテスト結果で代用しない。

### 実行Evidenceと判定を分ける

検証項目の状態は`PASS / FAIL / NOT_RUN / ERROR`とする。各状態に実行環境、実際のargv・cwd・env、開始／終了時刻、終了コード、stdout・stderr、未実施理由または異常内容を対応付ける。生ログは許可済み保存先へ保存し、内容hashとレビューからの参照を記録する。単一Markdown契約ではログを本文へ収録する方式も可能とする。

| 観測 | 検証項目 | 総合Gateへの反映 |
|---|---|---|
| 指定版・コマンド・期待結果を満たした | PASS | 他の全基準と必須確認も満たした場合にのみPASS候補 |
| 対象製品のテストが失敗した | FAIL | 再現根拠をFindingへ記録し、総合FAIL |
| checkout不能、必要ツール・版・依存が不足 | NOT_RUN | 原因と必要な追試を記録し、総合INCONCLUSIVE |
| timeoutや検証環境の異常で結論を出せない | ERROR | 製品不具合と環境異常を区別し、総合INCONCLUSIVE |
| SHA・Skill hash・承認／出力範囲が一致しない | 実行開始を停止 | provenanceまたは契約不備としてHOLD |

既に再現した重大な製品不具合がある場合、そのFAILは別項目の未実施で消さない。必須実行不足があれば、静的確認と一部テスト成功だけから総合PASSにしない。任意検証の未実施も残余事項へ残す。

### 実行領域と成果物の書込みを区別する

Reviewerは固定SHAを取得した使い捨ての検証領域で実行する。テストfixture・temporary directory・キャッシュ等の一時生成は依頼で定めた領域へ限定し、製品変更の許可とは扱わない。実行後に製品ファイルの差分を確認する。

依存追加、ネットワーク接続、secret利用、外部サービス操作は検証依頼の許可範囲に従う。依存インストールが必要なら、固定済み依存・一時環境へのインストールが事前許可されている場合だけ実施する。リポジトリの依存定義をQA側で書き換えない。許可がなければ該当検証をNOT_RUNとして返す。

レビュー原文は独立Reviewerが作り、実装AIが補完・書換えしない。`quality-qa`の単一Markdown契約と`blind-qa-cycle`の4成果物契約を依頼ごとに明記し、同じ案件へ異なる保存契約を混在させない。ログ用の追加出力先は依頼時に予約・登録し、再QAの製品差分へ混入させない。

## このリポジトリの基本コマンド

現在のREADMEはPython標準ライブラリのunittestを検証入口としている。pytestの新規導入をこの改訂の既定条件にはしない。最初の実行契約は次の形を基本とする。

```json
{
  "id": "CHECK-001",
  "required": true,
  "criterion_ids": ["AC-001"],
  "cwd": "quality-loop",
  "argv": ["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
  "env": {"PYTHONDONTWRITEBYTECODE": "1"},
  "timeout_seconds": 300,
  "expected_exit_code": 0,
  "tool": {"name": "python", "version_constraint": ">=3.10"}
}
```

これは検証項目の例であり、実際の依頼では受入基準との対応とtimeoutを対象に合わせて固定する。他repositoryのpytest、Rscript、npm test等は、実際のrepositoryが定める検証入口・依存条件を使う。

## 変更対象と工程

1. OpenSpecのproposal/spec/design/tasksへPhase 0と実行検証契約を追加し、管理用Python不要と製品検証の実行義務を区別する。39タスクの既存項目を具体化し、Evidenceなしで完了チェックを付けない。
2. `quality-loop/qa_workflow/`のprepare/state/review/ingestへ構造化された検証項目と実行Evidence検査を追加する。既存の文字列`required_tests`入力は互換として保持し、任意の文字列を自動実行する経路にしない。
3. 追跡パッケージの両SKILL、依頼・レビューtemplate、references、machine契約、evalを更新する。Cloudは指定Skillを読み、環境確認、取得、指定検証、Evidence保存、詳細Findingとtask作成まで進める。
4. 管理runtimeはEvidenceの構造・対象・必須項目とGateの整合を検査する。JSONが整っているだけで実際の実行や独立性を証明したとは表示しない。
5. 計画031のsource/package/mirror一致、配置ガイド、既存回帰、OpenSpec strict検証と引渡しへ統合する。

## 検証する正常系・拒否系

- 固定SHAでの正常実行と、stdout・stderr・終了コードを伴う結果取込。
- テスト失敗、timeout、ツール不足、版不一致、checkout失敗、依存取得不可の区別。
- 必須検証の省略、未知check ID、重複ID、指定外argv・cwd・env、別SHAの実行、過去ログの使い回し、必須未実施とPASSの併記を拒否する。
- 任意検証の未実施は記録を残し、必須検証との混同を拒否する。
- QA-F01の全基準保持・厳密一致と、QA-F02の提出後変更拒否を新しい実行Evidence契約と組み合わせて再検証する。
- 依頼準備・状態確認がテスト実行や依存導入を勝手に開始せず、Reviewer工程だけが固定された検証契約に従うことを確認する。
- dirtyな初期checkout、対象外staged変更、unstaged/untracked、main/master、checkpoint欠落・重複をPhase 0が安全に検出し、既存変更を失わず止まるか次の手順を返す。
- clean checkpoint後にBaseline SHAを固定して実装・Reviewed範囲を区別し、QA依頼準備だけではcommit／pushを行わない。
- fixture成功、ローカル回帰、実Cloud実行、独立QA、Owner判断を別々に報告する。

## 承認と対象外

本計画は作成済み・承認待ちである。AGENTS.mdの「対象範囲、実装方式、影響範囲、変更対象が変わる場合は、計画を更新し、再承認を得る」に該当するため、実行契約・状態・結果検査を拡張する改訂部分はまだ実装しない。

承認後は計画031と本計画を併せて適用する。GitHubへのpush、PR、外部Skill配置、実クラウドQAの起動・送信、Owner裁定、元checkoutの既存差分整理は今回の実装承認に含めない。新しい外部依存の追加も含めない。
