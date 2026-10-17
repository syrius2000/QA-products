# spec-review r2: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-5.1）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `be2fca6b7266d808a6333898e2ad37a199829290`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: Findingの停滞

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:1に各項目を定義。tests/test_schema_contract.py:36、42、63に正常・欠落・重複の検査がある。python3 -Bによるメモリ上の検査でも正常例は適合、criteria欠落とID重複は拒否された。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:7以降に読取り専用、原文・順序、根拠、提案、再判定の各契約がある。tests/test_schema_contract.py:85でスキーマ項目・Gateとの対応を検査している。契約文書の整備は確認できるが、原文照合の実装にはF-001が残る。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:34、88に抽出処理、tests/test_criteria.py:16以降にarchive済み4件の期待件数と原文照合がある。読取り専用の再抽出で順に37/25、5/5、15/18、11/23件を確認し、期待件数と一致した。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:44、64でチェック状態を含めず本文を組み立て、21、179、210でSHA-256と差分を計算する。tests/test_criteria.py:67、77に状態変更と1文字変更の回帰検査がある。本roundの43基準を再抽出し、指定指紋との一致とドリフトなしを確認した。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:75、78、97でbranch・dirty検査とbase記録を実施。gitops.py:80以降で報告必須・未stage拒否・trailerを実装。tests/test_gitops.py:19、27、39、46、60に対応する正常・拒否テストがある。提示されたCHK-PYTESTもPASS。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101でcontextmanagerを定義し、finallyでworktree remove・prune・一時ディレクトリ削除を行う。tests/test_gitops.py:76、86が成功・失敗・timeout・例外後のworktree削除を検査する。 |
| T-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30、82に前提検査・dry-run・バックアップ・tree検証・復元を実装。gitops.py:165でreset --softを使う。tests/test_gitops.py:101、119、129、139、147、191に正常系・拒否系・tree不一致・commit失敗の検査がある。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:116で対象refと到達不能候補を返し、confirmなしでは削除しない。render.py:95で確認用に表示。tests/test_gitops.py:178で確認前のref保持と確認後の削除を検査する。 |
| T-4.1 | PASS | openspec/changes/add-spec-review-loop/design.md:145以降にOpen Questionの解消と3 CLIの版・フラグ・出力取得方法を記載。runtime/spec_review_loop/reviewers.py:33、76以降のアダプタとprobeが対応する。evidence/sandbox-add-slugify-codex/r2_review.jsonとevidence/sandbox-add-slugify-cursor/r2_review.jsonにも実機のReviewer情報と判定が保存されている。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:25、33、144に共通インタフェースと3経路、cli.py:54にdoctorがある。tests/test_reviewers.py:23で3アダプタをパラメータ化検査し、62、68で未導入・フラグ不足を検査する。 |
| T-5.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:41がtextをstripして比較するため、原文の前後に空白・改行を追加しても構造検証を通過する。保存済みレビューのT-1.1だけをメモリ上で変更してstructural_errorsを呼ぶと([], [])となった。tests/test_schema_contract.py:80以降もこの改変を許容している。F-001は未解消。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:109以降でPASS・HOLD・停滞・上限を判定する。tests/test_gate.py:143、150、161、175が2 round目PASS、同一Finding未解消、3 round上限、件数非減少を検査する。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:14、44で両Markdownを生成し、基準表・Gate・Finding・提案・Reviewer・SHAを出力する。tests/test_report.py:16に内容検査がある。summaryの最終レビュー失敗時の引継ぎもreport.py:62以降とtests/test_gitops.py:218で追加され、メモリ上の生成で前roundの6件を保持することを確認した。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1から同梱runtimeを起動する。runtime/spec_review_loop/cli.py:18、65、88に全サブコマンド・dispatch・終了コード処理がある。tests/test_cli.py:9、18、47、56、63、69に正常系と終了コード2・3・4の検査がある。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4のdescriptionに適用範囲・明示例・非発火例があり、13以降に既存経路との使い分け、各round手順、停止時の引継ぎを記載。tests/test_skill.py:13、21に対応検査がある。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:1を読み取り、activation_casesに起動3件・非起動4件を確認した。tests/test_skill.py:28でも件数・ID一意性・期待値の型を検査している。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:11が偽ReviewerでFAIL→PASS→finishを実行する。35以降で2 commitから1 commitへの集約、バックアップとのtree一致、summary内の両SHAとGate、trailer、clean状態を検査する。提示されたCHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/r1_review.jsonとr2_review.jsonを読み、codex-cli 0.160.1／gpt-6-luna、FAIL→PASSを確認した。同ディレクトリのsummary.md:12以降に両roundのSHAとGate推移、squash_commit.txt:1以降にsquashのtrailerが保存されている。実装報告だけでなく保存されたレビューJSONと要約を照合した。 |
| T-7.3 | PASS | git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac be2fca6b7266d808a6333898e2ad37a199829290で、追加対象changeとquality-loop/skills/spec-review-loop配下のみであることを確認した。既存QA Skill・記録の変更はない。提示されたCHK-VALIDATEはPASS。git diff --checkも終了コード0。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4、28に明示起動と存在確認を規定。runtime/spec_review_loop/criteria.py:25、session.py:31でも対象changeの存在を検査する。evals/evals.jsonの起動3例がこの経路に対応する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4、22に説明・一般レビュー・applyだけでは起動しないことを明記。evals/evals.jsonの非起動4例とtests/test_skill.py:28で契約を検査し、今回の変更範囲にも既存QA記録は含まれない。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:34、88、192がタスク・Scenarioを順序付きで抽出する。session.py:94、104から抽出一覧を返し、render.pyのstart表示に渡す。tests/test_criteria.py:57でID順序と本文を検査し、本changeの再抽出でも43基準と指定指紋が一致した。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:44で本文のみを取得し、64、179で状態を含めずハッシュ化する。tests/test_criteria.py:67がチェック変更前後のdriftなしを検査する。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:87でround SHAから再抽出し、差分時は_finish_roundへ渡してHOLDを記録する。session.py:135、next_actionのhold分岐で基準IDとrefreezeを案内。tests/test_gate.py:87、96、219、228に変更・全削除の回帰検査がある。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:198で0件を契約拒否する。session.py:94の抽出は状態書込み前に行われ、startはcommitを呼ばない。tests/test_criteria.py:100に抽出不可の拒否テストがある。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、46でmain/masterを拒否し、topic branchへの切替例を示す。session.py:75から呼び出し、tests/test_gitops.py:19でdefault branch拒否を検査する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82で報告の存在と空でないことを、add・commitより前に検査する。tests/test_gitops.py:39に報告なしの拒否検査がある。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86以降がreview成果物以外のunstaged/untrackedをpath付きで拒否し、stageまたは除外を案内する。tests/test_gitops.py:46が両状態の拒否を検査する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16、36で既定Codexとread-onlyを指定する。review_round.py:92と94でcheck用とReviewer用のworktreeを分離し、Reviewerは毎回record['sha']から作成される。tests/test_gate.py:262がcheckの追跡ファイル改変がReviewerへ伝わらないことを検査し、tests/test_reviewers.py:24が版・モデル・cwdを検査する。F-002は解消。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:79以降でprobe失敗時はReviewerを実行せず、doctor結果と導入・切替案内を返す。reviewers.py:76以降に必要フラグと導入方法があり、tests/test_gate.py:131、tests/test_reviewers.py:62、68が対応する。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:151以降で起動失敗・timeoutを結果化し、review_round.py:16、101以降と_finish_roundでINCONCLUSIVE・最大2 attemptsを記録する。tests/test_gate.py:118、203が失敗・timeout・不正出力と再試行回数を検査する。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:31以降がID配列を比較し、欠落・追加・重複・順序違いを構造不適合にする。review_round.py:118以降は不適合出力を有効reviewとして扱わない。tests/test_gate.py:30、tests/test_schema_contract.py:63が対応し、メモリ上でもID重複の拒否を確認した。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:76以降はFAILを未実行より優先し、_pending_reasonsも保持する。tests/test_gate.py:53でNOT_RUNとの併存を検査する。メモリ上でもGate FAILとCHK-VALIDATE: NOT_RUNの個別理由を確認した。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12で基準に対応しないFindingをproposalsへ移す。decideと_stalledはproposalsを参照せず、report.py:38で提案欄へ表示する。tests/test_gate.py:65が格下げ・PASS・Markdown記録を検査する。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:114でPASS停止、review_round.pyの_finish_roundでstoppedを保存する。session.pyのnext_actionのpass分岐でfinishと人によるarchive判断を案内。tests/test_gate.py:143、tests/test_integration.py:11が2 round目PASSの停止を検査する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:125以降で前回openだった同IDのunresolvedを停滞とする。session.pyのnext_actionとSKILL.mdの停止表に引継ぎ先を記載。tests/test_gate.py:150が上限前の同一Finding停滞を検査する。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:119で上限停止し、session.py:133でも超過roundのcommitを拒否する。next_actionが人の判断と既存QA経路への引継ぎを案内し、tests/test_gate.py:161が4 round目を開始しないことを検査する。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:64でtrailer、84でconfirm、90以降でsummary commit・バックアップ・squash・tree検証を行う。tests/test_integration.py:35以降が1 commit化、tree、summary、trailerを検査する。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:134がremote追跡refからの到達可能性を検査する。finish.py:54以降がsquash前に拒否し、別途承認・手作業を案内する。tests/test_gitops.py:119に拒否テストがある。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:107でtreeを比較し、不一致時はgitops.restore後に失敗を返す。gitops.py:172でHEAD・index・作業ツリーを復元する。tests/test_gitops.py:147に改変したtreeからの復元検査がある。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:40で明示受容を必須化し、64、68で最終Gateと最新有効レビューの残余IDをtrailerへ出力する。report.py:62、73も同じレビューを参照する。tests/test_gitops.py:218にFAIL→次round失敗→残余受容の回帰検査があり、メモリ上の生成でも前roundの6件が保持された。F-003は解消。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:32で成果物を対象change内のreviewへ配置し、finish.py:90、92でsummaryを含め追跡する。report.py:56以降で各round SHAとGate推移を記録し、tests/test_integration.py:44以降で最終commitにreview成果物が含まれることを検査する。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:116以降で対象ref・到達不能SHA・dry-runを返し、confirm時だけ削除する。render.py:95が対象と確認案内を表示し、tests/test_gitops.py:178で確認前後のref状態を検査する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 未解消 | medium | defect | T-5.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:41 | 内部の空白・改行の正規化は除去されたが、前後のstripによる原文改変の許容が残る。保存済みレビューのT-1.1のtextだけに先頭空白2文字と末尾改行を追加し、メモリ上でstructural_errorsを実行すると、構造エラー・provenance不一致とも空配列になった。契約は同じ原文を要求し、前後空白の例外を定めていない。tests/test_schema_contract.py:80以降もこの改変を正常として期待している。 | 固定済みtextとReviewerのtextをstripせず直接比較する。前後の空白・改行追加も構造不適合になる回帰検査へ変更する。 |
| F-002 | 解消 | high | defect | S-spec-review-loop-4.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:92 | check専用worktreeを終了してから、recordのround SHAで別のReviewer専用worktreeを作成する構造になった。check後のdirty状態をReviewerの正常基準として扱う処理も除去されている。tests/test_gate.py:262ではcheckがapp.pyを改変しても、Reviewerの読んだ内容がround SHAのgit show結果と一致することを検査している。元の指摘の原因は解消された。 | 追加対応不要。check用とReviewer用のworktree分離と回帰検査を維持する。 |
| F-003 | 解消 | medium | defect | T-5.3, S-spec-review-loop-7.4 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:95 | latest_reviewが有効なレビューを後方検索し、finish.py:68とreport.py:62が共通して参照するよう修正された。保存済みdogfood stateの最終reviewをメモリ上でNoneにしてsummaryを生成し、r1の未解決F-001〜F-006が全件残余欄に保持されることを確認した。tests/test_gitops.py:218には両回のReviewer失敗後のfinishで要約とtrailerに残余IDを保持する回帰検査もある。 | 追加対応不要。最新の有効なレビューを要約とtrailerで共通参照する処理を維持する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

43基準を指定roundで再確認した。F-002とF-003は解消。F-001は前後空白・改行の改変を構造検証が受理するため未解消で、T-5.1はFAIL。基準指紋は一致し、CLI提供の必須checkは両方PASS。検査は読取りとメモリ上の処理に限定し、終了時の作業ツリーに変更はない。
