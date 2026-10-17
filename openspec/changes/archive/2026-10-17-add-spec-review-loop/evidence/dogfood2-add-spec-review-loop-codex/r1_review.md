# spec-review r1: add-spec-review-loop

- Gate: **FAIL**（FAIL: T-5.1, T-5.3, S-spec-review-loop-4.1, S-spec-review-loop-7.4）
- base SHA: `ac998ea71b04aac543c4bcf0b90ece6268967bac`
- round SHA: `69f05fbf412a1bb97f3796dd81e4001b6668bf3d`
- Reviewer: codex codex-cli 0.160.1 ／ model: gpt-6.1-sol（effort medium）
- 停止判定: 継続

## 受入基準

| ID | 判定 | 根拠 |
|---|---|---|
| T-1.1 | PASS | quality-loop/skills/spec-review-loop/references/review.schema.json:7 に必須項目、同:26 に基準、同:41 にcheck、同:56 にFindingと前round判定を定義。tests/test_schema_contract.py:35、同:40、同:60 が正常・欠落・重複を検査する。必須check CHK-PYTESTはPASS。 |
| T-1.2 | PASS | quality-loop/skills/spec-review-loop/references/reviewer_contract.md:5、同:11、同:33、同:38 に要求された契約を記載。tests/test_schema_contract.py:81 が契約とスキーマ・Gateの対応を検査する。契約の実行時適用には別途F-001、F-002の不備がある。 |
| T-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:39、同:93 にタスク本文・検証文・各deltaの抽出を実装。tests/test_criteria.py:15 にarchive 4件の期待件数、同:32 に原文照合がある。python3 -B -cによる読取り検査でも4件の抽出件数と独立した見出し数え上げが37/25、5/5、15/18、11/23で一致した。 |
| T-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:49、同:69 でチェックボックスを本文から除外し、同:184 で本文のSHA-256を計算する。tests/test_criteria.py:61 と同:69 がチェック変更と1文字変更を検査する。 |
| T-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:75、同:97 に開始検査とbase記録。runtime/spec_review_loop/gitops.py:80 に報告・未stage検査とtrailer。tests/test_gitops.py:19、同:39、同:46、同:60 が指定されたケースを検査する。 |
| T-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:101 のcontextmanagerがfinallyでworktreeを削除する。tests/test_gitops.py:75 が成功・失敗・timeoutを、同:86 が例外を検査し、worktree一覧に残らないことを確認する。 |
| T-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:30 に前提条件とdry-run、同:81 にbackup・squash・復元・tree照合を実装。tests/test_gitops.py:101、同:119、同:129、同:139、同:147、同:191 に対応テストがある。 |
| T-3.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:115 に対象refと到達不能SHAの取得、confirm分岐、削除を実装。tests/test_gitops.py:178 が表示のみではrefが残り、確認後に消えることを検査する。 |
| T-4.1 | PASS | openspec/changes/add-spec-review-loop/design.md:148 にOpen Questionの解消、同:154〜156 に3 CLIの版・フラグ・出力取得を記載。runtime/spec_review_loop/reviewers.py:78、同:106 が対応するCLIと必要フラグを検出する。evidence/sandbox-add-slugify-codex/summary.md:15 とevidence/sandbox-add-slugify-cursor/summary.mdに実際のReviewer情報が残る。 |
| T-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/reviewers.py:25、同:144 に共通インタフェースと3経路を実装。tests/test_reviewers.py:23 が3アダプタをパラメータ化し、同:62、同:68 が未導入・未対応を検査。tests/test_cli.py:56 がdoctorの導入案内と終了コードを検査する。 |
| T-5.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:41 は原文をnormalizeして比較するため、原文改変を一部受理する。python3 -B -cで本changeのT-1.1の空白を改行へ変更した出力をstructural_errorsへ渡すと([], [])となった。tests/test_schema_contract.py:72 も空白改変を許容する期待値であり、同じ原文を保持する契約に反する。F-001。 |
| T-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:102 に停止優先順位、同:116 に同一Findingと件数の停滞判定を実装。tests/test_gate.py:143、同:150、同:161、同:175 が2 round目PASS・停滞・上限・非減少を検査する。 |
| T-5.3 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/report.py:60〜69 は最終roundのreviewだけを参照する。前roundに未解決Findingがあっても、最終roundのReviewer失敗でreview=Noneになるとsummaryの残余Findingは「なし」になる。保存済みstateをメモリ上でこの状態にしてsummary_markdownを呼び、前roundの未解決6件が消えることを確認した。F-003。 |
| T-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/cli.py:18 に8サブコマンド、同:65 に実行経路、同:88 にエラー分類を定義。tests/test_cli.py:9、同:18、同:47、同:56、同:63、同:69 が正常・拒否・入出力・内部エラーを検査する。 |
| T-6.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4 に適用範囲・正例・非発火例、同:13 に使い分け、同:43 にround手順、同:54 に停止時の引継ぎを記載。tests/test_skill.py:13、同:21 が形式と手順を検査する。 |
| T-6.3 | PASS | quality-loop/skills/spec-review-loop/evals/evals.jsonをpython3 -B -cで読み取り、起動3件・非起動4件を確認した。tests/test_skill.py:28 もそれぞれ3件以上とIDの一意性を検査する。 |
| T-7.1 | PASS | quality-loop/skills/spec-review-loop/tests/test_integration.py:9 が一時リポジトリでFAIL→PASS→finishを実行し、同:33〜49 で2 commitから1 commitへの整理、tree一致、summary・trailer・証跡の追跡を検査する。必須check CHK-PYTESTはPASS。 |
| T-7.2 | PASS | openspec/changes/add-spec-review-loop/evidence/sandbox-add-slugify-codex/summary.md:15〜16 に実際のchange add-slugifyのFAIL→PASS、round SHA、codex-cli 0.160.1、gpt-6-lunaを記録。対応するr1_review.json、r2_review.jsonとsquash_commit.txtも保存され、後者にGate・round数・Reviewerのtrailerがある。 |
| T-7.3 | PASS | CLI実行済みCHK-VALIDATEは終了コード0。git diff --name-only ac998ea71b04aac543c4bcf0b90ece6268967bac 69f05fbf412a1bb97f3796dd81e4001b6668bf3dで、変更が新Skillとopenspec/changes/add-spec-review-loop配下に限られることを確認した。既存4経路・既存QA記録の変更はない。 |
| S-spec-review-loop-1.1 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4 に明示起動条件、同:28 にchange存在確認後の起動手順を規定。runtime/spec_review_loop/criteria.py:30 とsession.py:31 に存在検査があり、tests/test_cli.py:13 で存在しないchangeを拒否する。 |
| S-spec-review-loop-1.2 | PASS | quality-loop/skills/spec-review-loop/SKILL.md:4、同:22 に説明・一般レビュー・OpenSpec applyの非起動を明記。evals/evals.jsonにこれらの非起動例があり、今回の差分にも既存QA経路への変更はない。 |
| S-spec-review-loop-2.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:65、同:127〜139 にID付与、session.py:94〜104 に抽出結果の保存・返却を実装。tests/test_criteria.py:50 が順序、tests/test_cli.py:11 がstart出力へのID表示を検査する。 |
| S-spec-review-loop-2.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:49〜69 がチェック状態を本文に含めない。tests/test_criteria.py:61 が指紋不変を検査し、tests/test_integration.py:23〜27 がチェック更新後の次round commitを通す。 |
| S-spec-review-loop-2.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:135〜137 とreview_round.py:88〜90 が再抽出とHOLDを実装。tests/test_gate.py:87、同:96、同:219、同:228 が本文変更と全件削除のHOLD、変更ID、refreezeを検査する。 |
| S-spec-review-loop-2.4 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/criteria.py:203 が0件の開始を拒否する。session.py:94 の抽出はstate作成より前であり、startにはcommit処理がない。tests/test_criteria.py:90 が基準なしを検査する。 |
| S-spec-review-loop-3.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:13、同:46 にmain/master拒否とtopic branch案内。tests/test_gitops.py:19 がmasterでstateを作らず拒否することを検査する。 |
| S-spec-review-loop-3.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:82〜85 が実装報告の存在と内容を検査する。tests/test_gitops.py:39 が拒否とbase以降のcommit数0を確認する。 |
| S-spec-review-loop-3.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gitops.py:86〜91 が対象外のunstaged/untrackedをpath付きで拒否する。tests/test_gitops.py:46 がnew.pyとapp.pyの拒否pathを照合する。review配下を自動stageする設計はdesign.md:71に明記されている。 |
| S-spec-review-loop-4.1 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:91〜95 は必須checkを実行した同じworktreeを、そのままReviewerへ渡す。checkによる追跡ファイルの改変を検査・復元せずcheck後の状態を基準にするため、Reviewerが読む内容はround SHAと異なり得る。Codexのread-only指定とメタデータ記録はあるが、固定SHAの内容に対するレビュー保証が欠ける。F-002。 |
| S-spec-review-loop-4.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:79〜82 がprobe不適合時に起動せずdoctor結果と導入・切替案内を返す。tests/test_gate.py:131 とtests/test_reviewers.py:62、同:68 が未導入・必要フラグ欠落を検査する。 |
| S-spec-review-loop-4.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:14、同:99〜114、同:121〜129 が失敗をINCONCLUSIVEにし、最大2試行に制限する。tests/test_gate.py:117 と同:202 が失敗・timeout・不正出力と再試行上限を検査する。 |
| S-spec-review-loop-5.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:32〜38 がID列を完全照合し、review_round.py:113〜114 が不適合出力を採用しない。tests/test_gate.py:30 とtests/test_schema_contract.py:60 が欠落・重複を検査する。 |
| S-spec-review-loop-5.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:80〜86 がFAILを未実行より優先し、同:90 が状態と理由を残す。tests/test_gate.py:53〜59 がFAILとNOT_RUNの併存、同:41 が実際のERROR併存時の個別記録を検査する。 |
| S-spec-review-loop-5.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:12 が対応基準のないFindingをproposalsへ移し、同:96 以降の停滞対象はfindingsのみ。tests/test_gate.py:65 が提案への移動、PASS維持、Markdownへの記録を検査する。 |
| S-spec-review-loop-6.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:106 がPASS停止、session.py:176〜177 がfinishと人によるarchive判断を案内。tests/test_gate.py:143 が2 round目PASSでの停止と案内を検査する。 |
| S-spec-review-loop-6.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:120〜123 が同じIDの未解消を検出。tests/test_gate.py:150 がF-002の停滞停止、引継ぎ案内、次round拒否を検査する。report.py:30〜33 にFinding内容の表示がある。 |
| S-spec-review-loop-6.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:111、session.py:133 に上限停止・次round拒否を実装。tests/test_gate.py:161 が3 round目INCONCLUSIVEで停止し、4 round目を拒否することを検査。session.py:180 に引継ぎ選択肢がある。 |
| S-spec-review-loop-7.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:64〜66 にtrailer、同:81〜112 に確認後のsummary追加・backup・squash・tree照合を実装。tests/test_integration.py:35〜48 が1 commit化と全項目を検査する。 |
| S-spec-review-loop-7.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:54〜59 が各commitのremote追跡ref到達可能性を検査し、別途承認・手作業を案内する。tests/test_gitops.py:119 がリモート追跡refを作って拒否とHEAD不変を検査する。 |
| S-spec-review-loop-7.3 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:106〜111 がtree不一致で復元し、失敗を返す。gitops.py:172 がHEAD・index・作業ツリーを復元。tests/test_gitops.py:147 が改変を模擬し、HEAD・tree・作業ツリーの復元を検査する。 |
| S-spec-review-loop-7.4 | FAIL | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:40 は明示受容を要求するが、同:68 は最終roundのreviewだけから残余IDを取得する。report.py:60〜69 も同様。前roundに未解決Findingが残り、最終roundがReviewer失敗でreview=Noneの場合、要約とtrailerは残余を「なし」と記録してしまう。F-003。 |
| S-spec-review-loop-8.1 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/session.py:31〜34 がreviewをchange配下に固定し、finish.py:89〜94 がsummaryと成果物をcommitする。tests/test_integration.py:44〜48 がround SHA・Gate推移とreview配下の追跡を検査する。archive対象のchangeフォルダ内に証跡が完結している。 |
| S-spec-review-loop-8.2 | PASS | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:117〜128 が対象ref・到達不能SHAを返し、confirmなしでは削除しない。tests/test_gitops.py:178 が確認前後のrefの存在と対象round SHAを検査する。 |

## 必須check

| ID | 状態 | 終了code | 理由 |
|---|---|---|---|
| CHK-VALIDATE | PASS | 0 | 期待 0・実際 0 |
| CHK-PYTEST | PASS | 0 | 期待 0・実際 0 |

## Finding

| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |
|---|---|---|---|---|---|---|---|
| F-001 | 新規 | medium | defect | T-5.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/gate.py:41 | Reviewer契約はtextの原文保持を要求するが、構造検証が空白・改行を正規化して比較するため、異なる原文を受理する。実際に本changeのT-1.1の空白1文字を改行へ置換したレビューを渡しても、structural_errorsはエラーもprovenance不一致も返さなかった。tests/test_schema_contract.py:72もこの契約違反を許容する期待値になっている。 | criteriaのtextを固定済み原文と直接比較する。空白・改行・連続空白の変更も構造不適合として拒否する回帰テストに変更する。 |
| F-002 | 新規 | high | defect | S-spec-review-loop-4.1 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/review_round.py:91 | 必須checkを実行したworktreeを、そのままReviewerへ渡し、check後のgit statusを正常な基準として扱っている。checkには任意のargvを指定でき、追跡対象の実装ファイルやspecを変更して終了コード0を返しても拒否されない。その場合、Reviewerはround SHAと異なる内容を読み、元のround SHAに対するPASSとして記録できる。checkが既にdirtyにしたpathをReviewerが再変更しても、statusの組が同じなら同:96の差集合による書込み検出も通過する。 | check実行用とReviewer用のworktreeを分離するか、check後に追跡ファイル・index・HEADがround SHAと一致することを検証して、不一致ならReviewerを起動せず記録する。書込み検出はstatusの組だけでなく内容の変化も検出する。checkが追跡ファイルを書き換えるケースの回帰テストを追加する。 |
| F-003 | 新規 | medium | defect | T-5.3, S-spec-review-loop-7.4 | quality-loop/skills/spec-review-loop/runtime/spec_review_loop/finish.py:68 | 前roundがFinding付きFAILで、次roundのReviewerが失敗またはスキーマ不適合となって有効なreviewを残せない場合、finish --accept-residualは前roundの未解決Findingを引き継がない。trailerはSpec-Review-Residual-Findings: なし、summaryも残余Finding「なし」となる。report.py:60〜69でも最終roundしか参照しないことを確認し、保存済みstateの最終reviewをメモリ上でNoneにしてsummary_markdownを呼ぶ読取り検査で、前roundの未解決6件が消えることを再現した。レビュー失敗はFinding解消の根拠にならない。 | 有効な再判定を受けるまで未解決Findingを保持し、最終レビューが無効なら前回の未解決項目を未検証として残す。summaryと残余Finding trailerに同じ集合を記録し、FAIL→次roundのReviewer失敗→残余受容finishの回帰テストを追加する。 |

## 提案（Gate・停滞判定の対象外）

なし

## 所見

全43基準を照合した。主要機能と対応テスト、実機Reviewerの保存証跡を確認したが、原文改変の受理、checkによる固定SHAの内容汚染、最終レビュー失敗時の残余Finding消失の3件があるため要求未達。ファイル変更・テスト用リポジトリ作成・network利用は行わず、読取りとメモリ上の検査を実施した。必須checkのPASSはCLI提供結果を参照した。
