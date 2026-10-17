# spec-review r3: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-3.3）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `b261d372805a26f3957073bbf3091f738bc15e8c`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: Findingの停滞

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:1 に必要な項目と列挙値を定義。tests/test_schema_contract.py:35、:40、:60 に正常・欠落・重複の検証があり、runtime/spec_review_loop/gate.py:34 がIDの重複も検査する。CLI提供のCHK-PYTESTはPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5、:11、:33、:38 に各契約を記載。tests/test_schema_contract.py:84 でスキーマ項目・Gate規則との対応を検証している。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:38、:91 に抽出処理がある。python3 -Bによる読取り専用照合でarchive済み4件のタスク／Scenario数が37/25、5/5、15/18、11/23と独立数え上げに一致し、抽出した全タスク本文・全Scenario本文が元ファイルに含まれることを確認した。tests/test_criteria.py:15 に固定期待件数がある。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:48 でチェックボックスを除外し、:190 で原文をSHA-256化、:221 で比較する。tests/test_criteria.py:64、:72 に状態変更・本文変更のテストがある。読取り専用の再抽出で今回の43基準にドリフトがないことも確認した。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:73 に開始検査・base記録、gitops.py:80 に報告必須・unstaged/untracked拒否・trailer付与がある。tests/test_gitops.py:19、:27、:39、:46、:60 が各経路を検証する。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101 のcontextmanagerがfinallyでworktreeを除去する。tests/test_gitops.py:75 は成功・失敗・timeout、:86 は例外時の残存なしを検証する。 |
| T-3.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30、:87 に前提検査・squash・復元があり、tests/test_gitops.py:101～164 に指定テストがある。F-003のsummary commit失敗は修正済み。ただしfinish.py:130～131 は今回作成していない既存refも削除する。python3 -Bとunittest.mockでcreate_refを既存ref衝突として失敗させ、list_refsに既存refを返すと、その既存refへのdelete_ref呼出しを確認した。失敗前のバックアップrefが保持されず、復元要件を満たさない。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:134 が対象refと到達不能SHAを返し、confirmなしでは削除しない。tests/test_gitops.py:178 が確認前後のrefの存否を検証する。 |
| T-4.1 | PASS | openspec/changes/add-spec-review-loop/design.md:146～162 にOpen Questionの解消と3 CLIの版・フラグ・出力取得方法がある。runtime/spec_review_loop/reviewers.py:78、:106 が対応フラグを検査する。evidence/sandbox-add-slugify-codex/summary.md:14、evidence/sandbox-add-slugify-cursor/summary.md:1 に実機レビューの保存証跡があり、tests/test_reviewers.py:62、:68 に未導入・フラグ不足の検証がある。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:25、:144 に共通インタフェースと実行処理、cli.py:54 にdoctorがある。tests/test_reviewers.py:23 は3アダプタをパラメータ化し、:62 は未導入時の導入案内を検証する。 |
| T-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11、:28、:76 に提案分離・構造検証・Gate優先順位がある。tests/test_gate.py:30、:41、:53、:65 とtests/test_schema_contract.py:60、:72 が欠落・重複・原文・優先順位・範囲外提案のScenarioを検証する。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:113、:127 に停止・停滞判定がある。tests/test_gate.py:143、:150、:161、:175 が2 round目PASS・同一Finding停滞・上限・件数非減少を検証し、session.py:108 が停止後の次roundを拒否する。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:14、:44 がJSON記録から各Markdownを生成し、:65～78 でsummaryの基準・残余Finding・提案を出力する。tests/test_report.py:16～40 が必要項目を検証する。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1 とruntime/spec_review_loop/cli.py:18、:65、:88 に入口・全サブコマンド・例外時終了コードがある。tests/test_cli.py:9、:18、:47 以降に正常・契約拒否・入出力・内部エラーの検証がある。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3 のdescriptionに適用範囲・正例・非起動例を記載し、:14、:43、:54 に使い分け・round手順・引継ぎがある。tests/test_skill.py:13、:21 が形式と本文を検証する。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:25～66 に起動3例・非起動4例がある。tests/test_skill.py:28 が件数・一意ID・必須内容を検証する。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:9～50 が偽ReviewerによるFAIL→PASS→finishを実行し、commit数・バックアップとのtree一致・summary・trailer・clean状態を検証する。CLI提供のCHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/summary.md:12～15 にCodexの版・モデル・round SHA・FAIL→PASSを記録し、同ディレクトリのr1_review.json:1、r2_review.json:1、squash_commit.txt:1 に個別判定と終了trailerを保存している。本change自身の実行証跡もevidence/dogfood-add-spec-review-loop-codex/state.json:1 にあり、implementation-record.md:40～51 は停滞停止とfinish未実行を区別している。 |
| T-7.3 | PASS | CLI提供のCHK-VALIDATEはexit_code 0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac..HEADで変更がopenspec/changes/add-spec-review-loop/とquality-loop/skills/spec-review-loop/の配下に限られ、既存QA Skill・既存QA記録の変更がないことを確認した。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3、:28 に明示依頼時の存在確認手順がある。runtime/spec_review_loop/criteria.py:29 が存在しないchangeを拒否し、tests/test_cli.py:13 に拒否確認がある。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3、:23 に非起動条件と既存記録の非変更を明記。evals/evals.json:44～66 に説明・一般レビュー・apply・結果共有の非起動例がある。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:63、:125、:208 が順序を保持してIDを付ける。session.py:104 が一覧を返し、tests/test_cli.py:11 とtests/test_criteria.py:52 が表示・順序を検証する。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:48 が番号以降の原文を指紋対象にする。tests/test_criteria.py:64～69 とtests/test_integration.py:23～30 がチェックボックス変更を許容する。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:135～137 がHOLDと変更ID・refreeze案内を返す。review_round.py:88～90、:127～139 はround SHA上のドリフトをHOLDとして記録する。tests/test_gate.py:87、:96、:219、:228 が通常変更・全削除を検証する。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:209～211 が0件を拒否し、session.py:94 はstate保存前に抽出する。startにcommit呼出しはなく、tests/test_criteria.py:93 に拒否テストがある。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、:46～50 でmain/masterを拒否し切替を案内する。tests/test_gitops.py:19 がmaster拒否とstate非作成を検証する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82～85 が実装報告の存在・内容を検査する。tests/test_gitops.py:39～43 は拒否後もcommitが増えないことを確認する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86～91 がreview成果物以外のunstaged/untrackedをpath付きで拒否する。tests/test_gitops.py:46～57 が両方のpathを検証する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16、:36～41 にCodex既定とread-only起動指定、review_round.py:94～100、:132 に隔離実行とReviewer記録がある。tests/test_reviewers.py:23～35 がcwd・フラグ・記録内容を検証する。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:79～82 がprobe失敗時にdoctor結果・導入・切替案内を返す。tests/test_gate.py:131～138 とtests/test_reviewers.py:62～71 に未導入・必要フラグ不足の検証がある。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:14、:101～116、:123～139 が失敗のINCONCLUSIVE記録と再試行1回を実装する。tests/test_gate.py:117～128、:202～210 が失敗・timeout・不適合出力を検証する。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:34～40 が欠落・追加・重複・順序違いを構造不適合にする。review_round.py:115～116 は当該出力を採用せず、tests/test_gate.py:30～38 とtests/test_schema_contract.py:60～69 が検証する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:83～95 がFAILを優先し、未実行理由も返す。tests/test_gate.py:53～59 にFAIL＋NOT_RUNの直接検証があり、report.py:29～30 が各checkの状態・理由を出力する。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11～25 が対応基準のない新規Findingを提案へ移す。tests/test_gate.py:65～71 は提案への移動・Markdown記録・Gate PASSを確認し、gate.py:107～110 の停滞対象はfindingsに限定される。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:117～118 がPASSで停止し、session.py:176～177 がfinishと人によるarchive判断を案内する。tests/test_gate.py:143～147 が2 round目の経路を検証する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:119～121、:131～134 が反復未解消を上限より先に検出する。tests/test_gate.py:150～158 がF-002で停止・次round拒否・引継ぎ案内を検証し、report.py:33～35 がFinding内容を表示する。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:122～123 とsession.py:109～118、:133～134 が上限後の開始を防ぐ。tests/test_gate.py:161～172 が3 roundで停止し4 round目を拒否することを検証し、session.py:180～181 に引継ぎ案内がある。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:68～83、:87～111 に確認・summary・バックアップ・squash・tree検証・trailer生成がある。tests/test_gitops.py:101～116 とtests/test_integration.py:35～49 が正常系を検証する。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:59～64 が各commitのリモート追跡refからの到達可能性を検査し、force-pushの別途承認・手作業を案内する。tests/test_gitops.py:119～126 がHEADを保持した拒否を確認する。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:109～116、:125～129 が不一致時にバックアップtreeを復元したうえでfinish前のround・stateへ戻し、失敗を報告する。tests/test_gitops.py:147～164 は改変内容の復元とfinish再実行成功を検証する。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:40～42、:72～76 に残余受容の必須化とtrailer記録、report.py:54、:73～75 に要約記録がある。tests/test_gitops.py:167、:206、:218 が通常の残余・最終レビュー失敗時の持越しを検証する。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:31～34 が成果物をchange内のreview/に配置する。tests/test_integration.py:44～48 がsummaryとレビュー成果物の追跡を検証し、report.py:56～61 がround SHA・Gate推移を出力する。SKILL.md:79 にchangeと一緒にarchiveされる配置を明記している。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:134～147 が対象ref・到達不能SHAを返し、confirm後に削除する。tests/test_gitops.py:178～188 がdry-runでの保持・確認後の削除を検証する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-003 | 解消 | medium | defect | T-3.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:97 | 元の指摘であるsummary commit失敗後にfinished/pendingが残る不具合は解消された。summary生成・state保存・git add・summary commit・バックアップref作成が復元用try内に入り、失敗時は終了前stateへ戻る。python3 -Bとunittest.mockで入出力とGit操作をメモリ上に置換し、summary commit失敗時および通常のref作成失敗時に、終了前stateの書戻し・元HEADへのreset・summary削除・squash未実行を確認した。tests/test_gitops.py:257～268 にhookによるsummary commit拒否後の復元と再実行成功の回帰テストがある。 | 元の指摘に対する追加修正は不要。既存バックアップrefの保持に関する別の問題はF-004として扱う。 |
| F-004 | 新規 | medium | defect | T-3.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:130 | バックアップref作成が同名refの存在により失敗すると、復元処理がその既存refを削除する。gitops.py:153 のcreate_refは既存refを保護するため更新を拒否するが、finish.py:107での失敗後も_rollbackは同名refが存在すれば無条件にdelete_refする。ref名はsession.py:22の秒単位timestampで生成され、事前の衝突検査もない。python3 -Bとunittest.mockでcreate_refを既存ref衝突として失敗させ、list_refsに以前から存在する同名refを返したところ、そのrefへのdelete_ref呼出しを確認した。既存のバックアップ参照を失うため、失敗前の状態への復元にならない。 | 今回のfinishでref作成に成功したかを別のフラグで管理し、成功したrefだけをrollback時に削除する。可能なら削除時も期待SHAを指定して別の更新を保護する。既存ref衝突を再現し、元のref名とSHAが保持され、終了前state・HEADが復元される回帰テストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準を指定順で再判定した。F-003は解消を確認したが、finish失敗時に既存バックアップrefを削除するF-004を確認し、T-3.3をFAILとした。必須checkは双方PASS。確認は読取りとメモリ上の模擬に限定し、作業ツリーの変更はない。
