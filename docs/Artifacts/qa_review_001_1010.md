# 独立QAレビュー

created: 2026-10-10 04:56 (JST)
update: 2026-10-10 04:56 (JST)
author: GPT-6 (GitHub connector / independent reviewer)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-001
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/blind-qa-cycle-remote-qa
- 初回基準SHA: fb44ff6d53beba3f0396e01e90c92691810c82aa
- 差分基準SHA: fb44ff6d53beba3f0396e01e90c92691810c82aa
- 対象SHA: f513df9d15c3bc2de7755951792bffc9ad769324
- サイクル: 1
- 要件指紋: e3397f7e6f37a59dc255f349d0da4247415673dcff84384f0b034e8fde34f804
- 担当: GPT-6（独立QA担当、実装者とは別チャット）
- 実行経路: 別チャット
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_001_1010.md
- 結論: FAIL
- 必須確認: 未完了

## 参照資材の検証

- quality-loop/skills/quality-qa/SKILL.md: SHA256:4f4166f0c6de378f6ff4b2be045f671da28737886f1aa5c290c4aaabf3154723
- quality-loop/skills/quality-qa/references/reviewer_contract.md: SHA256:0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42

対象SHAのGitHub contents APIから両ファイルのUTF-8全文を取得、SHA-256を独立計算し依頼記載値と完全一致。SKILL.md 6108 bytes、reviewer_contract.md 5081 bytes、Git blob SHAはそれぞれ89000a9cf6fffd68f1af55dd1566641b8c2e49a5／76638970d31977e6650e74f366285889bbd1228c。独立SHA-256実装の既知テストベクトル SHA256("abc")=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad と一致。GitHub取得内容のUTF-8バイト列をハッシュした結果であり、ローカルclone上のraw-byte照合は未実行。

## 確認範囲

- ユーザー指定対象 f513df9d15c3bc2de7755951792bffc9ad769324 を固定し、依頼ファイル docs/Artifacts/qa_invite_001_1010.md のQA-001、サイクル1、AC-001〜019(v2)、要件指紋を読み取った。初回基準fb44ff6からのGitHub比較は11コミット、製品差分41ファイル（34件以上の追加・更新を含む。差分一覧はGitHub compare取得結果）。今回依頼ファイルは対象コミット後にtopicブランチへ公開されている運用Artifactであり、Reviewedのコードには含めていない。
- AGENTS.md、OpenSpec acceptance.md(v2)/spec.md/design.md/tasks.md、qa_workflowのloop・guard・stages・minor_change・prompt_log・publish_guard・repair_commit・workflow・gitops・cli、quality-qa Skill/参照文書、関連testsの対象SHA版を取得・読査。
- Git treeのblob SHAで正本quality-loop/qa_workflowの15ファイルと同梱skills/quality-qa/runtime/qa_workflowの15ファイルを一対一照合し一致15/15、欠落・余分なし。
- 前回案件QA-004の旧基準に対するレビュー履歴は今回の受入基準と区別。今回依頼は「前回指摘なし」と明記しているため、前回指摘の引継ぎ判定対象はない。過去のFinding F09〜F12を今回の正式Findingと混同しない。

## 受入基準の照合

- AC-001: 承認前の loop は修正・commit・公開を行わず、計画を示して停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:30-32の未承認停止とworkflow.py:808-815のplan path/hash/body返却を確認。test_loop_integration.py:109-112,176-180は対応テスト（未実行）。
- AC-002: loop は commit・push・公開の前に、承認文が利用者発言ログ（.git/qa-user-prompts.jsonl）にあることを確認し、ログにない文（AIが作った文）では何も実行しない。既存の approve の動作は変えない | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:708-714でloopの副作用より先にprompt_log.verbatim_in_logを検査し、不一致ならstopped。approve()はworkflow.py:563-574に残りログ強制条件はない。prompt_log.py:8-19。静的確認。
- AC-003: 承認文に「修正後のcommitまで」が無い場合、commit しない | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:40-42およびrepair_commit.py:12-14で固定句「修正後のcommitまで」がなければcommit前に停止。test_loop.py:57-62にテスト定義。
- AC-004: commit は承認済みパスだけを対象とし、未承認の変更・未追跡ファイル・他者のステージ済み変更を含めない | 判定: PASS | 根拠: quality-loop/qa_workflow/repair_commit.py:15-20で承認パス内の既存stageを拒否し、git add/commitは明示パス指定。tests/test_repair_commit.py:43-70に未承認、untracked、他者stageのテスト。実行は未検証。
- AC-005: 承認文に「クラウドQAに出して」が無い場合、再QA依頼の作成前に停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/loop.py:43-46はクラウド承認のない場合push段階で停止し、loop_stages.py:9の後続requa-requestには進まない。test_loop_integration.py:126-133を確認。
- AC-006: 段階の順序は commit → submit → push → ancestry（祖先確認）→ requa-request → finalize → publish の7段階である | 判定: PASS | 根拠: quality-loop/qa_workflow/loop_stages.py:9にcommit→submit→push→ancestry→requa-request→finalize→publishの7段階を順序通り定義。workflow.py:761-794のaction接続と一致。
- AC-007: 途中失敗後の再実行は完了済みの段階を繰り返さず、未完了の段階から再開する | 判定: UNVERIFIED | 根拠: loop_stages.py:12-25のstage checkpoint、workflow.py:701-706,735-790の再入時ガード、tests/test_loop_integration.py:230-254,272-301の故障注入テスト定義を確認。ただし対象SHAのpytestを実行できず、外部副作用の全失敗点で再開保証は独立検証未了。
- AC-008: 同一Finding IDが連続2サイクル未解決、または3サイクル目で未解決が残る場合に停止する | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:723-724でunresolved IDの履歴を収集し、loop_guard.py:17-23で2サイクルの積集合と3サイクル上限を判定。test_loop_guard.py:13-43の境界ケースを確認。
- AC-009: 承認済みパス外の変更・新規パスでは停止しない。コミットには含めず、結果の left_out に記録する。承認外のファイルがHEADまでのコミットに含まれる場合は、提出の前に停止する | 判定: FAIL | 根拠: quality-loop/qa_workflow/minor_change.py:29-35は承認外をoutside_pathsへ分離し、repair_commit.py:15-20は承認パスのみcommit。ただしworkflow.py:733-741でleft_outは段階状態done.commitにのみ入り、workflow.py:800-815の_loop_replyにはleft_outキーがない。依頼文の「結果の left_out に記録」を満たす戻り値がない。
- AC-010: 変更行数では停止しない（行数上限は設けない） | 判定: PASS | 根拠: quality-loop/qa_workflow/minor_change.py:26-35は契約hashのみ停止要因とし行数条件を使用しない。tests/test_loop_integration.py:135-142は60行の変更が続行する期待値（未実行）。
- AC-011: loop は修正担当自身の判定（PASS/FAIL）を記録せず、判定段階を持たない | 判定: PASS | 根拠: quality-loop/qa_workflow/loop_stages.py:9にreview/verdict段階なし。workflow.py:761-796のactionsも判定を含まず、submitはindependently_verified=False（workflow.py:596）。
- AC-012: push の前に、送出する全コミットの変更ファイルについて、コミット済みの内容の機密情報・個人ローカルパスを検査し、検出があれば push しない | 判定: FAIL | 根拠: quality-loop/qa_workflow/gitops.py:205-213のoutgoing_findingsはchanged(root,base,head)＝始終差分に載る最終HEAD blobだけを走査し、途中コミットごとの変更ファイルのblobは走査しない。workflow.py:637-642のpush_topicでこの不完全な走査をpush直前の必須検査に用いる。機密追加→復元の2コミットでは基準..HEAD差分0だが中間コミットに機密が残ることを隔離Gitで再現。
- AC-013: 再QA依頼の前に、対象SHAと基準SHAの両方が origin/<branch> の祖先であることを確認する | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:756-766でancestry actionが前回reviewed（baseline）と現在HEAD（新対象）の両方をorigin/<branch>で確認し、requa-requestより前に置く。publish_guard.py:17-22に祖先判定。
- AC-014: 同梱コピー（skills/quality-qa/runtime/qa_workflow/）は正本と一致する | 判定: PASS | 根拠: 対象f513df9のGit treeを比較し、quality-loop/qa_workflow/正本15ファイルとskills/quality-qa/runtime/qa_workflow/同梱15ファイルのGit blob SHAが15/15一致。欠落・余分・不一致0。
- AC-015: 既存の承認・提出・公開・終了の操作の意味は変更されていない（既存テストが通る） | 判定: UNVERIFIED | 根拠: workflow.py:563-630のapprove/submit/decide、266-373のpublish等のAPI存続は静的確認したが、既存test_qa_workflow_contract.pyを含むpytestを対象SHAで実行できず、意味と互換性の完全維持を確認していない。
- AC-016: openspec validate improve-quality-qa-loop --strict が通る | 判定: UNVERIFIED | 根拠: openspec/changes/improve-quality-qa-loop/acceptance.mdとspec.mdを読査したが、対象SHAをcheckoutできずopenspec validate improve-quality-qa-loop --strictの独立実行結果がない。
- AC-017: 完了条件・受入基準・確認方法の本文が承認時点から変わった場合、loop は停止して再承認を求める | 判定: PASS | 根拠: quality-loop/qa_workflow/workflow.py:667-671で保存済みplan本文の現在hashを読取り、minor_change.py:31-34で承認時のplan_hashとの不一致を停止判定。loop.py:37-39でcommit前停止。
- AC-018: 公開後に、リポジトリ・ブランチ・依頼ファイル・対象版・保存先を埋めた短いクラウド指示書を表示する手順が skill 文書にあり、結果は保存先の1ファイルから acquire で取得できる | 判定: PASS | 根拠: quality-loop/skills/quality-qa/references/publish.md:31-40にrepository/branch/invite/reviewed/review_pathを埋める短いクラウド指示書があり、references/results.md:3,7とqa_workflow/workflow.py:418-480にacquireの結果取得経路を確認。公開とacquireの実運用実行は未検証。
- AC-019: 同一指摘の反復で停止したloopは、利用者の発言（発言ログにあり「続行」を含む）を `authorize-continue` で記録すると、記録した指摘IDに限り続行できる。修正サイクルの上限と、記録にない指摘の反復では停止する | 判定: FAIL | 根拠: quality-loop/qa_workflow/workflow.py:685-699のauthorize_continueは発言ログを確認するが、line 690で「続行」だけでなく「継続」も受理し、さらにloopが実際に反復停止した状態かの検証がない。AC-019の「続行」を含む発言で反復停止後に記録する条件より受理範囲が広い。loop_guard.py:17-23には免除ID限定と3サイクル上限保持がある。

## 実施した検証

- GitHub読み取り: 対象commit、指定branch、依頼全文、acceptance.md(v2)、元仕様、主要ソース、関連テストを取得。compare fb44ff6..f513df9 はahead 11 commits。対象と依頼のrepository/branch/SHA/AC原文/指紋が一致することを確認。
- 参照資材SHA-256: SKILL.mdとreviewer_contract.mdでいずれも一致（上記参照資材節）。
- 正本対runtimeのGit blob SHA: 15件一致／15件、差異0。
- 独立Git再現（隔離した一時Gitリポジトリ、Git CLI）: baseでp.py='safe'、次コミットでAPI_TOKEN相当の架空値を挿入、次コミットで元に戻す。git diff --name-only base HEAD のパス数は0だが git rev-list base..HEAD は2コミットで、中間コミットのblobには値が残る。この条件では gitops.py:205-213のchanged(base,HEAD)が空になり、outgoing_findingsは必須検査対象を列挙できない（AC-012、QA-F01）。検証はGit差分意味論とコードの直接照合であり、対象版outgoing_findings関数をimportして実行した結果ではない。
- pytest（`cd quality-loop && python3 -m pytest tests -q`）: NOT_RUN。対象git checkoutを取得するためのgithub.comへのDNS解決が実行環境で失敗。実装者の成功申告は独立PASSとしない。
- openspec（`openspec validate improve-quality-qa-loop --strict`）: NOT_RUN。対象checkoutとCLIを使用できないため実行不能。
- CI: このレビューでは対象版の成功CIログを独立検証していない。依頼に構造化された必須checkの登録は0件。未実行のpytestとOpenSpec strictはAC-015/016のUNVERIFIEDに残す。
- AC集計：PASS 13、FAIL 3、UNVERIFIED 3。provenance一致、明確なAC FAILあり→Gate=FAIL、必須確認=未完了。

## 未検証事項

- 対象SHAに対するpytest全件実行およびOpenSpec strict validation（独立実行できないため成功とは記載しない）。
- AC-007の各副作用直後のクラッシュ再開・永続化障害・remoteとの競合を対象実装で再現する統合試験。
- UserPromptSubmit hookが実環境で記録するログの真正性と改ざん耐性、クラウド独立QA実環境でのend-to-end実行。
- 以前から残る旧形式データのリプレイ代替と標準ライブラリtraceによる近似カバレッジの独立再測定。
- SHA-256はGitHubから取得したUTF-8テキストに対する独立計算である。git cloneからのraw-fileの再ハッシュではない。

## 指摘

### 指摘 QA-F01
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: AC-012、OpenSpec「公開前の検査と再QA前の祖先関係を必須とする」
- 根拠: quality-loop/qa_workflow/gitops.py:205-213 の outgoing_findings は最終HEADとbaseの差分パスだけに対して HEAD:path を読み、送出する各コミットのblobを読んでいない。workflow.py:637-642 はこの結果が空ならpushする。tests/test_publish_guard.py:41-60のテストも一時的な機密追加と後続除去を試していない。
- 影響: push対象履歴の途中コミットに秘密情報や個人パスを含む場合、最終HEADがクリーンでも秘密がGit履歴ごと外部公開される。
- 対応案: git rev-list base..HEAD の全送出コミットを列挙し、各親との差分に現れる追加・変更blobを当該コミットSHAで走査する。削除のみはblobなしとして処理し、重複はSHAで抑制してもよい。push時と事前計算のHEAD/remote tip固定も検査する。
- 対象: quality-loop/qa_workflow/gitops.py
- 完了条件: 中間コミットに秘密があり最終HEADでは消えている履歴でもpush前に拒否され、remoteのtipが不変。
- 検証方法: 隔離bare remoteに対し (1) baseの安全ファイル、(2)秘密を追加したcommit A、(3)元に戻したcommit B を用意。git diff base..Bのパス数0を確認後、outgoing_findingsがAの秘密を検知しloop/push_topicがpushせず停止することをテスト。

### 指摘 QA-F02
- 種別: 要求未達
- 重大度: 通常
- 状態: OPEN
- 要求対応: AC-009の「結果の left_out に記録する」
- 根拠: quality-loop/qa_workflow/workflow.py:733-741 はleft_outをdone.commitに格納するが、workflow.py:800-815の_loop_replyはstatus,reason,completed,next,planのみを返し、top-levelのleft_outがない。tests/test_loop_integration.py:144-156は内部stateだけをassertして返却結果を検査していない。
- 影響: 承認外で残された変更一覧がloopの呼出結果に現れず、利用者・自動実行側が除外範囲を認識しにくい。
- 対応案: loopの返却契約にleft_outを追加し、stage再開時もdone.commit.left_outから保持して返却する。内部stateと表示結果の一致テストを追加する。
- 対象: quality-loop/qa_workflow/workflow.py
- 完了条件: 承認外変更があるケースで、loop結果にleft_out配列が現れ、stage再開後も同一値を返す。
- 検証方法: 範囲外の追跡済み変更と新規未追跡ファイルを用いたloop統合テストで返却JSONのleft_outと実際のcommit差分を突合。

### 指摘 QA-F03
- 種別: 要求未達
- 重大度: 通常
- 状態: OPEN
- 要求対応: AC-019の続行発言および反復停止後の承認条件
- 根拠: quality-loop/qa_workflow/workflow.py:685-699 の authorize_continue は line 690で「続行|継続」を許可し、実際のloopが反復理由でstoppedになったことを検査しない。tests/test_loop_integration.py:311-344は「続行」成功と非反復拒否は試すが「継続」単独や停止前の反復事前承認を試していない。
- 影響: 依頼の明示的な「続行」を含まない発言や、停止前の先回り操作で反復停止ゲートの免除記録を作成できる。
- 対応案: 受入基準どおり「続行」の明示句を必須とし、現在のloopが同一指摘の反復を理由に停止したことを状態で確認してからcontinue_authorizationへIDを記録する。もし「継続」も許容するならAC-019を事前承認で更新する。
- 対象: quality-loop/qa_workflow/workflow.py
- 完了条件: 停止前・『継続』単独では承認が作成されず、反復停止後にログにある『続行』発言を用いたときのみID限定で解除される。
- 検証方法: 反復停止前／後、発言ログ有／無、文言『続行』／『継続』、3サイクル上限、および未記録ID反復を境界テストで検証。

## 実施側タスク

- T-01: Finding=QA-F01; path=quality-loop/qa_workflow/gitops.py; action=git rev-list base..HEAD の全送出コミットを列挙し、各親との差分に現れる追加・変更blobを当該コミットSHAで走査する。削除のみはblobなしとして処理し、重複はSHAで抑制してもよい。push時と事前計算のHEAD/remote tip固定も検査する。; done_when=中間コミットに秘密があり最終HEADでは消えている履歴でもpush前に拒否され、remoteのtipが不変。; verify=隔離bare remoteに対し (1) baseの安全ファイル、(2)秘密を追加したcommit A、(3)元に戻したcommit B を用意。git diff base..Bのパス数0を確認後、outgoing_findingsがAの秘密を検知しloop/push_topicがpushせず停止することをテスト。
- T-02: Finding=QA-F02; path=quality-loop/qa_workflow/workflow.py; action=loopの返却契約にleft_outを追加し、stage再開時もdone.commit.left_outから保持して返却する。内部stateと表示結果の一致テストを追加する。; done_when=承認外変更があるケースで、loop結果にleft_out配列が現れ、stage再開後も同一値を返す。; verify=範囲外の追跡済み変更と新規未追跡ファイルを用いたloop統合テストで返却JSONのleft_outと実際のcommit差分を突合。
- T-03: Finding=QA-F03; path=quality-loop/qa_workflow/workflow.py; action=受入基準どおり「続行」の明示句を必須とし、現在のloopが同一指摘の反復を理由に停止したことを状態で確認してからcontinue_authorizationへIDを記録する。もし「継続」も許容するならAC-019を事前承認で更新する。; done_when=停止前・『継続』単独では承認が作成されず、反復停止後にログにある『続行』発言を用いたときのみID限定で解除される。; verify=反復停止前／後、発言ログ有／無、文言『続行』／『継続』、3サイクル上限、および未記録ID反復を境界テストで検証。

## 前回指摘の再確認

- 対象: なし

## 残余事項

- 提案: QA-F01を最優先とし、全送出コミットの個別blobを対象に秘密情報を走査した後にpushする設計へ修正する。続いてQA-F02の返却契約とQA-F03の承認境界をテストで固定する。
- 批判的立場: 現行test_publish_guard.pyには最後のコミットに秘密が残るケースはあるが、途中コミットで挿入・復元された履歴ケースはない。終点スナップショットだけではGit履歴に残る機密情報の漏洩を防げない。安全なpushの前提が未成立のため、今回の受入はFAILとする。
- 本レビューは製品コードを変更しない。運用Artifactや状態を更新せず、GitHubブランチへ指定レビューMarkdown1ファイルだけを公開する。main/masterへの統合は行わない。
