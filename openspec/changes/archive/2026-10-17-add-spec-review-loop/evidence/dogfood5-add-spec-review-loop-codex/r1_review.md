# spec-review r1: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-4.2, T-5.1, T-6.1, S-spec-review-loop-4.3; T-4.1: UNVERIFIED）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `864e6ea2cf6c316093dfb9e03f560b0814307bcc`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:7 に必須項目、同:26以降に各判定・Finding・提案を定義。tests/test_schema_contract.py:35-81で正常、必須項目欠落、ID重複・欠落・順序・原文変更を検査している。必須CHK-PYTESTはPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5-49に指定の契約が存在。tests/test_schema_contract.py:84-106でスキーマ項目、状態enum、Gate規則との対応を検査している。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:38-135に抽出処理。読取り専用のpython3 -B検査でarchive済み4件を独立に数え、タスク／Scenarioが37／25、5／5、15／18、11／23で一致し、抽出タスク先頭行と全Scenario本文を原文に照合した。tests/test_criteria.py:15-49の期待件数とも一致。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:25-26、48、190-200でチェックボックスを除いた原文をSHA-256化。tests/test_criteria.py:64-77に状態変更と本文変更の検証がある。今回の読取り専用再抽出でも19タスク・24Scenario・2checkの指紋が指定値と一致した。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:73-105で開始検査とbase記録、gitops.py:80-98で報告必須・未stage拒否・trailer付与。tests/test_gitops.py:19-72が指定の拒否と正常commitを検証している。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101-112でround SHAのdetached worktreeを作りfinallyで削除。tests/test_gitops.py:75-91で成功・失敗・timeout・例外後のworktree一覧を検査している。 |
| T-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30-135で計画・前提検査・バックアップ・tree照合・復元、gitops.py:165-180でsoft resetと復元を実装。tests/test_gitops.py:101-164、191-203、236-295に正常系と各拒否・復元の検査がある。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:138-151で対象refとSHAを計算しconfirm時だけ削除。render.py:95-99で表示。tests/test_gitops.py:178-188で確認前の保持と確認後の削除を検証している。 |
| T-4.1 | UNVERIFIED | openspec/changes/add-spec-review-loop/design.md:146-159にOpen Questionの解消、3 CLIの版・フラグを記載。runtime/spec_review_loop/reviewers.py:78-127に検出処理、tests/test_reviewers.py:23-35、62-71に偽CLIによる検証がある。Codex／Cursorの実行記録はevidence配下に存在するが、Claudeの実機確認はimplementation-record.md:34の申告以外の実行記録を確認できず、3 CLIすべての実機確認は確証を得られない。 |
| T-4.2 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:144-168に共通実行処理、tests/test_reviewers.py:23-35に3経路の正常系がある。ただし読取り専用のメモリ内模擬実行で、Claude／Cursorがstdoutに[]を返すとrunがAttributeErrorを送出し、失敗結果を返さないことを再現した。F-002参照。 |
| T-5.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:28-96に構造検証と優先順位があるが、review_round.py:101-116のReviewer失敗・不適合経路では実行済みcheck結果を渡さない。メモリ内模擬実行でCHK-VALIDATE=FAILとReviewer timeoutを与えるとGate=INCONCLUSIVE、review=nullとなり、FAIL優先とcheck記録が失われた。F-001参照。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:113-138にPASS・停滞・上限の停止判定。tests/test_gate.py:143-180で2 round目PASS、同じFinding、round上限、未解消数非減少を検証している。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:14-80でレビューと要約を生成。tests/test_report.py:16-40で基準ID・Gate・Finding・提案・Reviewer・SHAを検査。summaryの全基準表はreport.py:65-70に実装されている。 |
| T-6.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/cli.py:18-85に全サブコマンド、tests/test_cli.py:9-72に各終了コードの検査がある。しかしF-002の不正なReviewer応答はreviewers.runからAttributeErrorが漏れ、cli.py:95-97によって内部エラー4となる。Reviewerの入出力失敗として3を返しroundを記録する経路を通らない。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3-4に適用範囲・正例・非発火例、同:13-74に経路の使い分け・実装手順・停止・終了確認を記載。tests/test_skill.py:13-25で形式と手順を検査している。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.jsonのactivation_casesに起動3件・非起動4件が存在する。tests/test_skill.py:28-35で件数・ID一意性・判定型を検査している。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:9-50が偽ReviewerによるFAIL→PASS→finishを通しで実行し、2 commitから1 commitへの集約・backup tree一致・summary・trailer・clean状態を検証。必須CHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/summary.md:12-15に実change add-slugifyのFAIL→PASS、codex-cli 0.160.1、gpt-6-lunaと両round SHAが記録されている。同ディレクトリのr1_review.json・r2_review.jsonとsquash_commit.txt:4-8にもGate・Reviewer・round数・最終SHAの証跡が存在する。 |
| T-7.3 | PASS | 必須CHK-VALIDATEは指定round SHAでexit 0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac 864e6ea2cf6c316093dfb9e03f560b0814307bccを確認し、変更はopenspec/changes/add-spec-review-loop/とquality-loop/skills/spec-review-loop/の98ファイルのみで、指定された既存QA経路・記録の変更はなかった。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:26-38で対象changeの存在確認後のstartを定義。runtime/spec_review_loop/criteria.py:29-35でもchange存在を必須とし、tests/test_cli.py:13で存在しないchangeの拒否を検証している。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4、22で非起動条件を明記し、evals/evals.jsonに説明・一般レビュー・applyの非起動例がある。SHA間差分にも既存QA記録の変更はない。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:38-135で原文順のIDを付与し、render.py:23-31で一覧表示。tests/test_criteria.py:52-61でID順序を、tests/test_cli.py:9-11で一覧出力を検証している。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:48でチェックボックス以降の番号から原文を保持。tests/test_criteria.py:64-69でチェック状態変更時にドリフトしないことを検査している。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:135-137で変更ID付きHOLD拒否、review_round.py:88-90、124-139でround SHAのドリフトをHOLDとして記録し停止する。tests/test_gate.py:87-112、219-238に変更・全削除・refreezeの検証がある。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:203-211で0基準を拒否し、session.py:94で状態保存より先に抽出する。startにはcommit操作がない。tests/test_criteria.py:93-98で基準なし拒否を検証している。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、46-50でmain/masterを拒否しtopic branchを案内。session.py:75で開始時に呼ぶ。tests/test_gitops.py:19-24でmaster拒否と成果物未作成を検証している。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82-85で実装報告なしをcommit前に拒否。tests/test_gitops.py:39-43で拒否とbase以降commit 0件を検証している。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86-91で自動収集対象review/以外のunstaged／untrackedをpath付きで拒否。tests/test_gitops.py:46-57で両状態のpathを確認している。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16、36-41でCodex既定とread-only起動、review_round.py:94-100、132-135でworktree実行とReviewer情報記録。tests/test_reviewers.py:23-35でcwd・フラグ・記録を検証している。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:106-127で未導入と必要フラグ不足を検出し、review_round.py:79-82でdoctor結果と導入・切替案を返す。tests/test_gate.py:131-138でattempt未作成を確認している。 |
| S-spec-review-loop-4.3 | FAIL | 通常の失敗・timeout・不正本文はtests/test_gate.py:117-128、202-210で検証されるが、runtime/spec_review_loop/reviewers.py:58-59はstdout JSONの型を検査しない。Claude／Cursorのstdout=[]を与えたメモリ内模擬実行でrunからAttributeErrorが漏れることを再現し、review_round.py:100以降のround記録・再試行設定へ到達しない。F-002参照。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:34-44で基準ID・順序・原文を照合。tests/test_schema_contract.py:60-81とtests/test_gate.py:30-38で欠落・重複を構造不適合とし、有効reviewを採用しないことを検証している。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:83-95で有効reviewのFAILを未実行状態より優先。tests/test_gate.py:53-59で基準FAIL＋NOT_RUNを直接検査し、同:41-50でERROR併存時の記録も検査している。F-001は有効reviewを得られない別経路の不具合。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11-25で基準外Findingを提案へ移す。tests/test_gate.py:65-71でFindingからの除外、Gate PASS、Markdownの提案欄掲載を確認している。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:117-118でPASS停止。session.pyのnext_actionでfinishと人によるarchive判断を案内し、tests/test_gate.py:143-147で2 round目PASSと案内を検証している。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:119-138で同一Findingの停滞を判定。render.py:59-67で内容と引継ぎを表示。tests/test_gate.py:150-158でF-002による上限前停止・引継ぎ・次round拒否を検証している。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:122-123で上限停止、session.py:108-118で停止後の次roundを拒否。tests/test_gate.py:161-172が3 roundで停止し4 round目を拒否することを検証。render.py:59-67でFindingと選択肢を表示する。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:68-83、87-121で確認・summary追加・ref保存・squash・tree照合・trailerを実装。tests/test_integration.py:33-49とtests/test_gitops.py:101-116で結果を検証している。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:59-64で全round commitのremote ref到達性を確認し、明示承認と手作業を案内して拒否。tests/test_gitops.py:119-126で拒否とHEAD不変を検証している。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:113-135でtree不一致からバックアップ復元とfinish前の状態復元を行う。tests/test_gitops.py:147-164でtree改変を模擬し、HEAD・内容・stateの復元と再実行可能性を検証している。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:39-42、72-76で受容の明示を要求し残余Finding trailerを生成。report.py:51-75でGateと残余を要約。tests/test_gitops.py:167-175、206-233に拒否・記録・直近レビュー失敗時の引継ぎ検証がある。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:31-34で成果物をchange内review/へ配置し、finish.py:101-106でsummaryを追跡対象に追加。tests/test_integration.py:44-48でSHA・Gate推移とreview成果物のcommit収録を検証。SKILL.md:79にもchangeとともに保存する契約がある。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:138-151で確認前は削除せず対象ref・到達不能SHAを返し、render.py:95-99で表示。tests/test_gitops.py:178-188でround SHAの表示対象入りと確認前後のref保持・削除を検証している。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | medium | defect | T-5.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:101 | Reviewerが失敗した場合、実行済み必須checkの結果が捨てられる。run_checks後の失敗経路はcheck結果を_finish_roundへ渡さず、gate.decide(None)によって常にINCONCLUSIVEとなる。ファイル書込みを無効化したメモリ内模擬実行で、CHK-VALIDATE=FAILとReviewer timeoutの組合せからGate=INCONCLUSIVE、review=null、check結果を持たないround記録が返ることを再現した。必須checkのFAILを優先するGate規則を満たさず、失敗理由の証跡も失われる。スキーマ不適合・書込み検出の経路にも同じ問題がある。 | Reviewer出力の有効性と独立にCLIのcheck結果をround記録へ保持し、Reviewer失敗時もHOLD > FAIL > INCONCLUSIVEの優先順位で判定する。必須check FAILとtimeout・不適合出力が併存する回帰テストを追加し、JSONとMarkdownにcheck状態・理由が残ることも検証する。 |
| F-002 | 新規 | medium | defect | T-4.2, T-6.1, S-spec-review-loop-4.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:58 | Claude／Cursorのstdout JSONが配列やnullの場合、final_textはオブジェクトと仮定して.getを呼び、AttributeErrorがrunの例外処理から漏れる。Claudeのモデル名推定にも同様の仮定がある。subprocessと一時出力先をメモリ内で置き換え、終了コード0・stdout=[]で両アダプタのrunがAttributeErrorを送出することを再現した。この場合はroundのINCONCLUSIVE記録も1回の再試行制御も行われず、CLIの内部エラー4となる。 | stdoutのJSONを利用する前にオブジェクト型を確認し、型不適合をValueErrorなどの処理対象へ変換する。モデル名取得を含む応答解釈の失敗をok=Falseへ統一し、配列・nullなどの応答でもroundがINCONCLUSIVEとして記録され、再試行は1回、CLI終了コードは3となるテストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準を指定順序・原文で確認した。通常経路と抽出・squashの検証は揃っているが、Reviewer失敗時のcheck結果消失と、不正なCLI応答での例外漏れを再現した。Claudeの実機確認は申告以外の証跡を確認できずUNVERIFIED。確認終了時の作業ツリー差分はなく、ファイル変更・ネットワーク利用は行っていない。
