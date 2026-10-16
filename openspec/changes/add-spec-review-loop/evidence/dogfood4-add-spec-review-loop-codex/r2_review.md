# spec-review r2: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-3.3）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `753058f815aeee4bc34389afe217f8282c96df37`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:7で必須項目、:26以降で各判定・Finding等を定義。tests/test_schema_contract.py:37以降の正常例、欠落・重複・原文改変の検査を確認。python3 -Bによる書込みなしの直接呼出しで正常例と重複・欠落・原文改変のテストが成功。必須CHK-PYTESTもPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5以降に読取り専用、基準と根拠、Gate、提案、前round再判定を規定。tests/test_schema_contract.py:81の契約対応テストを読取り専用で直接実行し成功。runtime/spec_review_loop/gate.py:48で前round IDの再判定も検証する。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:38、:91で抽出・ID付与。読取り専用Pythonでarchive済み4件を独立に数え、37/25、5/5、15/18、11/23件が抽出結果と一致し、全Scenario本文の原文一致も確認した。tests/test_criteria.py:17以降の固定期待値とも一致。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:25、:49、:190、:221でチェックボックスを除いた原文のSHA-256と比較を実装。tests/test_criteria.py:70以降に状態変更・1文字変更の回帰テスト。今回の読取り専用再抽出では43基準、指紋0df605a8a5e200802b43c1786baf116d1726bf481d9127300cb448bfbc1aefc1となり指定値と一致。必須CHK-PYTESTはPASS。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:73でbranch・対象外差分・baseを確認。gitops.py:80で報告必須、未stage拒否、Spec-Review-Round trailerを実装。tests/test_gitops.py:23以降に指定された拒否系と正常commitの検査があり、必須CHK-PYTESTはPASS。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:105でcontextmanagerのfinallyからworktree remove・pruneと一時ディレクトリ削除を行う。tests/test_gitops.py:78以降は成功・失敗・timeoutと例外についてworktree一覧が元に戻ることを検証。必須CHK-PYTESTはPASS。 |
| T-3.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30以降の前提検査と:105以降のsquash失敗・tree不一致の復元は確認した。ただし:96でfinishedを保存した後、:99のsummary commitは復元用tryの外にある。python3 -Bとunittest.mockによるファイル書込みなしの再現で、このcommitを失敗させるとsquash未実行なのにfinished/pendingが残り、statusは「squash済み」、finish再試行は拒否された。F-003参照。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:129で対象refと到達不能候補を返し、confirmがなければ削除しない。tests/test_gitops.py:178でdry-run時の保持と確認後のrefs消失を検証。必須CHK-PYTESTはPASS。 |
| T-4.1 | PASS | openspec/changes/add-spec-review-loop/design.md:146でOpen Questionを解消し、:150以降にCodex 0.160.1、Claude 2.1.296、Cursor 2026.10.14-941492eとフラグ・取得方法を記録。runtime/spec_review_loop/reviewers.py:78、:106で3種の版と必要フラグを検出する。evidence/sandbox-add-slugify-codex/r2_review.jsonとevidence/sandbox-add-slugify-cursor/r2_review.jsonでも実際のReviewer情報・構造適合結果を確認した。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:33、:55、:106、:144で共通入出力、3種の起動、timeout、導入案内を実装。tests/test_reviewers.py:24以降で3経路、:64以降で未導入・非対応フラグを検査。tests/test_cli.py:55でdoctorの拒否と導入案内を確認。必須CHK-PYTESTはPASS。 |
| T-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11、:28、:76で提案除外、構造・provenance検証、Gate優先順位を実装。tests/test_gate.py:30、:41、:65が該当Scenarioに対応。今回の読取り専用再現でも、前round F-001をproposalsだけで返す出力は「findingsで再判定されていません」と拒否された。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:113、:127でPASS・同一Finding・件数非減少・round上限による停止を実装。tests/test_gate.py:143、:150、:161、:175に対応するテストがあり、session.py:108、:170で次round拒否と引継ぎ案内を実装。必須CHK-PYTESTはPASS。 |
| T-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:14、:44でMarkdownを生成し、基準表・Gate・Finding・提案・Reviewer・SHAを出力する。tests/test_report.py:16以降は両生成物の項目とsummaryの全基準IDを検証。必須CHK-PYTESTはPASS。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli:1とruntime/spec_review_loop/cli.py:18、:67以降に全8サブコマンド、例外別終了コードを実装。tests/test_cli.py:11以降で正常系、契約拒否、Reviewer失敗、破損state、内部エラーの0/2/3/4を検証。必須CHK-PYTESTはPASS。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3のdescriptionに適用範囲、明示例、非発火例を記載し、本文に作業手順・停止・既存経路との使い分けがある。tests/test_skill.pyのdescriptionと手順対応テストをpython3 -Bで直接実行し成功。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.json:26以降に起動3件、非起動4件を記載。tests/test_skill.py:28の件数・ID一意性・内容検査をpython3 -Bで直接実行し成功。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:11でCLI経由のFAIL→PASS→finishを構成。:33以降で2 round commit、1 commitへの集約、バックアップとのtree一致、summaryの両SHA、GateとReviewerのtrailerを検証する。必須CHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/summary.md:11以降に実機CodexのFAIL→PASS、各round SHA、codex-cli 0.160.1/gpt-6-lunaを記録。r1_review.json・r2_review.jsonを読取り検証し、構造適合とGateを確認。squash_commit.txt:1以降に集約commitとtrailerが残る。本change自身の実機レビューもevidence/dogfood-add-spec-review-loop-codex/に保存されている。 |
| T-7.3 | PASS | 必須CHK-VALIDATEは指定roundでexit 0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac..753058f815aeee4bc34389afe217f8282c96df37を確認し、変更はopenspec/changes/add-spec-review-loop/とquality-loop/skills/spec-review-loop/の新規追加に限定され、対象外Skillや既存QA記録の変更はなかった。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3と起動前の確認に対象change確認→startを規定。runtime/spec_review_loop/criteria.py:29でも存在しないchangeを拒否する。tests/test_cli.py:11でmissing changeの拒否、evals/evals.json:5以降で明示起動例を確認。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:3および非起動例に3種の依頼を明示し、既存QA記録の非変更を規定。evals/evals.json:44以降に各非起動ケースがある。git diff --name-onlyでも既存QA経路の変更はなかった。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:38、:80、:91で原文順にIDを付与し、session.py:94以降で固定結果を返す。tests/test_cli.py:11はstart表示にT/S/CHKが含まれることを検証。今回の再抽出でも全43基準と指紋が指定値に一致した。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:49は番号からの原文を保存してチェックボックスを除外する。tests/test_criteria.py:70の専用テストとtests/test_integration.py:27の完了状態変更後のround継続を確認。必須CHK-PYTESTはPASS。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:83以降でround SHAから再抽出し、:122以降でHOLDと変更IDを記録。session.py:170の案内はrefreezeを示す。tests/test_gate.py:87、:96、:219、:228に改変・全削除とHOLDの回帰テストがあり、必須CHK-PYTESTはPASS。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:203で0基準のstartを拒否。session.py:94は抽出成功後にのみstateを書き、startにはcommit操作がない。tests/test_criteria.py:99でtasksとspecの両方がない拒否を検証。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、:47でmain/masterの両方を拒否し、topic branchを案内する。session.py:75で最初に検査。tests/test_gitops.py:23でmaster拒否とstate未作成を検証。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82以降は報告の存在・非空をcommit前に必須化。tests/test_gitops.py:45は拒否後base以降のcommitが0件であることを確認し、tests/test_cli.py:24でも終了コード2と報告案内を検証。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86以降でreview成果物以外のunstaged/untrackedをpath付きで拒否。tests/test_gitops.py:52では?? new.pyと M app.pyの具体的なpathが拒否詳細に含まれることを検証する。 |
| S-spec-review-loop-4.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:16は既定codex、:36はexec --sandbox read-onlyを指定。review_round.py:91以降でround SHAの隔離worktreeを渡し、:136以降でツール・版・モデルを記録。tests/test_reviewers.py:24と実機evidence/sandbox-add-slugify-codex/r2_review.jsonを照合した。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:106で実行ファイルと必須フラグを検出し、review_round.py:74以降でdoctor情報・導入・Reviewer切替を示して起動前に拒否する。tests/test_gate.py:131とtests/test_reviewers.py:64以降で未導入・フラグ不足を検証。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:144で失敗・timeoutを結果化し、review_round.py:122以降でINCONCLUSIVEと最大2 attemptsを記録。tests/test_gate.py:118、:203で失敗・timeout・不適合出力を検証。必須CHK-PYTESTはPASS。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:34以降で期待順序とID配列を比較し、review_round.py:116以降は構造不適合の結果を有効レビューとして扱わない。tests/test_schema_contract.pyの欠落・重複テストを読取り専用で直接実行し成功し、tests/test_gate.py:30も対応する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:84以降でFAILをpending状態より優先し、個別pending理由も保持。report.py:29で各check状態・理由を出力する。tests/test_gate.py:41と:53がFAIL/NOT_RUN併存と優先順位を検証。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:11で新規の基準外Findingをproposalsへ移し、:76と:127は提案をGate・停滞に数えない。report.py:38で提案を表示。tests/test_gate.py:65でこのScenarioを検証する。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:117でPASS停止、session.py:176以降でfinishと利用者によるarchive判断を案内。tests/test_gate.py:143はr2 PASS停止と両案内を検証する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:127で前round未解決IDのunresolved再判定を停滞とする。tests/test_gate.py:150ではF-002で上限前に停止し、引継ぎ案内と次commit-round拒否まで確認する。report.py:32以降にFinding内容を残す。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:122とsession.py:135で上限到達停止・超過拒否を実装。tests/test_gate.py:161ではr3 INCONCLUSIVE後にr4を拒否し、session.py:180以降の共通引継ぎ案内を確認できる。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:69以降でtrailerを組み、:87以降でconfirm後のsummary・ref・squash・tree比較を実施。tests/test_gitops.py:108以降とtests/test_integration.py:33以降が正常系を検証。summary commit失敗時の復元欠落はT-3.3のF-003として別途記録した。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:59以降で各commitのリモート追跡ref到達を検査して、明示承認と手作業を案内する。tests/test_gitops.py:123以降で拒否とHEAD不変を検証。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:111でtreeを比較し、:120の復元処理でバックアップのファイル状態を戻してからsummary commitを外し、終了前stateへ戻す。tests/test_gitops.py:147以降で改変の復元、state・ref、再finish成功まで検証。必須CHK-PYTESTはPASS。 |
| S-spec-review-loop-7.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:40と:72でaccept-residual必須と残余Findingのtrailerを実装。report.py:54、:73で要約に残す。tests/test_gitops.py:167、:206、:218では拒否、残余trailer、最終レビュー失敗時の持越しを検証する。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:32でreviewをchange直下に置き、finish.py:97で成果物を追跡する。tests/test_integration.py:45以降でsummary・基準・各roundレビューがcommitに含まれることを検証。report.py:56以降はround SHAとGate推移をsummaryへ保存し、archive自体は利用者の操作として残している。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:129でrefs・unreachable_after_pruneを返し、confirm前は削除しない。tests/test_gitops.py:178でround SHAの表示対象、確認前のref保持、確認後の削除を検証。必須CHK-PYTESTはPASS。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 解消 | medium | defect | T-5.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:48 | 解消を確認した。前round IDはfindings内のstatusで再判定される必要があり、同じIDをproposalsだけに返すと構造不適合になる。読取り専用のPython再現でもF-001について「findingsで再判定されていません（提案としてだけ返されています）」を確認した。gate.py:20とreview_round.pyのkeep_ids指定により、既存IDは基準IDが空でも自動格下げされず、newのままなら拒否される。tests/test_gate.py:276、:282に回帰テストがある。 | 対応済み。既存IDの再判定を提案への移動で代替できない現在の検証を維持する。 |
| F-002 | 解消 | medium | defect | T-3.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:105 | 元の指摘対象であるsquash処理の例外とtree不一致について解消を確認した。両経路が_rollbackを呼び、バックアップ復元後にsummary commitを外して終了前stateへ戻し、summaryと不要refを削除する。tests/test_gitops.py:147以降と:191以降はstate・HEAD・refの復元を検査し、tree不一致テストは復元後のfinish再実行成功も検査する。必須CHK-PYTESTはPASS。summary commit自体の失敗は別の未処理経路でありF-003に記録した。 | 対応済み。squash失敗・tree不一致の復元テストを維持し、別途F-003の事前処理失敗も復元対象に含める。 |
| F-003 | 新規 | medium | defect | T-3.3 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:96 | summary commitの失敗時にfinish前の状態へ復元されない。finishedをstate.jsonへ保存した後のgit add・summary commit・バックアップref作成が復元用tryの外にあるため、例えばsummary commitをhook等が拒否すると、squash未実行なのにfinished/pendingが残る。python3 -Bとunittest.mockでSessionの入出力とGit操作をメモリ上に置き換え、summary commitだけを失敗させたところ、commit_squashは未呼出し、next_actionは「squash済み」、finish.planの再試行は「このループはsquash済みです」で拒否された。作業ツリーへの書込みなしで再現した。 | summary生成からバックアップ作成までを含むfinish全体に、進行段階に応じた復元処理を設ける。summary commit未作成の失敗では終了前state・summary・indexを復元し、作成後の失敗では追加commitも適切に戻す。summary commit失敗とバックアップref作成失敗について、未完了の案内、元の変更の保持、finish再試行成功まで検証する回帰テストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

前roundのF-001・F-002は解消を確認した。43基準の再抽出指紋は指定値と一致し、archive済み4件の抽出件数・Scenario原文も照合した。一方、summary commit失敗時に未実行のsquashを完了扱いとして再試行を拒否するF-003を再現したため、T-3.3をFAILとした。全体の書込みを伴うテストは再実行せず、CLI提供の必須check結果と実装・テスト・保存済み証跡、書込みなしの検査を組み合わせて判定した。
