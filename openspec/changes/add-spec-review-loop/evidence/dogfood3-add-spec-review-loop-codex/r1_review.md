# spec-review r1: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-2.2, T-3.3, S-spec-review-loop-2.3, S-spec-review-loop-7.1）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `d71d81cf366e9da0bb7aafe42c9d24676b309ef8`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:1 に指定された項目・列挙値がある。tests/test_schema_contract.py:23 以降で正常例、必須項目欠落、列挙値違反、基準IDの欠落・重複・順序違いを検査している。IDと原文の照合はruntime/spec_review_loop/gate.py:26 以降が担う。提示されたCHK-PYTESTもPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:1 以降に読取り専用、ID・原文・順序、evidence、提案への格下げ、既存Findingの再判定、Gate優先順位が明記されている。tests/test_schema_contract.py:test_contract_items_map_to_schema_or_gate_rules が契約とスキーマ・Gateの対応を検査している。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:34、77、122 に抽出・ID付与がある。python3 -Bによる読取り専用照合でarchive済み4件のタスク／Scenario件数が37／25、5／5、15／18、11／23となり、独立した行数カウントと一致した。各タスク本文・継続行と各Scenario本文もsourceの行番号から再構成して全件一致を確認した。 |
| T-2.2 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:44、53 が本文をstripしてから、179-184でSHA-256を計算している。実ファイルを作らない仮想入力で「- [ ] 1.1 実装する」と、その本文末尾に空白1文字を加えた入力をextract_tasksへ渡したところ、どちらもtextが「1.1 実装する」となりSHAが一致した。チェックボックス以外の原文変更も消されるためF-002。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:73-105 がbranch・対象外dirtyを検査してbase SHAを保存する。gitops.py:80-98 が報告必須、review配下以外のunstaged／untracked拒否、review成果物のstage、round trailer付きcommitを実装する。tests/test_gitops.pyに指定された拒否系・正常系があり、提示されたCHK-PYTESTはPASS。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101-112 が指定SHAのdetached worktreeを作り、finallyでremove・prune・一時ディレクトリ削除を行う。tests/test_gitops.py:test_worktree_is_removed_after_review が成功・失敗・timeoutを、test_worktree_is_removed_on_exception が例外を検査する。 |
| T-3.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30-113 にdry-run・バックアップ・squash・tree比較・復元はある。しかし48-49のcommit検査はtrailerの前方一致だけで、stateに記録されたレビュー済みSHAとの一致を検査しない。読取り専用のインメモリ再現で、PASS済みSHAをa×40、実際のcommitをb×40、同じ「demo r1」trailerとしたところplanが拒否せず受理した。amend後の未レビュー実装をPASSとしてsquashできるためF-001。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:116-129 がrefと到達不能候補SHAを計算し、confirmがない場合は削除しない。render.py:95-99 が確認対象を表示する。tests/test_gitops.py:test_prune_requires_confirmation がdry-runでの保持と確認後のref消失を検査する。 |
| T-4.1 | PASS | openspec/changes/add-spec-review-loop/design.md:146-162 にOpen Questionの解消と3 CLIの版・フラグ・出力取得方法が記載されている。runtime/spec_review_loop/reviewers.py:78-127 が対応する版・必要フラグを検査する。evidence/sandbox-add-slugify-codex/r2_review.jsonとevidence/sandbox-add-slugify-cursor/r2_review.jsonに実行attempt・版・モデル・Gateがあり、tests/test_reviewers.pyは未対応フラグの検出も検査する。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:25-61、144-168 に共通Adapter、3経路、stdin・cwd・timeout・最終出力の処理がある。cli.py:54-62 がdoctorを実装する。tests/test_reviewers.py:test_each_adapter_runs_read_only_in_worktree は3経路をパラメータ化し、未導入時のinstall hintも検査している。 |
| T-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12-92 に提案の格下げ、基準IDの完全な順序照合、原文の完全一致、SHA・指紋照合、Gate優先順位がある。tests/test_schema_contract.pyとtests/test_gate.pyが欠落・重複、FAILとNOT_RUNの併存、範囲外指摘の提案化を検査する。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:108-134 がPASS、停滞、round上限を判定し、session.py:128-134 が次roundを制限する。tests/test_gate.pyに2 round目PASS、F-002連続未解消、未解消数非減少、3 round上限と4 round目拒否の検査がある。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:14-80 がJSON・stateから基準ID、Gate、Finding、提案、Reviewer、SHAを含むMarkdownを生成する。tests/test_report.py:16-40 がレビュー文書のFinding・提案と要約の基準ID・Gate推移・SHAを検査する。evidence/sandbox-add-slugify-cursor/summary.mdにも基準表とGate推移がある。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1 がruntimeを起動し、runtime/spec_review_loop/cli.py:18-106 に全8サブコマンドと終了コード処理がある。tests/test_cli.pyは正常系、契約拒否、Reviewer失敗・破損JSONの3、模擬内部エラーの4を検査する。refreeze正常系はtests/test_gate.pyでも検査される。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:1 のdescriptionに現在のメッセージでの明示依頼条件、正例、非起動例があり、本文に実装・報告・commit-round・review・停止・引継ぎと既存QA経路の使い分けがある。tests/test_skill.py:13-25 が形式と必要な手順を検査する。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:1 のactivation_casesに起動例3件、非起動例4件がある。tests/test_skill.py:28-35 がID一意性、発話・理由、各3件以上を検査する。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:10-50 が偽Reviewerでr1 FAIL、r2 PASS、finishを実行し、2 round commitから1 commitへの集約、バックアップとのtree一致、Gate・round数・Reviewer・SHAのtrailer、summaryのGate推移、成果物の追跡を検査する。提示されたCHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/r1_review.json、r2_review.jsonにCodex実行attempt、codex-cli 0.160.1、モデル名、FAIL／PASSとFinding再判定が記録されている。同ディレクトリのsummary.md:1 にround SHAとFAIL→PASSの推移、squash_commit.txt:1 に最終trailerが残る。実装報告だけでなく保存されたレビューJSONと要約を照合した。 |
| T-7.3 | PASS | 提示されたCHK-VALIDATEはexit_code 0でPASS。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac d71d81cf366e9da0bb7aafe42c9d24676b309ef8を確認し、変更は新Skillとopenspec/changes/add-spec-review-loop配下に限定され、指定された既存Skill・既存QA記録の変更はなかった。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:1 の起動条件と「0. 起動前の確認」に対象changeの特定・存在確認がある。runtime/spec_review_loop/session.py:28-31 はSession作成時にcriteria.change_dirを呼び、criteria.py:25-31が不正ID・不存在changeを拒否する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:1 と非起動例が説明・一般レビュー・OpenSpec applyだけの依頼を明示的に除外する。evals/evals.jsonのsrl-explain-only、srl-general-review、srl-openspec-apply-onlyはexpected_trigger=false。Git差分にも既存QA経路の記録変更はない。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:41-69、95-134 が原文順でタスク・Scenario IDを付け、192-207が一覧を構築する。render.py:23-31 がstart時に全基準のIDと見出しを表示する。tests/test_criteria.py:test_ids_order_and_text_in_demo_change がID順序と本文を検査する。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:42-45、64 はチェックボックス状態をtextに含めない。tests/test_criteria.py:test_checkbox_toggle_keeps_fingerprint が[ ]→[x]でドリフトしないことを検査し、tests/test_integration.pyでもr2でチェックを更新して継続する。 |
| S-spec-review-loop-2.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:135-137、review_round.py:88-90 は検出されたドリフトをHOLDにするが、criteria.py:44、53、120、132 が原文の空白を削ってから指紋を作る。インメモリ再現では本文末尾の空白1文字変更が同一SHAとなった。指定された原文指紋に基づく変更検出を満たさず、この変更でHOLDにならないためF-002。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:192-200 が基準0件を契約拒否にする。session.py:94 はstate保存前に抽出し、startにはcommit操作がない。tests/test_criteria.py:test_no_criteria_is_rejected がタスク・Scenarioの両方がない場合を検査する。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、46-50 がmain／masterを拒否してtopic branchへの切替方法を返す。session.py:75 がstart冒頭で呼ぶ。tests/test_gitops.py:test_start_rejects_default_branch はmaster拒否とstate未作成を検査する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82-85 が報告の存在・空本文を検査し、commit前に作成を求める。tests/test_gitops.py:test_commit_round_requires_report は拒否とbase以降のcommit数0を検査する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86-91 が自動収集するreview成果物以外のunstaged／untrackedを拒否し、details.pathsとstage／除外の案内を返す。tests/test_gitops.py:test_commit_round_rejects_untracked_and_unstaged はnew.pyとapp.pyのpathを検査する。review成果物の自動stageはdesign.md:71に明記されている。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16、36-41 が既定Codexと--sandbox read-onlyを定義する。review_round.py:94-100 がround SHAのworktreeで実行し、132-135でtool・version・modelを保存する。tests/test_reviewers.pyがcwd・フラグ・記録情報を検査する。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:106-127 がCLI不存在と不足フラグを検出し、review_round.py:79-82 が実行前にdoctor情報・導入／切替案内付きで拒否する。tests/test_gate.py:test_missing_reviewer_cli_does_not_review はattemptが追加されないことも検査する。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:151-167 が起動失敗・timeout・出力不適合を返し、review_round.py:101-116、123-135 がINCONCLUSIVEと最大2 attemptsを記録する。tests/test_gate.py:test_reviewer_failure_is_inconclusive_with_single_retry が失敗・不正出力・timeout・書込みと3回目拒否を検査する。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:32-38 が基準ID列の欠落・重複・追加・順序違いを構造不適合にする。review_round.py:113-116 はその出力をreview=Noneとして扱い、通常の基準別Gate判定には使用しない。tests/test_schema_contract.pyとtests/test_gate.py:test_missing_criterion_id_is_not_gated が検査する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:82-92 はFAILをpending状態より優先し、pending理由も保持する。report.py:29-30 がcheckごとの状態・終了code・理由を表示する。tests/test_gate.py:test_decide_priority_and_not_run がFAILとNOT_RUNの併存を検査する。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12-23 が既知の基準・checkに対応しないFindingをproposalsへ移す。Gateと停滞は提案を参照せず、report.py:38-39 が提案欄を生成する。tests/test_gate.py:test_out_of_scope_request_becomes_proposal がPASSとMarkdown記録を検査する。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:112-113 がPASSで停止し、session.py:174-177 がfinishと利用者によるarchive判断を案内する。tests/test_gate.py:test_pass_in_round_two_stops がr2 PASSの停止と案内を検査する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:122-129 が前roundの未解決Findingと同じIDのunresolvedを停滞とする。session.py:180-181 が引継ぎ選択肢を返す。tests/test_gate.py:test_same_finding_unresolved_twice_stops_before_limit がF-002と次round拒否を検査し、dogfoodのr2証跡にも停滞停止が記録されている。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:117-118 が上限到達で停止し、session.py:108-118、133-134 が次roundを拒否する。tests/test_gate.py:test_round_limit_stops_without_fourth_round はr3 INCONCLUSIVEと4 round目拒否を検査する。 |
| S-spec-review-loop-7.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:48-49 はcommitのtrailerだけを確認し、レビュー済みround SHAと現在の履歴を照合しない。インメモリ再現でPASS済みSHAとは異なる同trailerのamend後SHAをplanが受理した。88-101はその履歴をsquashし、64-66は旧roundのPASSとSHAをtrailerへ記録するため、レビューしたtreeと異なる実装をPASS付きで仕上げられる。F-001。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:54-59 が全commitについてremote_refs_containingを呼び、公開済みなら変更前に拒否し、別途の明示承認と手作業を案内する。gitops.py:134-136 がrefs/remotesからの到達性を検査する。tests/test_gitops.py:test_finish_rejects_pushed_rounds がHEAD不変も検査する。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:107-112 がtree不一致でrestoreし、復元先を含む入出力エラーを返す。gitops.py:172-180 がHEAD・index・作業ツリーをバックアップへ戻す。tests/test_gitops.py:test_finish_restores_on_tree_mismatch が改変を模擬してHEAD・tree・clean状態の復元を検査する。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:39-42 が明示受容を必須にし、67-71 がGate・残余Finding・利用者判断をtrailerへ記録する。report.py:54-75 が要約へ残す。tests/test_gitops.pyは非PASS時の拒否、残余trailer、最終レビュー失敗時の前round Finding引継ぎを検査する。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:31-34 が成果物をchange内のreview/へ配置し、finish.py:90-95 がsummaryを含むreview成果物をcommitする。report.py:56-61 が全roundのSHAとGate推移を保存する。tests/test_integration.py:43-50 がsummaryと各成果物のGit追跡を検査する。archive実行はSkillで利用者の判断に委ねられている。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:116-129 が対象ref・round SHAの到達性を算出し、confirmなしでは返却だけ、確認後にdelete_refする。render.py:95-99 が対象refと到達不能SHAを表示する。tests/test_gitops.py:test_prune_requires_confirmation が確認前後のref状態を検査する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | high | defect | T-3.3, S-spec-review-loop-7.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:48 | finishはbase..HEADのcommitが同changeのround trailerを持つかだけを検査し、state.roundsに保存されたレビュー済みSHAとの一致を確認しない。PASS後に最終roundをgit commit --amend --no-editで変更すると、同じtrailerを保持した未レビューのcommitを受理し、旧roundのPASSとSHAをtrailerへ記録してsquashできる。現在のtreeとバックアップのtree比較は、未レビューtree同士の比較になるため防げない。ファイル・Gitを変更しないインメモリ再現で、レビュー済みSHA a×40に対しcommit列をb×40へ差し替えてもfinish.planが成功することを確認した。 | summary追加前に、HEADが最終レビュー済みround SHAと一致すること、およびbase..HEADのcommit列がstate.roundsのSHA列と順序も含めて一致することを検証し、不一致なら変更前に拒否する。PASS後のamendと、同じround trailerを持つ追加commitを使った拒否テストを追加する。 |
| F-002 | 新規 | medium | defect | T-2.2, S-spec-review-loop-2.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:44 | 要件指紋の入力を作る段階でタスク本文をstripし、継続行もstrip、Scenario行もrstripしているため、チェックボックス以外の原文変更まで除去される。仮想tasks.mdを使った書込みなしの再現で、本文末尾に空白1文字を追加しても抽出textとSHA-256が同一になった。design.mdの「チェックボックス状態を除いた基準原文のUTF-8 bytes」とT-2.2の原文指紋契約を満たさず、この変更をHOLDとして検出できない。 | 表示用に整形するtextと指紋用の原文を分離し、指紋用にはチェックボックス状態以外の本文空白・継続行・Scenario本文を保持する。末尾空白1文字の追加や継続行の空白変更でもドリフトし、チェック状態の変更ではドリフトしない回帰テストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準をround SHA上で確認した。必須checkは両方PASSだが、未レビューcommitをPASS付きでsquashできる問題と、原文の空白変更を指紋が検出しない問題があり、4基準をFAILとした。ファイル変更・ネットワーク利用は行わず、終了時のgit statusにも差分はなかった。
