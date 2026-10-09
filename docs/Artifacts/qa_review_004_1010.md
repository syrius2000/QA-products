# 独立QAレビュー

created: 2026-10-10 03:59 (JST)
update: 2026-10-10 03:59 (JST)
author: GPT-6 (GitHub connector / independent static reviewer)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-004
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/blind-qa-cycle-remote-qa
- 初回基準SHA: fb44ff6d53beba3f0396e01e90c92691810c82aa
- 差分基準SHA: d355b70eff14dde6ffedec0e6c01a59bbc630244
- 対象SHA: 9103a9a8515f4337d4a5acefd11c6681325d5e3b
- サイクル: 2
- 要件指紋: f04477652513d848cf6ec7c1d526a7034cb57c2c4df79a5894dbe45e98f7ff49
- 担当: GPT-6（独立Reviewer）
- 実行経路: 別チャット
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_004_1010.md
- 結論: FAIL
- 必須確認: 未完了

## 参照資材の検証

- quality-loop/skills/quality-qa/SKILL.md: SHA256:278d46bb76e6367ddd7e4200234772e3bb68df1828cd342377361396d378b351
- quality-loop/skills/quality-qa/references/reviewer_contract.md: SHA256:0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42

対象SHAの各ファイルをGitHubから取得し、取得UTF-8のSHA-256を計算して依頼記載値と両方一致。SKILL.md=6019 bytes、reviewer_contract.md=5081 bytes。ハッシュ計算器は既知ベクトル SHA256("abc")=ba7816bf...15ad と一致。GitHub blob SHAはSHA-256とは別の照合値である点に注意。

## 確認範囲

- qa_invite_004_1010.mdに記載の初回基準fb44ff6、今回差分基準d355b70、Reviewed 9103a9aを固定。GitHub compare d355b70..9103a9a はahead 3 commits、23 changed files（AGENTS.md、OpenSpec、workflow、runtime、tests等）。
- qa_workflowのloop.py、loop_guard.py、loop_stages.py、minor_change.py、prompt_log.py、publish_guard.py、repair_commit.py、workflow.py、cli.py、関連gitops.py、OpenSpec spec/design、AGENTS.md、主要統合テストの対象SHA本文を読査。
- Git tree比較ではqa_workflow正本15ファイルと同梱runtime 15ファイルでblob SHA 15/15一致。
- 前回8 Findingの本文と再確認条件は今回の依頼ファイルから確認し、現行コードの行番号と突合。実装者の完了申告やテスト成功申告は独立証拠として扱わない。
- 依頼に残されたAC原文と改訂OpenSpecは矛盾する箇所がある。レビューではユーザー依頼のAC原文を優先し、改訂仕様に合わせてACを読み替えない。

## 受入基準の照合

- AC-001: 承認前の loop は修正・commit・公開を行わず、計画を示して停止する | 判定: PASS | 根拠: qa_workflow/loop.py:31-32（承認前停止）、qa_workflow/workflow.py:774-783（計画path/hash/bodyを返す）。test_loop_integration.py:176-180が対応するが未実行。
- AC-002: 承認文は利用者発言ログ（.git/qa-user-prompts.jsonl）に含まれる場合だけ受理し、AIが作った文は拒否する | 判定: FAIL | 根拠: qa_workflow/workflow.py:563-574のapproveは利用者発言ログを確認せず承認を保存できる。693-694でloop開始時に拒否するが承認の受理自体を防いでいない。test_loop_integration.py:168-174もログなしapprove成功を前提としている。
- AC-003: 承認文に「修正後のcommitまで」が無い場合、commit しない | 判定: PASS | 根拠: qa_workflow/loop.py:38-39とqa_workflow/repair_commit.py:13-14で「修正後のcommitまで」がなければcommitの前に停止。test_repair_commit.py:36-41対応、未実行。
- AC-004: commit は承認済みパスだけを対象とし、未承認の変更・未追跡ファイル・他者のステージ済み変更を含めない | 判定: PASS | 根拠: qa_workflow/repair_commit.py:15-20で承認パスの既存ステージと衝突したらQAError、git add/commitにパス指定。test_repair_commit.py:43-70に対象外・未追跡・別パスstage・同一パスstageケース。静的検証のみ。
- AC-005: 承認文に「クラウドQAに出して」が無い場合、再QA依頼の作成前に停止する | 判定: PASS | 根拠: qa_workflow/loop.py:40-41で公開承認がなければpush前に停止、STAGES順からrequa-requestも未実施。test_loop_integration.py:126-133対応、未実行。
- AC-006: 段階の順序は commit → submit → requa-request → finalize → publish である | 判定: FAIL | 根拠: qa_workflow/loop_stages.py:9はcommit→submit→push→ancestry→requa-request→finalize→publishの7段階であり依頼原文の5段階順序と一致しない。改訂OpenSpecも7段階を採用しAC原文が変更されていない。
- AC-007: 途中失敗後の再実行は完了済みの段階を繰り返さず、未完了の段階から再開する | 判定: UNVERIFIED | 根拠: qa_workflow/loop_stages.py:12-24で段階チェックポイント、workflow.py:681-685,722-759でcommit/submit/push/requa/publishの再利用ガードを追加。ただし途中副作用直後の永続化失敗、push成功後の障害について独立した故障注入テストを実行できない。
- AC-008: 同一Finding IDが連続2サイクル未解決、または3サイクル目で未解決が残る場合に停止する | 判定: PASS | 根拠: qa_workflow/workflow.py:703-704でstate.unresolvedのFinding IDから履歴を構築し、651-655で次QAへ引継ぎ、qa_workflow/loop_guard.py:17-22で連続2回・3回上限判定。静的照合。
- AC-009: 承認範囲外の変更（承認済みパス外、または新規パス）がある場合、commit 前に停止する | 判定: FAIL | 根拠: qa_workflow/minor_change.py:29-34は承認外・新規パスをoutside_pathsに記録するだけで停止しない。workflow.py:713,715-720もleft_out記録でcommitに進む。test_loop_integration.py:144-156は範囲外があってもcompletedになることを期待している。
- AC-010: 変更行数が 50 行を超える場合、commit 前に停止する（MINOR_LINE_LIMIT = 50） | 判定: FAIL | 根拠: qa_workflow/minor_change.pyにMINOR_LINE_LIMIT=50が存在せず、行数の検査がない。test_loop_integration.py:135-142は60行超の変更でもcompletedを期待。AC原文と反対の動作。
- AC-011: loop は修正担当自身の判定（PASS/FAIL）を記録せず、判定段階を持たない | 判定: PASS | 根拠: qa_workflow/loop_stages.py:9に判定段階なし。qa_workflow/workflow.py:761-772のactionsに自分の修正へのPASS/FAIL判定なし、submitのindependently_verified=Falseは維持（workflow.py:596）。
- AC-012: 公開前に機密情報・個人ローカルパスの検査を行い、検出があれば push しない | 判定: FAIL | 根拠: qa_workflow/workflow.py:632-643のpush_topicはgitops.preflight後にgit pushし機密情報検査を呼ばない。728-734のrun_pushが公開前にこれを使用し、後段publishのpublication_findingsへ到達する前に未検査コードを送出できる。
- AC-013: 再QA依頼の前に、対象SHAが origin/<branch> の祖先であることを確認する | 判定: PASS | 根拠: qa_workflow/workflow.py:736-745で前回reviewed（baseline）と現在HEAD（修正対象）両方のorigin祖先性をrequa作成前に検査、qa_workflow/publish_guard.py:18-22が判定。静的照合。
- AC-014: 同梱コピー（skills/quality-qa/runtime/qa_workflow/）は正本と一致する | 判定: PASS | 根拠: 対象9103a9aのGit treeのqa_workflow正本15ファイルとskills/quality-qa/runtime/qa_workflow同梱15ファイルのGit blob SHAを全件比較し一致15/15、欠落・余分なし。
- AC-015: 既存の承認・提出・公開・終了の操作の意味は変更されていない（既存テストが通る） | 判定: UNVERIFIED | 根拠: 旧approve/submit/publish/decideのAPIは存続（workflow.py:563-624等）。ただしapproveはapproved状態での再更新を許す変更（workflow.py:567-573）を含み、全既存テストを独立実行できていないため互換性の受入を証明できない。
- AC-016: openspec validate improve-quality-qa-loop --strict が通る | 判定: UNVERIFIED | 根拠: OpenSpec仕様は取得・読査したがopenspec CLIが実行環境になく、openspec validate improve-quality-qa-loop --strictを対象9103a9aで独立実行できない。

## 実施した検証

- GitHubリポジトリAPI（読み取り）: 対象commit 9103a9aの存在確認 PASS、初回基準・差分基準の識別と差分メタデータ取得 PASS。
- SHA-256照合: 対象版SKILL.mdとreviewer_contract.mdの取得内容をSHA-256化し依頼記載値と完全一致 PASS（raw bytesからの変換なしを保証する独立cloneは未実施。ファイルのUTF-8とbyte長はGit treeと整合）。
- Git tree整合性: 正本15、runtime15、Git blob SHA差異0、欠落0、余分0、PASS。
- 静的制御フロー評価: workflow.py:632-643で公開前スキャン抜け、minor_change.pyで旧50行制限削除、loop_stages.py:9で7段階契約、workflow.py:563-574でログ未照合の承認保存を確認。
- 対象版でのPython製品テスト: NOT_RUN。レビュー環境のGitHub cloneでDNS解決不能（github.com）、対象ファイル一式を実行可能なcheckoutとして取得できないため。実装者のテスト結果は代用しない。
- `cd quality-loop && python3 -m pytest tests -q`: NOT_RUN（対象版の実行環境未構築）。
- `openspec validate improve-quality-qa-loop --strict`: NOT_RUN（openspec CLI未導入、対象版checkoutなし）。
- 依頼内の構造化checkは0件。実環境テスト・strict検査の未実施はPASSの根拠としない。対象SHAのGitHub Actions CIステータスは該当結果を確認できず。
- 判定集計：PASS 8、FAIL 5、UNVERIFIED 3。provenance整合を確認済みでAC FAILがあるため総合Gate=FAIL（必須確認は未完了）。

## 未検証事項

- 対象9103a9aのpytest全件成功（未実行）、OpenSpec strict成功（未実行）。
- 過去のQA-F03のクラッシュ時冪等性、QA-F07のstatus復旧情報と実操作の一致（独立故障注入未実施）。
- Claude Code UserPromptSubmit hook実環境からの発言ログが原本であること（合成JSONLのみテスト対象）、GitHub上の実クラウドQA自動実行、旧unify-blind-qa-cycle実データによる9.1リプレイ、traceカバレッジの独立実測。
- SHA-256照合はGitHub取得テキストのUTF-8バイト列に基づく。独立したgit checkout上の raw byte ハッシュコマンドは未実行。

## 指摘

### 指摘 QA-F09
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: AC-002
- 根拠: quality-loop/qa_workflow/workflow.py:563-574ではapproveが利用者発言ログ不在でもapprovalを保存する。workflow.py:693-694でloop実行時には停止するが承認受理は成立する。test_loop_integration.py:168-174もこれを前提にしている。
- 影響: AI生成文でもapproveの承認状態を作れ、ACの『場合だけ受理』に反する。loop以外の既存経路にも承認レコードが残る。
- 対応案: 承認のprovenance検証を保存前に行うか、未検証の申請をapprovalと別状態に保管する。既存approveの互換性要件とのトレードオフは仕様変更承認で解決する。
- 対象: quality-loop/qa_workflow/workflow.py
- 完了条件: 発言ログにない文がapproveから正式approvalとして保存されず、正規利用者発言でのみ承認成立。
- 検証方法: ログ無しapprove、ログ有りapprove、AIが作成した別文、loop以外の経路の承認状態を比較。

### 指摘 QA-F10
- 種別: 要求未達
- 重大度: 通常
- 状態: OPEN
- 要求対応: AC-006
- 根拠: quality-loop/qa_workflow/loop_stages.py:9は7段階、依頼のAC-006は5段階。test_loop.py:44-49も7段階を期待し、openspec/changes/improve-quality-qa-loop/design.md:27-30で仕様を変更している。
- 影響: 受入基準原文が変わらないままステージ契約が改訂され、テスト成功しても正式ACが満たされない。
- 対応案: 実際に合意された5段階へ統合・修正するか、AC-006を正式なユーザー承認を得て改定した新契約として別のレビュー対象にする。
- 対象: quality-loop/qa_workflow/loop_stages.py
- 完了条件: 受入基準とSTAGES、OpenSpec、テストの順序が整合。
- 検証方法: STAGESを列挙し承認済みACの要求段階と1対1で照合、統合テストを実行。

### 指摘 QA-F11
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: AC-009およびAC-010
- 根拠: quality-loop/qa_workflow/minor_change.py:24-34は範囲外・新規パスを停止せず50行制限も持たない。test_loop_integration.py:135-156は60行超・範囲外変更を許容する期待値。openspec/changes/improve-quality-qa-loop/specs/unified-qa-workflow/spec.mdもAC-009/010と逆の規則へ改訂。
- 影響: 未承認変更・50行超過があってもcommit前の承認ゲートが作動せず、明示された安全制約を回避する。
- 対応案: 依頼ACの範囲外・新規パス・MINOR_LINE_LIMIT=50を復元する。方針変更が必要なら受入基準の変更を事前にユーザーへ提示し別途承認を得る。
- 対象: quality-loop/qa_workflow/minor_change.py
- 完了条件: 承認外、新規パス、51行以上でcommit前停止。50行以内のみ継続。
- 検証方法: 48/50/51/60行、未追跡新規、承認外既存、承認内変更のテストでHEAD不変を確認。

### 指摘 QA-F12
- 種別: 不具合
- 重大度: 重大
- 状態: OPEN
- 要求対応: AC-012
- 根拠: quality-loop/qa_workflow/workflow.py:632-643は公開前スキャンなしでgit push。workflow.py:728-734のrun_pushがpublishに先行し、publish()にあるpublication_findingsによる検査より先に対象コードがremoteへ公開され得る。gitops.py:177-201の検査はpush_topicから未呼出。
- 影響: 秘密情報・個人ローカルパスを含んだ修正コミットがGitHubに先に公開され、後からの公開拒否では流出を取り消せない。
- 対応案: push_topic()でpush対象commit全パスのblobを直接スキャンしてからpushする。remote既到達をスキップする経路にも検査済み証跡を要求する。
- 対象: quality-loop/qa_workflow/workflow.py
- 完了条件: シークレット・個人ローカルパスを含む対象コミットでpushが一度も発生しない。
- 検証方法: bare remoteを使い修正内容にAPI_TOKEN相当値と/Users/の架空パスを入れてloopを実行、remote tip不変・stage=push失敗・再QA依頼なしを確認。

## 実施側タスク

- T-01: Finding=QA-F09; path=quality-loop/qa_workflow/workflow.py; action=承認のprovenance検証を保存前に行うか、未検証の申請をapprovalと別状態に保管する。既存approveの互換性要件とのトレードオフは仕様変更承認で解決する。; done_when=発言ログにない文がapproveから正式approvalとして保存されず、正規利用者発言でのみ承認成立。; verify=ログ無しapprove、ログ有りapprove、AIが作成した別文、loop以外の経路の承認状態を比較。
- T-02: Finding=QA-F10; path=quality-loop/qa_workflow/loop_stages.py; action=実際に合意された5段階へ統合・修正するか、AC-006を正式なユーザー承認を得て改定した新契約として別のレビュー対象にする。; done_when=受入基準とSTAGES、OpenSpec、テストの順序が整合。; verify=STAGESを列挙し承認済みACの要求段階と1対1で照合、統合テストを実行。
- T-03: Finding=QA-F11; path=quality-loop/qa_workflow/minor_change.py; action=依頼ACの範囲外・新規パス・MINOR_LINE_LIMIT=50を復元する。方針変更が必要なら受入基準の変更を事前にユーザーへ提示し別途承認を得る。; done_when=承認外、新規パス、51行以上でcommit前停止。50行以内のみ継続。; verify=48/50/51/60行、未追跡新規、承認外既存、承認内変更のテストでHEAD不変を確認。
- T-04: Finding=QA-F12; path=quality-loop/qa_workflow/workflow.py; action=push_topic()でpush対象commit全パスのblobを直接スキャンしてからpushする。remote既到達をスキップする経路にも検査済み証跡を要求する。; done_when=シークレット・個人ローカルパスを含む対象コミットでpushが一度も発生しない。; verify=bare remoteを使い修正内容にAPI_TOKEN相当値と/Users/の架空パスを入れてloopを実行、remote tip不変・stage=push失敗・再QA依頼なしを確認。

## 前回指摘の再確認

- QA-F01: 解消 | repair_commit.py:16-20で同一承認パスのstaged衝突を検査し拒否。test_repair_commit.py:61-70に回帰テストを追加（実行未確認）。
- QA-F02: 解消 | workflow.py:736-745でbaseline相当reviewedと現HEADの双方をrequa前にorigin祖先検査。
- QA-F03: 未検証 | workflow.py:681-685,715-759に重複防止ガードが追加されたが、push成功後の保存障害・部分失敗を独立故障注入テストできず完全な冪等性は未確認。
- QA-F04: 解消 | workflow.py:703-704でplan.itemsではなくunresolved全IDを履歴化している。
- QA-F05: 解消 | workflow.py:774-783でwaiting_approval時にplan path/hash/bodyを返す。
- QA-F06: 解消 | workflow.py:563-574から旧approveへのログ必須化が撤去された。元の後方互換性の懸念は解消方向。ただしAC-002の新たな承認provenance欠陥はQA-F09で別途指摘。
- QA-F07: 未検証 | workflow.py:144-145にstatusのloop進捗表示が追加されたが再開方法の表示と障害時更新を実行確認できない。
- QA-F08: 解消 | workflow.py:669-679のauthorize_publishと688-702のcloud_authorized経路を追加。test_loop_integration.py:201-229対応、未実行。

## 残余事項

- **提案**: まずQA-F12のpush前スキャン欠落を修正し、機密情報を含むfixtureでremote tip不変を検証。次にQA-F09の承認受理条件、QA-F10〜F11のAC原文とOpenSpec/AGENTSの不整合をユーザー確認のうえ解消する。
- **批判的立場**: 今回の改訂は前回不具合を修正しつつ、明示AC-006/009/010を改訂OpenSpecによって事実上緩和した。テストも緩和側の期待値になっており、テストが通ってもユーザーが固定した受入基準への適合は証明しない。公開前スキャン欠落はセキュリティ上特に重大。
- このレビューは本人の別チャットで行う静的独立検証。実環境へのcloning/pytest/OpenSpecは未達成。ユーザーの指示どおりレビュー成果物1ファイルだけをtopic branchへコミットし、製品コード・依頼・状態・他のArtifactは変更しない。
