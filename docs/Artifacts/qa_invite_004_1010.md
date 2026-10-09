# 独立QAの依頼

created: 2026-10-10 03:36 (JST)
update: 2026-10-10 03:36 (JST)
author: Claude Haiku 5.5（依頼作成）

## 目的と受入基準

quality-qa の loop 操作（承認後の修正を commit・提出・再QA依頼・公開まで進める）の独立QA

前提: 未指定

- AC-001: 承認前の loop は修正・commit・公開を行わず、計画を示して停止する
- AC-002: 承認文は利用者発言ログ（.git/qa-user-prompts.jsonl）に含まれる場合だけ受理し、AIが作った文は拒否する
- AC-003: 承認文に「修正後のcommitまで」が無い場合、commit しない
- AC-004: commit は承認済みパスだけを対象とし、未承認の変更・未追跡ファイル・他者のステージ済み変更を含めない
- AC-005: 承認文に「クラウドQAに出して」が無い場合、再QA依頼の作成前に停止する
- AC-006: 段階の順序は commit → submit → requa-request → finalize → publish である
- AC-007: 途中失敗後の再実行は完了済みの段階を繰り返さず、未完了の段階から再開する
- AC-008: 同一Finding IDが連続2サイクル未解決、または3サイクル目で未解決が残る場合に停止する
- AC-009: 承認範囲外の変更（承認済みパス外、または新規パス）がある場合、commit 前に停止する
- AC-010: 変更行数が 50 行を超える場合、commit 前に停止する（MINOR_LINE_LIMIT = 50）
- AC-011: loop は修正担当自身の判定（PASS/FAIL）を記録せず、判定段階を持たない
- AC-012: 公開前に機密情報・個人ローカルパスの検査を行い、検出があれば push しない
- AC-013: 再QA依頼の前に、対象SHAが origin/<branch> の祖先であることを確認する
- AC-014: 同梱コピー（skills/quality-qa/runtime/qa_workflow/）は正本と一致する
- AC-015: 既存の承認・提出・公開・終了の操作の意味は変更されていない（既存テストが通る）
- AC-016: openspec validate improve-quality-qa-loop --strict が通る

## 対象と担当

リポジトリ: syrius2000/QA-products
開発ブランチ: codex/blind-qa-cycle-remote-qa
初回基準: fb44ff6d53beba3f0396e01e90c92691810c82aa
差分基準: d355b70eff14dde6ffedec0e6c01a59bbc630244
対象版: 9103a9a8515f4337d4a5acefd11c6681325d5e3b
依頼ID: QA-004
サイクル: 2

実装担当 `Claude Haiku 5.5（実装担当）` とは別の担当・チャットでレビューしてください。元要求との対応、修正差分と周辺影響、前回指摘を確認し、必要なら元実装にも遡ってください。

## 差分の選別

製品対象:
- AGENTS.md
- openspec/changes/improve-quality-qa-loop/.openspec.yaml
- openspec/changes/improve-quality-qa-loop/README.md
- openspec/changes/improve-quality-qa-loop/design.md
- openspec/changes/improve-quality-qa-loop/proposal.md
- openspec/changes/improve-quality-qa-loop/specs/unified-qa-workflow/spec.md
- openspec/changes/improve-quality-qa-loop/tasks.md
- quality-loop/qa_workflow/cli.py
- quality-loop/qa_workflow/loop.py
- quality-loop/qa_workflow/loop_guard.py
- quality-loop/qa_workflow/loop_stages.py
- quality-loop/qa_workflow/minor_change.py
- quality-loop/qa_workflow/prompt_log.py
- quality-loop/qa_workflow/publish_guard.py
- quality-loop/qa_workflow/repair_commit.py
- quality-loop/qa_workflow/workflow.py
- quality-loop/skills/quality-qa/SKILL.md
- quality-loop/skills/quality-qa/references/publish.md
- quality-loop/skills/quality-qa/references/repair.md
- quality-loop/skills/quality-qa/references/results.md
- quality-loop/skills/quality-qa/runtime/qa_workflow/cli.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/loop.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/loop_guard.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/loop_stages.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/minor_change.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/prompt_log.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/publish_guard.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/repair_commit.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
- quality-loop/tests/test_approval_verbatim.py
- quality-loop/tests/test_loop.py
- quality-loop/tests/test_loop_guard.py
- quality-loop/tests/test_loop_integration.py
- quality-loop/tests/test_loop_stages.py
- quality-loop/tests/test_minor_change.py
- quality-loop/tests/test_publish_guard.py
- quality-loop/tests/test_qa_workflow_contract.py
- quality-loop/tests/test_repair_commit.py

登録済み運用成果物（製品差分から選別し、根拠として保持）:
- docs/Artifacts/qa_state_003_1010.json: ローカル状態
- docs/Artifacts/qa_invite_003_1010.md: QA依頼
- docs/Artifacts/qa_review_003_1010.md: レビュー予約先
- docs/Artifacts/implementation_plan_040_1010.md: 修正計画
- docs/Artifacts/implementation_plan_041_1010.md: 修正計画
- docs/Artifacts/implementation_plan_042_1010.md: 修正計画
- docs/Artifacts/implementation_plan_043_1010.md: 修正計画
- docs/Artifacts/qa_state_004_1010.json: ローカル状態
- docs/Artifacts/qa_invite_004_1010.md: QA依頼
- docs/Artifacts/qa_review_004_1010.md: レビュー予約先

対象外の判断:
なし

初回基準からの差分と今回差分に同じ個別パスの選別を適用してください。DIR全体の除外、未分類パスの黙示的除外は行わず、改名は旧新パスを確認します。

## 前回指摘と必要な検証

- QA-F01: {'id': 'QA-F01', '種別': '要求未達', '重大度': '重大', '状態': 'OPEN', '要求対応': 'AC-004', '根拠': '`quality-loop/qa_workflow/repair_commit.py:13-18` が既存index検査なしに`git add`。承認済みパスにすでにある他者のstageを上書きできる。隔離Git実行で再現。', '影響': '他者の既存ステージ内容を失い、承認されていない差分を承認パスのcommitへ巻き込むリスク。', '対応案': '`gitops.commit_paths` の分離index・既存stage衝突検査を再利用するか、承認パスとのstage衝突時に停止する。', '対象': 'quality-loop/qa_workflow/repair_commit.py; quality-loop/tests/test_repair_commit.py', '完了条件': '同じ承認パスに既存stageがあるとコミットせず停止し、他者のindex内容を保持する。', '検証方法': '同じ承認パス内の staged / unstaged 内容相違、別パスのstaged変更、未追跡、部分stageの4系統でindex blobとcommit treeを確認。'}
- QA-F02: {'id': 'QA-F02', '種別': '要求未達', '重大度': '重大', '状態': 'OPEN', '要求対応': 'AC-013、OpenSpecの「公開前の検査と再QA前の祖先関係を必須とする」', '根拠': '`quality-loop/qa_workflow/workflow.py:690-706` で祖先確認が `requa`・`publish` の後であり、チェック対象はreviewedだけ。`publish_guard.py:17-22`。', '影響': '対象SHA・baseline未到達の段階でも再QA依頼を作成でき、場合によってはpush済みになる。', '対応案': '正式な再QA依頼成立前に両SHAのremote祖先チェックを強制するよう、push/公開と依頼作成の責務・段階を再設計する。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/qa_workflow/publish_guard.py; quality-loop/tests/test_loop_integration.py', '完了条件': 'baseline/Reviewed SHAの少なくとも一方がoriginの祖先でない場合、再QA依頼は作成／公開されない。両方が到達しているときだけ進む。', '検証方法': 'remote未push・Reviewedのみpush・baselineのみ未到達・両方到達の4条件を統合テストで実行。'}
- QA-F03: {'id': 'QA-F03', '種別': '不具合', '重大度': '重大', '状態': 'OPEN', '要求対応': 'AC-007、OpenSpec「loopの途中失敗から安全に再開する」', '根拠': '`quality-loop/qa_workflow/loop_stages.py:13-24` は副作用の成功後に進捗を保存。`workflow.py:700-706` はpushを含む `publish()` 完了後に検査し、検査失敗だとpublish stage未完了。再試行でpublish()が再実行される。', '影響': 'push済み・依頼作成済みでも段階失敗扱いとなり、再試行時に副作用操作を重複実行する。', '対応案': 'push等のリモート操作を独立段階にし、リモート状態の照合で完了を回復する。事前条件チェックを前段に移し、状態保存失敗時はGitの既存SHAからリカバリする。', '対象': 'quality-loop/qa_workflow/loop_stages.py; quality-loop/qa_workflow/workflow.py; quality-loop/tests/test_loop_integration.py', '完了条件': 'push直後・state保存直前・requa作成直後に故障注入しても新規commit/pushや依頼作成を重複しない。', '検証方法': '各副作用直後にQAErrorを注入し、保存状態、remote tip、commit回数、QA依頼数を照合して再実行する。'}
- QA-F04: {'id': 'QA-F04', '種別': '要求未達', '重大度': '重大', '状態': 'OPEN', '要求対応': 'AC-008', '根拠': '`quality-loop/qa_workflow/workflow.py:672-674` のhistoryは `plan.items` IDであり、実際の `state["unresolved"]` のOPEN IDではない。`workflow.py:526-538` で非blocking Findingは計画対象から省略可。', '影響': '同一の未解決Findingが2サイクル継続しても、計画に入っていなければ反復停止を検出しない。', '対応案': '各サイクルのレビュー確定時点で未解決Finding ID全件をsnapshot化し、plan IDとは分離する。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/qa_workflow/loop_guard.py; quality-loop/tests/test_loop_integration.py', '完了条件': '非blocking Findingの連続OPEN、解消、再発のケースで規則通り停止する。', '検証方法': '2サイクル連続OPEN（未計画）と解消を挟む再出現、3サイクル末OPENを統合テストする。'}
- QA-F05: {'id': 'QA-F05', '種別': '要求未達', '重大度': '軽微', '状態': 'OPEN', '要求対応': 'AC-001、OpenSpec承認前停止シナリオ', '根拠': '`quality-loop/qa_workflow/loop.py:29-31` と `workflow.py:718-723` はgenericな文言のみ。plan本文やpathを返さない。', '影響': 'ユーザーが停止理由と承認対象計画を一回のloop応答から確認できない。', '対応案': '未承認時に保存済みplan本文またはpath・hash、実際に必要な承認条件を返す。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/tests/test_loop.py', '完了条件': '`loop` 未承認時の応答が計画全文あるいは明示的計画参照を含む。', '検証方法': '`Workflow.loop` の戻り値に計画識別情報・本文が存在することを統合テストする。'}
- QA-F06: {'id': 'QA-F06', '種別': '要求未達', '重大度': '重大', '状態': 'OPEN', '要求対応': 'AC-015', '根拠': '既存 `approve` はBaseline `workflow.py:553-563` で発言ログの有無を問わなかったが、対象版 `workflow.py:557-566` は `.git/qa-user-prompts.jsonl` を必須化。承認操作の利用条件が変化。', '影響': 'hook導入なし・Claude以外の通常QA操作が従来どおり実行できなくなる。AC-002とAC-015の仕様整合性を確認する必要がある。', '対応案': '承認の発話由来を安全に保証する共通アダプタを設け、旧呼出経路の互換性・移行条件を明示する。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/tests/test_qa_workflow_contract.py; openspec/changes/improve-quality-qa-loop/specs/unified-qa-workflow/spec.md', '完了条件': '旧操作の意味に関する仕様整合が取れ、全既存契約テストを実行してPASSになる。', '検証方法': 'BaselineとReviewedの旧approve操作を同一入力で比較し、hook有り無しの双方で期待動作を検証する。'}
- QA-F07: {'id': 'QA-F07', '種別': '要求未達', '重大度': '通常', '状態': 'OPEN', '要求対応': 'OpenSpec「loopの途中失敗から安全に再開する」のstatusシナリオ', '根拠': '`workflow.py:632-636` にloop完了／失敗情報の保存はあるが、`workflow.py:91-143` の`describe/status`は`loop.done`、`loop.failed`、未完了段階、再開手順を返していない。', '影響': '失敗後の次の操作を利用者が確定できず、重複操作の誘因になる。', '対応案': 'statusへstage_status()結果と復旧指示を統合する。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/tests/test_loop_integration.py', '完了条件': '失敗段階、完了段階、次段階、再開方法がstatus応答に表示される。', '検証方法': '途中QAError発生後に`Workflow.status`を呼び、全項目を検証する。'}
- QA-F08: {'id': 'QA-F08', '種別': '不具合', '重大度': '通常', '状態': 'OPEN', '要求対応': 'AC-005の停止後再開ユースケース', '根拠': '`loop.py:38-40` は承認メッセージにcloud句がないと永続停止する。`workflow.py:709-716` は保存済み`approval.message`だけを読む。`workflow.py:557-559` の`approve`は`phase == planned`専用で、commit/submit済みの`submitted`状態で承認を追加できない。`cli.py:37` のloopに後追い承認引数なし。', '影響': '「まず修正後commitまで、次にクラウドQA」という分割指示では、後からユーザーが公開を承認しても同じloopを再開できない。', '対応案': '追加の利用者発言を検証・記録してcloud gateを解除する操作を設ける。既存承認範囲を拡張しない設計にする。', '対象': 'quality-loop/qa_workflow/workflow.py; quality-loop/qa_workflow/loop.py; quality-loop/qa_workflow/cli.py', '完了条件': 'commit-only承認で2段階終了後、新たなクラウド承認によって残り3段階へ再開する。', '検証方法': '分割承認→loop停止→追加ユーザー発言→再loopの統合テスト。'}

## 実行検証契約

実行checkの指定はありません。対象環境で利用可能な場合は、受入基準に必要な製品テストを実行し、方法・環境・結果をEvidenceとして記録してください。
## Reviewerが読むQA Skillと出力契約

対象commitから以下のファイルを読み、記載hashを確認してください。不在、取得不能、またはhash不一致ならその理由をレビューへ記録し、GateをHOLDにしてください。実装担当AIの説明は根拠の代わりにせず、指摘・実施タスク・詳細なEvidenceは合意済み出力契約に従って記録してください。

- `quality-loop/skills/quality-qa/SKILL.md` — SHA-256: `278d46bb76e6367ddd7e4200234772e3bb68df1828cd342377361396d378b351`
- `quality-loop/skills/quality-qa/references/reviewer_contract.md` — SHA-256: `0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42`

## 保存と返却

変更してよいファイルは `docs/Artifacts/qa_review_004_1010.md` の日本語Markdown 1ファイルです。製品コード・依頼・管理状態は変更せず、指定先に結果を保存してください。Quality QA管理CLI・skill導入・JSONファイル作成は不要です。Pythonや既存の製品検証ツールは、対象リポジトリの規則と実行環境が許す場合に使用してください。指定ブランチが基本ですが、別ブランチ・PR・本文返却も可能です。取得元commitとパス、または本文返却であることを返信してください。レビュー成果物だけのtopic公開は依頼先の規則と許可に従い、main/masterへ統合しないでください。

指摘0件でも確認範囲と根拠を記載し、必要な確認を実行できない場合は必須確認を未完了にして未検証事項へ残してください。重大未解決・要求未達とPASSを併記しないでください。

## レビュー記載例

````markdown
# 独立QAレビュー

created: 2026-10-10 03:36 (JST)
update: 2026-10-10 03:36 (JST)
author: 担当AI (実際のモデル名)

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
- 担当: 別のレビュー担当名
- 実行経路: クラウド
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_004_1010.md
- 結論: INCONCLUSIVE
- 必須確認: 未完了

## 参照資材の検証

- quality-loop/skills/quality-qa/SKILL.md: SHA256:278d46bb76e6367ddd7e4200234772e3bb68df1828cd342377361396d378b351
- quality-loop/skills/quality-qa/references/reviewer_contract.md: SHA256:0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42

指定SHAのQA Skillと出力契約を読み、hashを照合してください。`不足`または不一致・取得不能の場合はGateをHOLDとし、その根拠を残してください。

## 確認範囲

確認した対象版のファイルと要件、根拠を記載。

## 受入基準の照合

- AC-001: 承認前の loop は修正・commit・公開を行わず、計画を示して停止する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-002: 承認文は利用者発言ログ（.git/qa-user-prompts.jsonl）に含まれる場合だけ受理し、AIが作った文は拒否する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-003: 承認文に「修正後のcommitまで」が無い場合、commit しない | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-004: commit は承認済みパスだけを対象とし、未承認の変更・未追跡ファイル・他者のステージ済み変更を含めない | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-005: 承認文に「クラウドQAに出して」が無い場合、再QA依頼の作成前に停止する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-006: 段階の順序は commit → submit → requa-request → finalize → publish である | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-007: 途中失敗後の再実行は完了済みの段階を繰り返さず、未完了の段階から再開する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-008: 同一Finding IDが連続2サイクル未解決、または3サイクル目で未解決が残る場合に停止する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-009: 承認範囲外の変更（承認済みパス外、または新規パス）がある場合、commit 前に停止する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-010: 変更行数が 50 行を超える場合、commit 前に停止する（MINOR_LINE_LIMIT = 50） | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-011: loop は修正担当自身の判定（PASS/FAIL）を記録せず、判定段階を持たない | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-012: 公開前に機密情報・個人ローカルパスの検査を行い、検出があれば push しない | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-013: 再QA依頼の前に、対象SHAが origin/<branch> の祖先であることを確認する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-014: 同梱コピー（skills/quality-qa/runtime/qa_workflow/）は正本と一致する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-015: 既存の承認・提出・公開・終了の操作の意味は変更されていない（既存テストが通る） | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-016: openspec validate improve-quality-qa-loop --strict が通る | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載

各行のID・基準原文・順序を保持し、判定と対象版の根拠を記載してください。

## 実施した検証

実行した方法・結果・根拠を記載。実行していない場合は「なし」。各指定checkについて、次のJSON行にargv、cwd、env、timeout、Python/tool runtime、status、exit_code、duration_ms、stdout/stderr excerpt、各SHA-256、output_truncatedを記録してください。statusはPASS/FAIL/NOT_RUN/ERRORです。


## 未検証事項

実行できなかった必須確認と理由を記載。ない場合は「なし」。

## 指摘

指摘がなければ「なし」。指摘がある場合は次のブロックを必要数追加。

```markdown
### 指摘 QA-F01
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: 受入基準の項目
- 根拠: src/example.py:12 対象版での観測
- 影響: 利用者への影響
- 対応案: 修正または確認の具体案
- 対象: src/example.py
- 完了条件: 観察できる完了条件
- 検証方法: 手順と期待結果
```

## 実施側タスク

修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。


## 前回指摘の再確認

- QA-F01: 未検証 | 対象版の根拠と確認方法を記載
- QA-F02: 未検証 | 対象版の根拠と確認方法を記載
- QA-F03: 未検証 | 対象版の根拠と確認方法を記載
- QA-F04: 未検証 | 対象版の根拠と確認方法を記載
- QA-F05: 未検証 | 対象版の根拠と確認方法を記載
- QA-F06: 未検証 | 対象版の根拠と確認方法を記載
- QA-F07: 未検証 | 対象版の根拠と確認方法を記載
- QA-F08: 未検証 | 対象版の根拠と確認方法を記載

## 残余事項

改善提案、残る確認と返却参照を記載。ない場合は「なし」。

````
