# 独立QAレビュー

created: 2026-10-10 05:29 (JST)
update: 2026-10-10 05:29 (JST)
author: GPT-6 (GitHub connector / independent reviewer)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-002
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/blind-qa-cycle-remote-qa
- 初回基準SHA: fb44ff6d53beba3f0396e01e90c92691810c82aa
- 差分基準SHA: f513df9d15c3bc2de7755951792bffc9ad769324
- 対象SHA: 57cf971ba9f68dd4a3840f36d416ed7093a38b3e
- サイクル: 2
- 要件指紋: e3397f7e6f37a59dc255f349d0da4247415673dcff84384f0b034e8fde34f804
- 担当: GPT-6（独立レビュー、実装担当Claude Haiku/Sonnet 5.5とは別）
- 実行経路: 別チャット
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_002_1010.md
- 結論: FAIL
- 必須確認: 未完了

## 参照資材の検証

- quality-loop/skills/quality-qa/SKILL.md: SHA256:4f4166f0c6de378f6ff4b2be045f671da28737886f1aa5c290c4aaabf3154723
- quality-loop/skills/quality-qa/references/reviewer_contract.md: SHA256:0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42

対象SHAの両ファイルをGitHub APIで取得し、得られたUTF-8本文のバイト列を独立SHA-256計算して依頼記載値と一致。SKILL.mdは6108 bytes、reviewer_contract.mdは5081 bytes。Git treeのblob SHAも以前と一致。ハッシュ計算器の既知ベクトルSHA256("abc")=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015adを確認。GitHub取得バイト列の照合でありローカルcheckoutからの再ハッシュは未実行。

## 確認範囲

- 対象版57cf971ba9f68dd4a3840f36d416ed7093a38b3eと依頼 docs/Artifacts/qa_invite_002_1010.md のQA-002・サイクル2・AC-001〜019(v2)・要件指紋を確認。前回QA-001のレビュー、今回差分基準f513df9、初回基準fb44ff6を固定。
- GitHub commit compareでf513df9..57cf971はahead 3コミット。運用Artifact（前回invite/review）と実装差分（gitops.py・workflow.py・OpenSpec・runtime同期・tests）を区別。対象コミットは今回の依頼の公開より前に作られたもの。
- AGENTS.md、OpenSpec acceptance.md/v2、spec.md、design、quality-qa SKILL.mdとreferences（publish/repair/results）、qa_workflowのgitops/workflow/loop/guard/stages/minor_change/prompt_log/repair_commit、関連testsを対象版で読査。
- 同梱runtimeのGit tree検査：正本qa_workflowの15ファイルとruntimeの15ファイルに全件一致、欠落・余剰・差異0。
- 前回OPEN QA-F01〜F03は依頼にある原文・完了条件を対象版ソースと個別突合。修正担当の自己申告のみで解消とはせず、現在の静的証拠と新たな別経路の問題を区別。

## 受入基準の照合

- AC-001: 承認前の loop は修正・commit・公開を行わず、計画を示して停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:30-32 で未承認時は actions を呼ばず waiting_approval、workflow.py:808-816 で計画path/hash/bodyを返す。静的確認。
- AC-002: loop は commit・push・公開の前に、承認文が利用者発言ログ（.git/qa-user-prompts.jsonl）にあることを確認し、ログにない文（AIが作った文）では何も実行しない。既存の approve の動作は変えない | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:714-720 がloopの副作用前に承認文を発言ログと照合し不一致なら停止。approveはworkflow.py:563-574の既存契約を保持。prompt_log.py:8-19の照合動作は実環境未検証。
- AC-003: 承認文に「修正後のcommitまで」が無い場合、commit しない | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:40-42 および repair_commit.py:12-14 で「修正後のcommitまで」なしのcommitを拒否。
- AC-004: commit は承認済みパスだけを対象とし、未承認の変更・未追跡ファイル・他者のステージ済み変更を含めない | 判定: PASS | 根拠: quality-loop/qa_workflow/repair_commit.py:15-20 は同じパスの既存stageを拒否し、git addとcommitの対象パスを明示。tests/test_repair_commit.py:43-70で未承認・未追跡・別パスstage・同一パスstageを扱う。実行未確認。
- AC-005: 承認文に「クラウドQAに出して」が無い場合、再QA依頼の作成前に停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:43-45 はクラウド指示がなければpushの前で停止し、loop_stages.py:9の後段requa-requestには進まない。
- AC-006: 段階の順序は commit → submit → push → ancestry（祖先確認）→ requa-request → finalize → publish の7段階である | 判定: PASS | 根拠: quality-loop/qa_workflow/loop_stages.py:9 はcommit→submit→push→ancestry→requa-request→finalize→publishの7段階。workflow.py:789-791で各段階actionへ対応付け。
- AC-007: 途中失敗後の再実行は完了済みの段階を繰り返さず、未完了の段階から再開する | 判定: UNVERIFIED | 根拠: quality-loop/qa_workflow/loop_stages.py:12-25でcheckpointを実装、workflow.py:707-712,742-786で一部副作用を検出・再利用する。tests/test_loop_integration.py:317-350に故障注入テストがあるが対象SHAのpytestと本当のremote障害は独立実行していない。
- AC-008: 同一Finding IDが連続2サイクル未解決、または3サイクル目で未解決が残る場合に停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:729-730に各サイクルのunresolved履歴、loop_guard.py:17-23に連続2サイクル/3サイクル上限判定。tests/test_loop_guard.py:13-43に境界ケースがある。
- AC-009: 承認済みパス外の変更・新規パスでは停止しない。コミットには含めず、結果の left_out に記録する。承認外のファイルがHEADまでのコミットに含まれる場合は、提出の前に停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/minor_change.py:29-34が範囲外・新規パスをoutside_pathsとして記録、repair_commit.py:15-20で承認パスのみcommit、workflow.py:588-590で承認外のHEAD混入をsubmit前に拒否、workflow.py:802-816はleft_outを返す。tests/test_loop_integration.py:144-164に返却チェック。
- AC-010: 変更行数では停止しない（行数上限は設けない） | 判定: PASS | 根拠: quality-loop/qa_workflow/minor_change.py:26-35に行数上限を設けず契約hashだけで停止判定。tests/test_loop_integration.py:135-142に60行超の期待ケース。
- AC-011: loop は修正担当自身の判定（PASS/FAIL）を記録せず、判定段階を持たない | 判定: PASS | 根拠: quality-loop/qa_workflow/loop_stages.py:9に判定段階なし。workflow.py:789-797のloop actionsも独立PASS/FAILを生成せず、submitのindependently_verified=Falseはworkflow.py:596。
- AC-012: push の前に、送出する全コミットの変更ファイルについて、コミット済みの内容の機密情報・個人ローカルパスを検査し、検出があれば push しない | 判定: FAIL | 根拠: quality-loop/qa_workflow/gitops.py:213-230はpush_topic向けに送出全コミットのblobを走査する改修があり前回QA-F01の直接原因は改善。しかしworkflow.py:268-367の別のpush経路publish()は289,344行で最終作業ツリーのみ走査し、363行でgitops.push()を実行。送出各コミットのblob走査は呼ばれない。通常のpublishおよびloopのrun_publish（workflow.py:781-785）で、履歴中の追加→復元した機密情報が最終ファイルに残らない場合に検査漏れ。
- AC-013: 再QA依頼の前に、対象SHAと基準SHAの両方が origin/<branch> の祖先であることを確認する | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:765-773は前回reviewed/baselineと現在HEADをoriginブランチとの祖先関係で検査、requa-requestより前のstageへ配置。publish_guard.py:17-22参照。
- AC-014: 同梱コピー（skills/quality-qa/runtime/qa_workflow/）は正本と一致する | 判定: PASS | 根拠: 対象コミットのGit treeを取得しquality-loop/qa_workflow/正本15ファイルとskills/quality-qa/runtime/qa_workflow/15ファイルのGit blob SHAを突合。15件一致、欠落0・余分0。
- AC-015: 既存の承認・提出・公開・終了の操作の意味は変更されていない（既存テストが通る） | 判定: UNVERIFIED | 根拠: quality-loop/qa_workflow/workflow.py:563-630のapprove/submit/decide、268-367のpublishは既存メソッドを維持。しかし対象版のpytest testsを独立実行できず、既存テストがすべて通ることは確認できない。
- AC-016: openspec validate improve-quality-qa-loop --strict が通る | 判定: UNVERIFIED | 根拠: openspec/changes/improve-quality-qa-loop/specs/unified-qa-workflow/spec.mdを対象版で取得。openspec validate improve-quality-qa-loop --strictは環境にopenspec CLIおよび対象checkoutがなくNOT_RUN。
- AC-017: 完了条件・受入基準・確認方法の本文が承認時点から変わった場合、loop は停止して再承認を求める | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:661-671で現行plan本文のhashを計算し、minor_change.py:29-34で承認時hashとの不一致を停止、loop.py:37-39からcommit前に拒否。
- AC-018: 公開後に、リポジトリ・ブランチ・依頼ファイル・対象版・保存先を埋めた短いクラウド指示書を表示する手順が skill 文書にあり、結果は保存先の1ファイルから acquire で取得できる | 判定: PASS | 根拠: quality-loop/skills/quality-qa/references/publish.md:31-40にrepository・branch・invite・reviewed・review_pathを埋めた短文テンプレートがあり、references/results.md:3-7とworkflow.py:412-450にacquireで指定結果Markdownを取得する経路を確認。実際の公開後UI表示は未検証。
- AC-019: 同一指摘の反復で停止したloopは、利用者の発言（発言ログにあり「続行」を含む）を `authorize-continue` で記録すると、記録した指摘IDに限り続行できる。修正サイクルの上限と、記録にない指摘の反復では停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:685-705で反復停止したID、発言ログ、明示語「続行」の三条件を検査しauthorize_continueを記録。loop_guard.py:17-23で許可IDだけを免除し3サイクル上限は維持。tests/test_loop_integration.py:356-405に反復停止前・語句差異などのテスト定義。

## 実施した検証

- GitHub API: 対象版コミット存在、指定topic branch、依頼全文、今回差分、ソースおよびOpenSpecの対象版を確認。差分は3コミット（製品コード・テスト・運用Artifactを含む）。
- QA SkillとReviewer契約SHA-256照合：両方PASS。要件指紋とAC原文・順序を維持。
- 同梱runtimeとの同一性：Git blob SHA 15件/15件一致。
- AC-012の静的反証：workflow.py:268-367のpublish()は公開前publication_findingsで最終snapshotを走査するが、送出コミットを列挙しない。その後gitops.pushへ進む。gitops.preflightは変更パスの許可検査（gitops.py:377-383）であり機密blob検査ではない。gitops.outgoing_findingsはpush_topicでのみ使われる。
- Python: pytest 9.0.2は利用可能だったが、対象版リポジトリのcheckoutがなく、git ls-remote https://github.com/syrius2000/QA-products.git はDNS解決不能で失敗。したがって `cd quality-loop && python3 -m pytest tests -q` はNOT_RUN。
- OpenSpec: openspec CLIが見つからず、対象checkoutもないため `openspec validate improve-quality-qa-loop --strict` はNOT_RUN。
- 依頼内で個別に固定された構造化checkは0件。未実施を実装者申告の成功で補わない。集計PASS 15件、FAIL 1件、UNVERIFIED 3件。provenance一致、既知の受入基準FAILあり→Gate=FAIL（必須確認=未完了）。

## 未検証事項

- 対象版pytest全体成功とOpenSpec strict成功。双方NOT_RUN。必要なCLIとローカルcheckoutのない環境制約。
- AC-007の全副作用直後の障害と再実行の完全冪等性。テスト定義は確認したが未実行。
- hookの本番UserPromptSubmitログ真正性、実クラウドQA起動からacquireまでのend-to-end、GitHub remote同時更新時のTOCTOU防止。
- QA-F04の実publishでの漏洩再現（静的コード経路は確認、対象実装での統合テストは未実行）。
- ハッシュはGitHubから取得したUTF-8本文のバイト列に基づき、独立したcloneからのraw-byte読取りではない。

## 指摘

### 指摘 QA-F04
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: AC-012：push前の全送出コミット検査
- 根拠: quality-loop/qa_workflow/workflow.py:289-305,344-363 のpublishは公開時点の製品・依頼内容のpublication_findingsと許可パスのpreflightを行うだけで、gitops.outgoing_findingsを呼ばないままgitops.pushへ到達する。workflow.py:781-785からloopのpublish段階でも使用される。gitops.py:386-390はscanなしのpush関数。gitops.py:213-230の中間コミット走査がpush_topicにのみ接続されている。
- 影響: 送出履歴の途中で機密情報を追加し後で元に戻した場合、最終HEADは安全でもcommit履歴の機密blobをGitHubに送る。通常publishならレースなしで再現可能、loop終盤でも検査後の追加履歴によって同様の危険がある。
- 対応案: gitops.pushの直前（publishとpublish_correctionを含む全push経路）にremote tipから送出HEADまでの全コミットblobを走査する共通ガードを配置する。再試行・remote tip更新時は送出範囲を再計算する。スキャン結果とpush対象HEADを一致させる。
- 対象: quality-loop/qa_workflow/workflow.py; quality-loop/qa_workflow/gitops.py
- 完了条件: 通常publishとloopの最終publishで、中間コミットの機密を検出したらpushせずremote tip不変。承認外パスも含め送出履歴を過不足なく走査。
- 検証方法: bare remoteで初回基準→安全対象→一時秘密commit→復元commit→招待commitの履歴を作り、通常publishおよびloop内publishをそれぞれ実行。双方でQAError、remote tip不変を期待。secretが作業ツリーから消えた状態と個人パスのケースも検証。

## 実施側タスク

- T-01: Finding=QA-F04; path=quality-loop/qa_workflow/workflow.py; action=publishとpublish_correctionのpush直前にも全送出コミットの履歴blobスキャンを組み込む; done_when=最終ファイルから消えた機密が中間コミットにあれば全push経路で拒否されremote tip不変; verify=bare remoteで秘密追加→復元の履歴を作り通常publishとloop最終publishの両方を検査する

## 前回指摘の再確認

- QA-F01: 解消 | quality-loop/qa_workflow/gitops.py:213-230が各送出コミットの変更blobをスキャンする構造に修正され、tests/test_publish_guard.py:68-83とtests/test_loop_integration.py:295-308に一時秘密追加→復元ケースが追加された。前回のpush_topic経路の原因は解消。ただし別publish経路の検査欠落は新規QA-F04へ独立記録。
- QA-F02: 解消 | quality-loop/qa_workflow/workflow.py:802-816の_loop_replyへleft_outを追加し、workflow.py:800-802でdone.commitから値を抽出。tests/test_loop_integration.py:144-164で返却値も検査。
- QA-F03: 解消 | quality-loop/qa_workflow/workflow.py:685-705にrepeat_stopの永続記録と「続行」必須検査を追加。tests/test_loop_integration.py:391-405が停止前承認と「継続」単独拒否を確認する定義。独立pytestは未実行。

## 残余事項

- 提案: QA-F04を優先し、個別のpublish()とpublish_correction()を含む全push呼出前で送出全コミットの機密情報検査を一元化する。push_topicだけの修正では漏れが残る。GitHub実履歴を使用しない隔離bare remoteの故障注入テストも追加する。
- 批判的立場: 前回QA-F01の特定経路は修正されたものの、同じ安全要件はpush操作の全入口へ適用される必要がある。最終状態の走査と送出履歴の走査は別の検査であり、前者の成功は後者を保証しない。よってこの対象版を完全PASSとしない。
- 本レビューは指定結果Markdown1ファイルのみをtopic branchへ保存する。製品コード、QA依頼、管理状態、他の運用Artifactには触れずmain/masterへの統合をしない。
