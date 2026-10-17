# spec-review r1: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-3.3, T-4.1, T-5.1, T-5.3, T-6.1, S-spec-review-loop-4.3, S-spec-review-loop-7.3, S-spec-review-loop-7.4; T-7.2: UNVERIFIED）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `c2070d7f2d83f9a7fa22439d888b80daefe0f4df`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:1 に各項目と列挙値を定義。tests/test_schema_contract.py:35-69 に正常・欠落・重複の検証があり、正常と重複・欠落の構造検証テストをpython3 -Bで直接実行して成功した。重複IDの拒否はgate.structural_errorsが担当する。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5-49 に要求された契約を記載。tests/test_schema_contract.py:81 の契約・スキーマ・Gate対応テストをpython3 -Bで直接実行して成功した。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:37-139 がタスク・検証文・各deltaのScenarioを抽出する。tests/test_criteria.py:15-56 に4件のarchive照合と原文確認がある。読み取り検査で4件のタスク／Scenario件数が37／25、5／5、15／18、11／23と独立集計に一致し、タスク本文も元ファイルに一致した。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:65-78 でチェックボックスを含めず原文を構成し、:184-194 でSHA-256を算出する。tests/test_criteria.py:61-74 がチェック変更と本文変更を検証する。現在の再抽出指紋も指定の8fcd90a769b8fcb1bb2b3f1d1c9ff3995455381d5fb19a95b158d701431b3c35と一致した。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:73-102 がbranch・dirty検査とbase記録を実施し、gitops.py:80-98 が報告・未stage検査とtrailerを実装する。tests/test_gitops.py:19-72 に指定された拒否系と正常commitの検証がある。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101-112 が指定SHAのworktreeを作成しfinallyで削除する。tests/test_gitops.py:75-91 が成功・失敗・timeout・例外の後にworktree一覧が元に戻ることを検証する。 |
| T-3.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:95-102 はtree不一致時だけ復元し、commit_squash自体の例外を捕捉しない。副作用のないモック検査でcommit_squashを例外にするとrestoreが呼ばれないことを確認した。またgitops.py:172-174 の復元はmixed resetであり、tree不一致を生じさせた作業ツリーの変更を戻さない。F-001。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:106-119 がrefと到達不能になるSHAを返し、confirm時だけ削除する。render.py:95-99 が確認内容を表示する。tests/test_gitops.py:177-187 が確認前後のrefを検証する。 |
| T-4.1 | FAIL | openspec/changes/add-spec-review-loop/design.md:157 はGeminiを未導入・実機未確認とし、読取り専用動作も想定に留まる。tasks.md:22 も未完了である。design.md:156 のagyについても成功した実機出力の証跡がなく、Open Questionが解消されたとは確認できない。F-003。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:20-89 に各アダプタ、:108-129 に版・フラグ・導入案内、:146-170 に共通実行経路がある。tests/test_reviewers.py:24-37 がcodex／claude／gemini／agy経路を、:68-78 が未導入・未対応フラグを検証する。 |
| T-5.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:26-87 に構造検証と優先順位はあるが、review_round.py:105 がスキーマ検証前にFindingを処理する。findings:[null]とcriterion_ids:nullを渡す読み取り検査でAttributeError／TypeErrorを再現し、不適合結果の記録に到達しない。F-002。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:102-127 がPASS・停滞・上限を判定し、session.py:108-134 が次roundを制限する。tests/test_gate.py:143-180 が2round目PASS、同一Finding未解消、3round上限、未解消数非減少を検証する。 |
| T-5.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:25-37 はroundレビューに全基準を出すが、:42-67 のsummaryは基準一覧を出さない。正常なレビューJSONからsummaryをメモリ上で生成するとT-1.1、S-cap-1.1の両IDが欠落した。tests/test_report.py:24-38 も全基準IDの検査はround文書だけである。F-004。 |
| T-6.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/cli.py:18-84 に全サブコマンドと終了コードの経路がある。しかし不正なFinding構造はreview_round.py:105から例外となり、cli.py:95-97 の内部エラー4へ進む。Reviewer不適合を入出力エラー3として記録する経路を通らない。F-002。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4 が適用範囲・明示例・非起動例を規定し、:13-22 に既存経路との区別、:43-66 に実装手順と停止時引継ぎを記載する。tests/test_skill.py:13-25 に対応する検査がある。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:25-67 に起動3件と非起動4件を収録し、各発話にexpected_triggerと理由がある。tests/test_skill.py:28-35 が件数と形式を検証する。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:10-50 がCLIでFAIL→修正→PASS→finishを実行し、commit数、バックアップとのtree一致、summaryの両SHAとGate推移、trailerを検証する。実装の対応箇所はfinish.py:78-103。提供されたCHK-PYTESTもPASSである。 |
| T-7.2 | UNVERIFIED | openspec/changes/add-spec-review-loop/implementation-record.md:26-36 は外部一時リポジトリの実行を説明するが、そのreview JSONやsummaryはround内にない。本changeのreview/state.json:13 はroundsが空で、summary.mdも存在しない。tasks.md:40 は完了だが、自己申告以外の通し実行証跡を指定SHAで確認できない。F-005。 |
| T-7.3 | PASS | 提供されたCHK-VALIDATEは終了0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac c2070d7f2d83f9a7fa22439d888b80daefe0f4dfで41ファイルを確認し、変更は本changeと新Skill内に限定されていた。git diff --checkも指摘なし。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4,28 が明示依頼と存在確認を規定する。runtime/spec_review_loop/session.py:31 とcriteria.py:29-34 は存在しないchangeを開始前に拒否し、tests/test_cli.py:10-14 が拒否を検証する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4,22 が非起動条件を明記し、evals/evals.json:44-66 が説明・一般レビュー・apply・結果共有を非起動とする。指定SHA間の変更パスにも既存QA経路の変更はない。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:65-78,127-139 が順序どおりIDを付け、render.py:23-31 が一覧を表示する。tests/test_criteria.py:50-58 とtests/test_cli.py:10-12 に順序と表示の検証がある。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:43-48,72 がチェック状態を原文に含めない。tests/test_criteria.py:61-66 がチェック変更前後のドリフトなしを検証する。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:135-137 が変更IDとrefreezeを示してcommitを拒否する。review_round.py:87-89,117-132 はround SHA上のドリフトをHOLDとして停止する。tests/test_gate.py:87-112 が両経路を検証する。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:197-205 が基準0件を拒否し、session.py:94-102 は抽出成功後にだけ状態を書き込む。startにcommit処理はなく、tests/test_criteria.py:90-95 に0件拒否の検証がある。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13,46-50 がmainとmasterを拒否し、topic branchへの切替を案内する。tests/test_gitops.py:19-24 がmaster拒否と状態未作成を検証する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82-85 は報告の存在と非空をcommit前に検査する。tests/test_gitops.py:39-43 が拒否後のcommit数0を検証する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86-91 が自動収集対象のreview配下を除くunstaged／untrackedをpath付きで拒否する。tests/test_gitops.py:46-57 が両状態と表示pathを検証する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16,31-36 が既定Codexとread-only指定を定義する。review_round.py:86-97,125-128 が指定SHAのworktreeで起動しReviewer情報を記録する。tests/test_reviewers.py:24-37 が起動cwd・フラグ・記録を検証する。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:108-129 が存在と必要フラグを確認し、review_round.py:78-81 がdoctor結果・導入・切替案内付きで拒否する。tests/test_gate.py:131-138 はReviewer未起動を検証する。 |
| S-spec-review-loop-4.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:105-109 はFindingの格下げをスキーマ検証より先に実行する。findings:[null]ならgate.py:17でAttributeErrorとなり、_finish_roundが呼ばれずINCONCLUSIVE・attempt数・再試行制限が記録されない。python3 -Bによるメモリ上の呼出しで再現した。F-002。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:32-42 がID一覧の欠落・重複・順序を検査し、review_round.py:108-109 が不適合レビューを採用しない。tests/test_schema_contract.py:60 の欠落・重複テストを直接実行して成功し、tests/test_gate.py:30-38 がレビュー未採用を検証する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:80-92 がFAILを先に判定し、未実行理由も保持する。tests/test_gate.py:53-59 がFAILとNOT_RUNの併存を検証し、report.py:27-28 がcheck状態・終了code・理由を個別に出力する。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12-23 が基準に対応しないFindingを提案へ移す。:96-127 の停滞処理はfindingsのみを参照し、report.py:36-37 が提案を記録する。tests/test_gate.py:65-71 にGate PASSと提案出力の検証がある。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:106-107 がPASS停止を返し、session.py:176-177 がfinishと利用者のarchive判断を案内する。tests/test_gate.py:143-147 が2round目のPASS停止と案内を検証する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:120-123 が同一未解消Findingを検出し、render.py:59-67 が内容・停滞ID・引継ぎ先を表示する。tests/test_gate.py:150-158 がF-002の2round停滞と次round拒否を検証する。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:111-112 が上限停止を返し、session.py:109-118,133-134 が次roundを拒否する。render.py:59-67 がFindingと引継ぎを表示し、tests/test_gate.py:161-172 が4round目の拒否を検証する。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:63-65,78-103 が確認後のsummary追加・バックアップ・squash・tree比較・trailerを実装する。tests/test_gitops.py:101-116 とtests/test_integration.py:33-50 が正常系のcommit数・tree・trailerを検証する。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:53-58 が各commitのリモート追跡refからの到達可能性を検査して拒否する。tests/test_gitops.py:119-126 が模擬リモートrefによる拒否・明示承認案内・HEAD不変を検証する。 |
| S-spec-review-loop-7.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:98-102 は復元を呼ぶが、gitops.py:172-174 は作業ツリーを戻さないmixed resetである。tests/test_gitops.py:152-155 のように作業ツリーとindexを変更する不一致では、HEADとindexだけ戻って改変ファイルが残る。同テスト:160-163 は作業ツリーの一致を検査していない。F-001。 |
| S-spec-review-loop-7.4 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:39-41 は明示受容を要求し、report.py:60-62 は残余Findingを要約する。しかしfinish.py:63-67 のtrailerはGateと利用者の自由記述だけで、残余FindingのIDや内容を記録しない。F-006。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:31-33 がreviewをchange内に配置し、finish.py:86-91 が成果物を追跡する。report.py:54-59 が全round SHAとGate推移をsummaryに保持する。tests/test_integration.py:44-49 がsummary内容とchange配下の追跡済み成果物を検証する。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:108-119 が対象ref・到達不能SHAを算出しconfirm後だけ削除する。render.py:95-99 が表示し、tests/test_gitops.py:177-187 が確認前後の挙動を検証する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | high | defect | T-3.3, S-spec-review-loop-7.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:96; quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:174 | squash失敗時の復元が不完全である。reset --soft後のcommitが失敗すると例外がそのまま伝播し、HEADはbaseに移動したままになる。メモリ上のモック検査でもrestoreが呼ばれないことを確認した。tree不一致時のrestoreもmixed resetだけなので、不一致を生じさせた作業ツリーの改変が残り、バックアップ状態へ完全には戻らない。 | バックアップ作成後のsquashとtree検証を例外復元の対象にし、失敗時はHEAD・index・今回の処理で変化した作業ツリーをバックアップ状態へ戻す。commit失敗とtree不一致の双方について、HEADだけでなくindex・作業ツリーの一致も検証する。 |
| F-002 | 新規 | high | defect | T-5.1, T-6.1, S-spec-review-loop-4.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:105 | スキーマ検証前にdemote_proposalsを実行するため、不正なFinding構造を安全に処理できない。findings:[null]でAttributeError、criterion_ids:nullでTypeErrorを再現した。CLIは内部エラー4となり、roundのINCONCLUSIVE記録・attempt加算・再試行1回制限が適用されない。 | 提案への格下げ前にJSONの型と必須項目を検証し、不適合は必ず_finish_roundへ渡す。findings要素がnull、criterion_idsがnull、proposalsが配列以外などの入力で、INCONCLUSIVE記録と再試行制限、終了コード3を確認する。 |
| F-003 | 新規 | medium | missing | T-4.1 | openspec/changes/add-spec-review-loop/design.md:156 | 代替ReviewerのmacOS実機確認が完了していない。Geminiの版と読取り専用挙動は未確認と明記され、agyも最終出力取得まで成功した実機証跡を確認できない。フラグ文字列のdoctor検出と偽Reviewerの成功では、要求された実機確認を満たさない。 | 対象CLIの実機版で読取り専用・非対話起動と最終JSON取得まで確認し、版・フラグ・観察結果をdesign.mdに記録する。実行不能の経路は未完了として維持する。 |
| F-004 | 新規 | medium | missing | T-5.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:42 | summary.mdに全受入基準IDが含まれない。summary_markdownはGate推移・残余Finding・提案だけを生成するため、基準IDはFinding等で偶然言及されない限り欠落する。正常なレビューJSONからのメモリ上の生成でも基準IDの欠落を確認した。 | summary.mdにも固定基準IDと最終判定、または全基準IDを確認できる一覧を出力し、round文書とsummaryの双方に全基準IDが含まれることを検証する。 |
| F-005 | 新規 | medium | test-gap | T-7.2 | openspec/changes/add-spec-review-loop/tasks.md:40; openspec/changes/add-spec-review-loop/implementation-record.md:26 | 実機通し実行の完了を独立に確認できる証跡が指定roundにない。implementation-record.mdは外部一時リポジトリでの実行を説明するだけで、対応するreview JSONやsummary.mdが含まれない。本change自体の通し実行も今回のレビュー時点では完了していないため、tasks.mdの完了表示を裏付けられない。 | 実際のchangeでの通し実行後、Reviewerのツール・モデル・round SHA・Gate推移を確認できるreview JSONとsummary.mdをレビュー可能な場所に残す。それまでは7.2を未完了として扱う。 |
| F-006 | 新規 | medium | missing | S-spec-review-loop-7.4 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:63 | PASS以外でfinishする場合、trailerに残余Findingが記録されない。Spec-Review-Residualは利用者の受容文を転記するだけで、未解決FindingのIDや内容とは結び付いていない。summaryには残余Findingが出るが、trailerにも記録するというScenarioを満たさない。 | 最終レビューの未解決FindingからID一覧を抽出し、受容文とともにtrailerへ記録する。残余Findingを含む非PASSのfinish --accept-residual --confirmで、summaryとcommit trailerの双方に残ることを検証する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準を指定SHAで照合した。必須checkはPASSだが、squash復元、不正Reviewer出力の処理、成果物の必須情報に未達がある。代替CLIの実機確認も未完了で、T-7.2は証跡不足のためUNVERIFIED。読み取り検査と副作用のない再現検査を行い、作業ツリーに変更はない。
