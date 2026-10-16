# spec-review r1: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-3.3, T-5.1; T-4.1: UNVERIFIED）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `72a2eca28b21ef402c5f2b6f1dcbe7d661e8596d`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:7 以降に必要項目と列挙値を定義。tests/test_schema_contract.py:42 以降に正常・欠落・重複・原文変更の検証がある。重複はgate.structural_errorsで検出する構成。提示されたCHK-PYTESTもPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5 以降に読取り専用、基準の原文・順序、根拠、提案への格下げ、前round Findingの4状態での再判定を規定。tests/test_schema_contract.pyのtest_contract_items_map_to_schema_or_gate_rulesで対応を検証している。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:42 以降で抽出する。python3 -Bによる読取り検査でarchive済み4件を独立集計し、タスク/Scenarioが37/25、5/5、15/18、11/23で一致。全タスクの先頭原文と全Scenario本文の原文一致も確認した。tests/test_criteria.py:16 に対応する期待件数がある。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:29 のsha256と_with_fingerprintsで原文をハッシュ化し、driftでID別指紋を比較する。tests/test_criteria.pyのtest_checkbox_toggle_keeps_fingerprint、test_one_character_change_is_drift、空白変更の回帰テストを確認。提示CHK-PYTESTはPASS。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:76 以降でtopic branch・対象外差分を検査しbase SHAを保存。gitops.pyのcommit_roundで実装報告、未stage/untracked、trailerを扱う。tests/test_gitops.py:19 以降に各拒否系と正常commitの検証がある。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.pyのreview_worktreeはfinallyでworktree remove、prune、一時ディレクトリ削除を行う。tests/test_gitops.pyのtest_worktree_is_removed_after_reviewが成功・失敗・timeoutを、test_worktree_is_removed_on_exceptionが例外を検証する。 |
| T-3.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:96 でsquash成功前にstatus=finishedを保存するため、108/114行の復元後もfinishedが残る。副作用のないインメモリ模擬でtree不一致後にstatus=finished、finish.squash=pendingとなり、finish再試行は「squash済み」で拒否、statusはarchiveを案内することを再現。既存復元テストはHEAD/treeだけを検証しており、この状態不整合を検出しない。F-002。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:121 以降で削除対象refと到達不能SHAを計算し、confirm時だけdelete_refを実行する。tests/test_gitops.pyのtest_prune_requires_confirmationでdry-run時の保持と確認後の削除を検証する。 |
| T-4.1 | UNVERIFIED | openspec/changes/add-spec-review-loop/design.md:150-159 に3 CLIの版・フラグ・取得方法を記載し、runtime/spec_review_loop/reviewers.pyのprobeが必要フラグを検査する。Codex/Cursorはevidence/sandbox-add-slugify-{codex,cursor}/に実行結果がある。一方、Claudeの実機実行はimplementation-record.mdの申告以外に対応する実行出力・レビュー記録を確認できず、3 CLIすべての実機確認は独立に検証できない。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:26 以降のAdapterとrunで3経路を実装。tests/test_reviewers.py:24 以降で3ツールのcwd・フラグ・出力・モデルを検証し、未導入・必要フラグ欠落時の案内も検証する。cli.pyのdoctorが全probe結果を返す。 |
| T-5.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:48-54 はproposals内のIDを前round Findingの再判定として受理する。python3 -Bでprevious_open=[F-001]、findings=[]、proposals=[F-001]、全基準/check PASSを入力するとstructural_errors=([],[])、Gate=PASSとなった。契約で必須のstatus付き再判定を省略できる。F-001。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.pyのstop_decisionと_stalledがPASS、HOLD、同一Findingの未解消、未解消数非減少、round上限を扱う。tests/test_gate.pyのtest_pass_in_round_two_stops、test_same_finding_unresolved_twice_stops_before_limit、test_round_limit_stops_without_fourth_round、test_non_decreasing_open_count_is_stagnationに対応する検証がある。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:16 以降でroundレビュー、summary_markdownでGate推移・全基準・残余Finding・提案を生成する。tests/test_report.py:16 以降で全ID、SHA、Gate、Reviewer情報を検証する。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1 が同梱runtimeを起動。runtime/spec_review_loop/cli.py:20 以降に8サブコマンド、execute/mainに終了コード処理がある。tests/test_cli.py:10 以降で成功、契約拒否、Reviewer失敗、破損state、内部例外の終了コードを検証する。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3 のdescriptionに現在メッセージでの明示依頼、正例、非起動例を記載。本文に使い分け、実装・報告・commit-round・review、停止時の引継ぎを記載。tests/test_skill.pyのdescriptionと本文の検査も確認した。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:28 以降のactivation_casesに起動例3件、非起動例4件を確認。tests/test_skill.pyのtest_evals_have_three_or_more_positive_and_negative_casesで件数とID一意性を検証する。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:10 のtest_fail_then_pass_then_finishがCLI経由でFAIL→PASS→finishを実行し、2 roundから1 commitへの整理、バックアップとのtree一致、summaryの両SHAとGate、各trailerを検証する。提示CHK-PYTESTもPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/r1_review.json、r2_review.json:5 以降にCodex実行attemptとレビュー結果がある。同ディレクトリsummary.md:14-15 にFAIL→PASS、round SHA、ツール・版・モデルを記録し、squash_commit.txtに対応するtrailerを保持している。 |
| T-7.3 | PASS | 提示されたCHK-VALIDATEはexit_code=0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac 72a2eca28b21ef402c5f2b6f1dcbe7d661e8596dを確認し、変更先は本changeとquality-loop/skills/spec-review-loop配下のみ。既存4 Skill・既存QA記録の変更はない。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.mdの「0. 起動前の確認」で対象changeの存在確認を先行させる。runtime/spec_review_loop/session.py:29 とcriteria.py:33 のchange_dirでも存在を検査し、tests/test_cli.py:14 で存在しないchangeを拒否する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3 のdescriptionと「起動しない例」で説明・一般レビュー・applyのみを除外する。evals/evals.jsonのsrl-explain-only、srl-general-review、srl-openspec-apply-onlyはすべてexpected_trigger=false。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:42 以降でタスク、_scenarios_inでScenarioを出現順にID化。render.py:24 の_startが一覧を表示する。tests/test_criteria.pyのtest_ids_order_and_text_in_demo_changeとtests/test_cli.py:10 で順序・表示を検証する。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:54 はタスク番号以降を原文とするためチェック状態を含めない。tests/test_criteria.pyのtest_checkbox_toggle_keeps_fingerprintでドリフトなしを検証し、test_integration.pyでも完了チェック変更後にr2が成功する。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.pyのcommit_roundはドリフト時にHOLDを示す契約拒否を返す。review_round.py:88 以降でもround SHA上のドリフトをHOLDとして記録する。tests/test_gate.pyのドリフト・全基準削除・refreeze再開テストを確認した。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.pyのbuildは基準0件をcontractで拒否する。session.pyのstartはbuild成功後にstateを書き、commit操作を含まない。tests/test_criteria.pyのtest_no_criteria_is_rejectedを確認した。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.pyのDEFAULT_BRANCHESはmain/masterで、ensure_topic_branchが切替案内付きで拒否する。tests/test_gitops.py:19 とtests/test_cli.py:16 にmaster拒否の検証がある。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.pyのcommit_roundは報告の存在・空本文をgit add/commitより前に検査する。tests/test_gitops.py:40 で報告なし拒否とbase以降commit数0を検証する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.pyのcommit_roundがreview成果物以外のunstaged/untrackedを列挙して拒否する。tests/test_gitops.py:49 でnew.pyとapp.pyのpath、状態表示を検証する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:17 の既定はcodex、Adapter.commandは--sandbox read-onlyと-Cを指定する。review_round.py:96 以降でround SHAのworktreeを渡し、132行以降でツール・版・モデルを保存する。tests/test_reviewers.py:24 以降で既定経路のフラグと記録を検証する。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:80 以降でprobe失敗をReviewer起動前に拒否し、doctor詳細、導入・切替方法を返す。tests/test_gate.pyのtest_missing_reviewer_cli_does_not_reviewとtests/test_reviewers.pyのprobe拒否テストを確認した。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:15 のMAX_ATTEMPTS=2と_finish_roundが失敗をINCONCLUSIVE、最大1回再試行として記録する。tests/test_gate.pyのtest_reviewer_failure_is_inconclusive_with_single_retryがfail・garbage・timeout・writeを検証する。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:31-41 は基準ID列全体を比較し、欠落・重複を構造不適合とする。review_round.pyでは不適合出力をreview=Noneとして保存する。tests/test_gate.py:30 とtests/test_schema_contract.pyの重複・欠落テストに対応する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:79 以降はFAIL判定をpending判定より優先し、_pending_reasonsも残す。tests/test_gate.pyのtest_decide_priority_and_not_runでFAILとNOT_RUNの併存を、test_fail_and_not_run_coexist_gives_failでERROR併存時の記録を検証する。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11-22 が基準と対応しないFindingをproposalsへ移し、open_findingsはfindingsのみを数える。tests/test_gate.pyのtest_out_of_scope_request_becomes_proposalでGate PASSとMarkdownへの提案記載を検証する。既存Findingの再判定省略は別途F-001。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.pyのstop_decisionはPASSで停止し、session.py:174-177 のnext_actionがfinishとarchiveの人による判断を案内する。tests/test_gate.pyのtest_pass_in_round_two_stopsで検証する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.pyの_stalledが前roundのopen IDと今回unresolvedを照合する。tests/test_gate.pyのtest_same_finding_unresolved_twice_stops_before_limitはF-002で停滞停止、引継ぎ案内、次round拒否を検証する。render.pyの_reviewがFinding内容を表示する。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.pyのstop_decisionはround_no>=max_roundsで停止する。session.pyのcommit_roundにも上限検査があり、render.pyの_reviewが残FindingとHANDOFFを表示する。tests/test_gate.pyのtest_round_limit_stops_without_fourth_roundを確認した。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:87-118 に確認付きsummary追加、バックアップ、squash、tree比較を実装し、planでtrailerを構成する。tests/test_integration.py:10 以降とtests/test_gitops.pyのtest_finish_dry_run_then_squashが正常系を検証する。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.pyのplanが全対象commitについてremote_refs_containingを確認し、force-pushと別途承認・手作業の説明付きで拒否する。tests/test_gitops.pyのtest_finish_rejects_pushed_roundsでHEAD不変も検証する。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:112-117 はtree不一致でrestoreを呼びio_errorを返す。tests/test_gitops.pyのtest_finish_restores_on_tree_mismatchはHEAD、tree、clean、改変ファイル復元を確認する。バックアップに早期保存されたfinished状態が残る問題はT-3.3/F-002として区別した。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.pyのplanはPASS以外でaccept_residual必須とし、Gate・残余Finding・受容理由をtrailerへ記録する。tests/test_gitops.pyのtest_non_pass_finish_records_residual_findings_in_trailerとtest_residual_findings_carry_over_when_last_review_failedで検証する。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:29-35 は成果物をchange直下のreviewに配置し、finish.py:95-100 でsummary等を追跡する。tests/test_integration.pyは最終treeにreview成果物一式と両round SHA・Gate推移が残ることを検証する。changeフォルダ全体のarchiveで証跡を同梱できる配置である。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:121 以降でref・到達不能SHAを返し、render.pyの_pruneが表示する。confirmなしでは削除しない。tests/test_gitops.pyのtest_prune_requires_confirmationとtests/test_cli.pyのprune正常系で検証する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | medium | defect | T-5.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:48 | 前roundの未解決Findingについて、findingsから省略して同じIDのproposalsを返すだけで再判定済みとして受理される。previous_open=[F-001]、findings=[]、proposals=[F-001]の読取り専用再現で構造エラーなし、Gate PASSになった。契約で要求するresolved/unresolved/unverified/withdraw-proposedの判定と根拠を残さず、未解決Findingを停滞判定から消せる。 | 前round IDの再判定を提案への格下げ前のfindingsで検証し、許可された再判定statusを必須にする。既存Findingのproposalsへの直接移動や、newのままの自動格下げを再判定完了と扱わない回帰テストを追加する。 |
| F-002 | 新規 | medium | defect | T-3.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:96 | squashとtree一致確認より前にstatus=finishedをsummary commitとバックアップへ保存する。squash失敗またはtree不一致でバックアップへ復元すると、実際にはround commit群が残っているのにfinished状態になり、statusは「squash済み」とarchiveを案内し、finishの再試行も拒否する。インメモリのtree不一致模擬で、restore実行後もfinished/pendingが残り、この誤案内と拒否を再現した。 | 失敗復元後は未完了・復旧待ちと分かる状態にし、statusが成功を案内しないようにする。summary commitを含む復旧後の履歴を考慮した再試行経路を定義し、tree不一致とcommit失敗の両テストで状態・次操作・再試行まで検証する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準を照合し、構造検証での前round Finding再判定の迂回と、squash失敗復元後の完了状態の誤記録を確認した。必須checkは両方PASSだが、T-5.1とT-3.3は未達。Claude実機確認は独立した実行証跡がなくUNVERIFIED。ファイル変更・依存導入・ネットワーク利用は行っていない。
