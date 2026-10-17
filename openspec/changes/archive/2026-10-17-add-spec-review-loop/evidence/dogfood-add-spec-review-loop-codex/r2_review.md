# spec-review r2: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-2.2, T-4.1, S-spec-review-loop-2.3）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `8b28ed1037fb5859f809ab96d55c17e8484412cc`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: Findingの停滞

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:7 に必須項目を定義。tests/test_schema_contract.py:39 以降に正常・欠落・重複の検査がある。python3 -Bによるメモリ上の検査でも、保存済み正常JSONの適合と4種類の不正構造の拒否を確認した。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5 以降に読取り専用、基準の保持、根拠、Gate、提案、再判定を規定。tests/test_schema_contract.py:81 以降でスキーマ項目とGate規則への対応を検査している。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:39、93、127 に抽出処理がある。読取り専用の再照合でarchive済み4件のタスク／Scenario件数が37/25、5/5、15/18、11/23となり、原文の見出し数と一致した。tests/test_criteria.py:26 以降に件数と原文の照合がある。 |
| T-2.2 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:184、215 に指紋と比較処理があり、tests/test_criteria.py:62 以降に指定の2テストがある。ただしcriteria.py:203で0件の再抽出を例外にするため、全基準削除時にはドリフト検出に到達しない。Session.commit_roundをメモリ上のモックで確認し、HOLDやrefreeze案内のない通常の抽出エラーとなることを再現した。F-007参照。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:75、78、97で開始条件とbaseを扱い、gitops.py:80で報告・未stage・trailerを扱う。tests/test_gitops.py:19、39、46、60に対応テストがある。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101でcontextmanagerを使い、finallyでworktree削除・prune・一時ディレクトリ削除を行う。tests/test_gitops.py:75、86で成功・失敗・timeout・例外時の残存を検査している。 |
| T-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30、81、98、99、106で計画・条件・バックアップ・例外復元・tree検証を実装。gitops.py:178でHEAD・index・作業ツリーを復元する。tests/test_gitops.py:101、119、129、139、147、191に正常・拒否・復元テストがある。F-001の指摘箇所は修正済み。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:115で対象refと到達不能SHAを返し、confirmがある場合だけ削除する。tests/test_gitops.py:178で確認前のref保持と確認後の消失を検査している。 |
| T-4.1 | FAIL | openspec/changes/add-spec-review-loop/design.md:154 以降に版とフラグがあるが、157でGeminiは実機未確認。implementation-record.md:54、58ではagyも最終出力取得まで未確認とされる。tasks.md:22も未完了。F-003は未解消。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:28、54、108、146に共通インタフェース・出力取得・probe・実行処理がある。tests/test_reviewers.py:23以降で4アダプタ経路を検査し、未導入時の導入案内も検査している。 |
| T-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12、26、73に提案除外・構造検証・Gate優先順位を実装。review_round.py:105で格下げ前のスキーマ検証を追加した。tests/test_gate.py:31、43、76、202に欠落、優先順位、提案、不正構造のテストがある。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:102、116に停止・停滞判定がある。tests/test_gate.py:143以降でr2 PASS、同一Finding未解消、r3上限、未解消数非減少を検査している。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:12、42に両生成処理があり、61以降でsummaryにも最終roundの全基準とcheckを追加。python3 -Bのメモリ上の生成で43基準すべての表行を確認した。tests/test_report.py:16、39にも対応検査がある。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1から同梱runtimeを起動し、runtime/spec_review_loop/cli.py:18、65、88で全サブコマンドと終了コードを処理する。tests/test_cli.py:11以降に正常・契約拒否・入出力・内部エラーの検査がある。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3のdescriptionに適用範囲・明示依頼例・非発火例がある。本文に実装担当の手順、停止時の引継ぎ、既存QA経路との使い分けを記載。tests/test_skill.py:14以降で形式と内容を検査している。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:25以降のactivation_casesに起動例3件、非起動例4件がある。tests/test_skill.py:30以降で各3件以上を検査している。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:11の通しテストがr1 FAIL→r2 PASS→finishを実行し、2件から1件への集約、バックアップとのtree一致、summary、trailer、成果物追跡、clean状態を検査する。提示されたCHK-PYTESTもPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/r1_review.json、r2_review.jsonの保存済み結果を読取り確認し、codex-cli 0.160.1／gpt-6-luna、各round SHA、FAIL→PASSを確認した。同ディレクトリのsummary.md:12以降に推移、squash_commit.txt:4以降にGate・round数・Reviewer・squash前SHAが残る。F-005の証跡不足は解消。 |
| T-7.3 | PASS | git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac HEADで、変更が新Skillと対象change配下に限定されていることを確認した。対象外の既存Skill・QA記録の変更はない。提示されたround SHA上のCHK-VALIDATEは終了コード0でPASS。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3に明示起動条件、起動前手順にchange存在確認を記載。runtime/spec_review_loop/criteria.py:30とsession.py:31で対象changeの存在を検査する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3に説明・一般レビュー・OpenSpec applyのみでは非起動と規定し、本文にも非起動例と既存記録の非変更を記載。evals/evals.json:45以降に対応する非起動例がある。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:65、127、136でIDを付与し、render.py:23以降で一覧を表示。対象changeの再抽出で19タスク・24Scenario、計43基準と指定指紋の一致を確認した。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:49、69でチェックボックス状態を原文に含めない。tests/test_criteria.py:62以降の切替テストとtests/test_integration.py:27以降のr2完了チェック変更がこの挙動を検査する。 |
| S-spec-review-loop-2.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:125、136およびreview_round.py:87はcrit.build成功後にだけドリフトを比較する。criteria.py:203が全基準削除時に例外を送出し、HOLD・変更ID・refreeze案内を経由しない。メモリ上のモックでcommit_roundの通常抽出エラーと状態書込み0回を確認した。F-007参照。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:203で0件を拒否し、session.py:94で状態作成前に呼び出す。start処理にはcommit操作がない。tests/test_criteria.py:92以降に0件拒否のテストがある。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、46でmain/masterを拒否してtopic branchを案内。tests/test_gitops.py:19とtests/test_cli.py:11以降でmaster拒否を検査する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82で実装報告の存在と空でないことをcommit前に検査。tests/test_gitops.py:39で拒否とcommit数0を確認する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86以降でreview成果物以外の未stage・未追跡pathを拒否結果に含める。tests/test_gitops.py:46で両状態のpath表示を検査する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16、31で既定Codexとread-only起動を指定。review_round.py:86、128でround worktreeとReviewer情報を扱う。tests/test_reviewers.py:23以降と保存済み実機レビューJSONで起動経路・記録を確認できる。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:108で存在と必須フラグを検査。review_round.py:78で実行前に拒否し、doctor結果・導入・切替案内を返す。tests/test_reviewers.pyとtests/test_gate.py:131以降に対応検査がある。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:153以降で起動失敗・timeoutを返し、review_round.py:98、105、119以降で不適合を記録し最大2 attemptに制限する。tests/test_gate.py:117以降と202以降に失敗・再試行・不正構造の検査がある。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:32以降でID配列の一致と欠落・重複を検査し、review_round.py:111で有効レビューとして採用しない。tests/test_schema_contract.py:65以降とtests/test_gate.py:31以降に対応テストがある。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:80以降でFAILを未検証より優先し、未実行理由も残す。report.py:27以降でcheck状態・終了コード・理由を個別に出力。tests/test_gate.py:56以降にFAILとNOT_RUN併存の検査がある。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12で対応基準のないFindingを提案へ移し、停止判定はfindingsのみを参照する。report.py:36で提案を別記する。tests/test_gate.py:76以降でPASSと提案欄への記録を検査する。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:106でPASS停止、session.py:174以降でfinishと人によるarchive判断を案内する。tests/test_gate.py:143以降でr2 PASSと案内を検査する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:120で前roundの未解決IDと今回のunresolvedを照合する。render.py:58以降でFinding内容と停止・引継ぎを表示する。tests/test_gate.py:151以降でF-002の停滞と次round拒否を検査する。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:111で上限停止し、session.py:109、133で次round開始を拒否する。tests/test_gate.py:164以降でr3の停止とr4拒否を検査する。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:64、83、89、98、100、106で確認・summary・バックアップ・squash・tree・trailerを実装。tests/test_integration.py:11とtests/test_gitops.py:101に通しの検査がある。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:54で全commitのリモート追跡ref到達性を検査し、57以降で拒否と明示承認・手作業を案内。tests/test_gitops.py:119でリモート追跡refを用いた拒否を検査する。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:106以降でtree不一致時にrestoreを実行して失敗を返す。gitops.py:178のhard resetにより作業ツリーも戻る。tests/test_gitops.py:147で改変ファイルを含む復元を検査する。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:40で明示受容を必須にし、64、68、70でGateと残余FindingのIDをtrailer化。report.py:67で要約へ残余Findingを記録する。tests/test_gitops.py:206で複数Findingのtrailerを検査する。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:32で成果物をchange内のreviewへ配置し、finish.py:89、91でsummaryを含め追跡する。report.py:54以降にround SHAとGate推移を出力。tests/test_integration.py:44以降でreview成果物が最終commitに含まれることを検査している。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:115以降で対象refと到達不能SHAを算出してconfirm前は削除しない。render.py:95以降で表示する。tests/test_gitops.py:178に確認前後のref検査がある。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 解消 | high | defect | T-3.3, S-spec-review-loop-7.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:99; quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:178; quality-loop/skills/spec-review-loop/tests/test_gitops.py:147 | 解消を確認した。squash commitの例外時にもrestoreを呼び、tree不一致時とともにHEAD・index・作業ツリーをバックアップへ戻す。回帰テストはcommit失敗時のclean状態と、tree不一致を起こしたファイルの復元まで確認する。 | 追加対応は不要。両方の復元回帰テストを維持する。 |
| F-002 | 解消 | high | defect | T-5.1, T-6.1, S-spec-review-loop-4.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:105; quality-loop/skills/spec-review-loop/tests/test_gate.py:202 | 解消を確認した。demote_proposalsより前にスキーマ検証を行い、不適合は_finish_roundへ渡す。findings要素null、criterion_ids null、criteria文字列を扱う回帰テストがある。メモリ上の検査でもこれらとproposals非配列が例外なく検証エラーとなった。 | 追加対応は不要。不正構造をINCONCLUSIVEとして記録する回帰テストを維持する。 |
| F-003 | 未解消 | medium | missing | T-4.1 | openspec/changes/add-spec-review-loop/design.md:156; openspec/changes/add-spec-review-loop/implementation-record.md:58; openspec/changes/add-spec-review-loop/tasks.md:22 | 未解消。agyの最終出力取得までの実機確認は未了で、Gemini CLIも未導入・未確認である。doctorのフラグ検出と偽Reviewerによる経路検査では、要求された実機での読取り専用・非対話実行と出力取得の確認を満たさない。タスクが未完了に修正されている点は適切である。 | 対象CLIのmacOS実機版で読取り専用・非対話起動から最終JSON取得まで確認し、版・フラグ・観察結果を保存する。実行できない間は未完了を維持する。 |
| F-004 | 解消 | medium | missing | T-5.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:61; quality-loop/skills/spec-review-loop/tests/test_report.py:39 | 解消を確認した。summary.mdへ最終roundの全受入基準IDと判定、必須checkの状態を出力する。保存済みレビューからメモリ上で生成し、43基準すべての表行が存在することを確認した。 | 追加対応は不要。全基準IDの包含検査を維持する。 |
| F-005 | 解消 | medium | test-gap | T-7.2 | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/summary.md:12; openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/squash_commit.txt:4 | 解消を確認した。実機Codexでのchange実行について、criteria、各roundのレビューJSON、Markdown、summary、squash commit情報がround SHA内へ追加された。JSONとsummaryのround SHA、Reviewerの版・モデル、FAIL→PASSの推移が一致している。 | 追加対応は不要。保存した実行証跡を維持する。 |
| F-006 | 解消 | medium | missing | S-spec-review-loop-7.4 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:68; quality-loop/skills/spec-review-loop/tests/test_gitops.py:206 | 解消を確認した。非PASSのfinishでは最終レビューの未解決FindingからIDを抽出し、利用者の受容文とは別にSpec-Review-Residual-Findings trailerへ記録する。回帰テストはF-001、F-002の双方とFAIL Gateの記録を検査する。 | 追加対応は不要。非PASS終了時の残余Finding記録テストを維持する。 |
| F-007 | 新規 | medium | defect | T-2.2, S-spec-review-loop-2.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:203; quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:125; quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:87 | 固定後に全タスク・Scenarioが削除された場合、再抽出した空集合を固定基準と比較できない。crit.buildが0件を契約エラーとして送出するため、commit-roundでは通常の抽出エラーとなり、reviewでもHOLD記録前に例外が伝播する。変更された基準IDとrefreezeの必要が示されない。Session.commit_roundをメモリ上で検査し、通常抽出エラー・状態書込み0回を再現した。 | 開始時の0件拒否と、既存セッションでの再抽出を分離する。再抽出では空集合も比較できるようにし、削除された全基準IDを含むHOLDとrefreeze案内を返す。commit-round前とround SHAレビュー時の双方に、全基準削除の回帰テストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

前roundの6件中5件は解消を確認した。F-003の代替Reviewer実機確認は未了。新たに、全基準削除時にドリフトをHOLDとして扱えないF-007を確認した。43基準を再判定し、指紋一致・archive済み4件の抽出件数・summaryの全基準ID出力を読取り専用で確認した。作業ツリーの変更はない。
