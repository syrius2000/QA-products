# QA依頼の下書き：対象確定待ち

created: 2026-10-04 21:21 (JST)
update: 2026-10-04 21:21 (JST)
author: Codex (GPT-6)

対象は未commitです。この下書きを正式依頼として渡さず、表示対象をローカルでcommitする指示、ユーザー作成commitの確認、またはクラウド公開の明示指示で対象を確定してください。

## 目的と受入基準

Plan033で実装した統合QAループ（QA依頼前Git基準づくりから、独立QA、結果回収、承認後修正、再QA、終了判断まで）の全残実装を独立レビューする

前提: QA基準はPlan033開始時点から今回の対象確定SHAまでの全差分。必要な実行検証は指定環境で試し、不能ならINCONCLUSIVE/未検証として明示する。

- AC-001: QA依頼前にbranch、HEAD、upstream/default branchとstaged・unstaged・untrackedを確認し、既存変更を保持してclean baselineへ導くこと
- AC-002: 初回QA依頼で初回基準SHA、reviewed SHA、全受入基準、変更対象パスを固定し、後続HEAD変更で対象がずれないこと
- AC-003: 受入基準の全件が依頼とレビューMarkdownに列挙され、完全一致が機械検証されること
- AC-004: 必須検証をargv/cwd/env/timeout/exit code付きで実行し、Evidenceと未実施理由を区別しPASSを捏造しないこと
- AC-005: クラウドQA公開は許可対象だけのQA専用commitと新規topic branchの通常pushに限定し、機密・ローカルパス・remote ancestry・衝突を検査すること
- AC-006: レビュー結果は指定先のMarkdown一つで回収し、依頼ID・repo・全基準・SHA・cycle・Finding・根拠・修正タスク・確認方法を照合して原文保持すること
- AC-007: Finding修正前に計画を作り、人の承認hash・path・methodに結びつけ、承認外の変更をsubmit/re-QA snapshotへ混入させないこと
- AC-008: 再QAで元依頼・全受入基準・前回Findingと履歴を継承し、解消Evidenceと未解決/未検証事項を正しく判定すること
- AC-009: 終了判断は人間に残し、自動merge/deploy/closeや実施者によるQA結果改変を行わないこと
- AC-010: 旧blind-qa-cycleとの互換経路は読取専用とし、新しい一Markdown契約と矛盾しないこと

## 対象と担当

リポジトリ: syrius2000/QA-products
開発ブランチ: codex/unify-qa-skill-workflow
初回基準: ad6ca1ee196bd75bed026858c2de9586ca49c85c
差分基準: ad6ca1ee196bd75bed026858c2de9586ca49c85c
対象版: 未確定
依頼ID: QA-002
サイクル: 1

実装担当 `Codex implementation agent` とは別の担当・チャットでレビューしてください。元要求との対応、修正差分と周辺影響、前回指摘を確認し、必要なら元実装にも遡ってください。

## 差分の選別

製品対象:
- AGENTS.md
- README.md
- docs/Archives/qa_workflow/qa_workflow_history_001_1004.md
- docs/Artifacts/implementation_plan_029_1004.md
- docs/Artifacts/implementation_plan_030_1004.md
- docs/Artifacts/implementation_plan_031_1004.md
- docs/Artifacts/implementation_plan_032_1004.md
- docs/Artifacts/implementation_plan_033_1004.md
- docs/Artifacts/implementation_report_001_1004.md
- docs/Artifacts/qa_implementation_baseline_001_1004.md
- docs/Artifacts/qa_invite_001_1004.md
- docs/Artifacts/qa_runtime_inventory_001_1004.md
- docs/Artifacts/qa_source_manifest_001_1004.md
- docs/Artifacts/qa_state_001_1004.json
- openspec/changes/unify-qa-skill-workflow/.openspec.yaml
- openspec/changes/unify-qa-skill-workflow/design.md
- openspec/changes/unify-qa-skill-workflow/proposal.md
- openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md
- openspec/changes/unify-qa-skill-workflow/tasks.md
- quality-loop/FUNCTIONAL_SPEC.md
- quality-loop/README.md
- quality-loop/SKILL_DEPLOYMENT_GUIDE.md
- quality-loop/qa_workflow/__init__.py
- quality-loop/qa_workflow/cli.py
- quality-loop/qa_workflow/github.py
- quality-loop/qa_workflow/gitops.py
- quality-loop/qa_workflow/legacy.py
- quality-loop/qa_workflow/review.py
- quality-loop/qa_workflow/store.py
- quality-loop/qa_workflow/workflow.py
- quality-loop/skills/blind-qa-cycle/SKILL.md
- quality-loop/skills/blind-qa-cycle/references/audience_channels.md
- quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md
- quality-loop/skills/blind-qa-cycle/references/focus_math_definitions.md
- quality-loop/skills/blind-qa-cycle/references/focus_openspec_coherence.md
- quality-loop/skills/blind-qa-cycle/references/focus_path_sanitization.md
- quality-loop/skills/blind-qa-cycle/references/focus_provenance_plans.md
- quality-loop/skills/blind-qa-cycle/references/git_wip_flow.md
- quality-loop/skills/blind-qa-cycle/references/machine_schema.md
- quality-loop/skills/quality-qa/CHANGELOG.md
- quality-loop/skills/quality-qa/SKILL.md
- quality-loop/skills/quality-qa/VERSION
- quality-loop/skills/quality-qa/bin/quality-qa-cli
- quality-loop/skills/quality-qa/evals/evals.json
- quality-loop/skills/quality-qa/references/prepare.md
- quality-loop/skills/quality-qa/references/publish.md
- quality-loop/skills/quality-qa/references/repair.md
- quality-loop/skills/quality-qa/references/results.md
- quality-loop/skills/quality-qa/references/reviewer_contract.md
- quality-loop/skills/quality-qa/runtime/qa_workflow/__init__.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/cli.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/github.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/gitops.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/legacy.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/review.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/store.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
- quality-loop/skills/quality-qa/templates/qa_review.md
- quality-loop/tests/test_qa_workflow_contract.py
- quality-loop/tests/test_sync_productivity_skills.py
- scripts/sync_productivity_skills.py

登録済み運用成果物（製品差分から選別し、根拠として保持）:
- docs/Artifacts/qa_state_002_1004.json: ローカル状態
- docs/Artifacts/qa_invite_002_1004.md: QA依頼
- docs/Artifacts/qa_review_002_1004.md: レビュー予約先

対象外の判断:
なし

初回基準からの差分と今回差分に同じ個別パスの選別を適用してください。DIR全体の除外、未分類パスの黙示的除外は行わず、改名は旧新パスを確認します。

## 前回指摘と必要な検証

前回指摘なし

## 実行検証契約

依頼に列挙したcheckは、対象SHAで利用可能な環境・規則の範囲内で実行してください。argv配列をshell経由で解釈せず実行し、環境構築のための無許可install、network、credential利用は行わないでください。Python等の製品検証ツールが利用可能なら実行し、QA管理CLIの導入は不要です。各結果はtype、status、runtime、argv、cwd、env、timeout、exit code、duration、stdout/stderr excerpt、完全な出力のSHA-256、excerpt切詰め有無を記録します。必須checkのFAILは総合FAIL、必須checkのNOT_RUN/ERRORはPASS不可です。環境不足は理由付きで未検証として残します。

- CHECK-PYTHON（python-version／必須）: argv=["python3", "--version"]; cwd=.; env={}; timeout=30秒; expected_exit_codes=[0]; Python minimum=3.10
- CHECK-QUALITY-LOOP（command／必須）: argv=["pytest", "tests", "-q"]; cwd=quality-loop; env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "."}; timeout=900秒; expected_exit_codes=[0]
## Reviewerが読むQA Skillと出力契約

対象commitから以下のファイルを読み、記載hashを確認してください。不在、取得不能、またはhash不一致ならその理由をレビューへ記録し、GateをHOLDにしてください。実装担当AIの説明は根拠の代わりにせず、指摘・実施タスク・詳細なEvidenceは合意済み出力契約に従って記録してください。

- `quality-loop/skills/quality-qa/SKILL.md` — SHA-256: `653d9ecc29ee59b954f2010d3e6dfa9c00bc65a872078f0945156098885d681d`
- `quality-loop/skills/quality-qa/references/reviewer_contract.md` — SHA-256: `不足`

## 保存と返却

変更してよいファイルは `docs/Artifacts/qa_review_002_1004.md` の日本語Markdown 1ファイルです。製品コード・依頼・管理状態は変更せず、指定先に結果を保存してください。Quality QA管理CLI・skill導入・JSONファイル作成は不要です。Pythonや既存の製品検証ツールは、対象リポジトリの規則と実行環境が許す場合に使用してください。指定ブランチが基本ですが、別ブランチ・PR・本文返却も可能です。取得元commitとパス、または本文返却であることを返信してください。レビュー成果物だけのtopic公開は依頼先の規則と許可に従い、main/masterへ統合しないでください。

指摘0件でも確認範囲と根拠を記載し、必要な確認を実行できない場合は必須確認を未完了にして未検証事項へ残してください。重大未解決・要求未達とPASSを併記しないでください。

## レビュー記載例

````markdown
# 独立QAレビュー

created: 2026-10-04 21:21 (JST)
update: 2026-10-04 21:21 (JST)
author: 担当AI (実際のモデル名)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-002
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/unify-qa-skill-workflow
- 初回基準SHA: ad6ca1ee196bd75bed026858c2de9586ca49c85c
- 差分基準SHA: ad6ca1ee196bd75bed026858c2de9586ca49c85c
- 対象SHA: None
- サイクル: 1
- 要件指紋: a6173a3c16527a0d4f5216cd0afe03f69d3373553261cbcde5931e2ed0357605
- 担当: 別のレビュー担当名
- 実行経路: クラウド
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_002_1004.md
- 結論: INCONCLUSIVE
- 必須確認: 未完了

## 参照資材の検証

- quality-loop/skills/quality-qa/SKILL.md: SHA256:653d9ecc29ee59b954f2010d3e6dfa9c00bc65a872078f0945156098885d681d
- quality-loop/skills/quality-qa/references/reviewer_contract.md: SHA256:不足

指定SHAのQA Skillと出力契約を読み、hashを照合してください。`不足`または不一致・取得不能の場合はGateをHOLDとし、その根拠を残してください。

## 確認範囲

確認した対象版のファイルと要件、根拠を記載。

## 受入基準の照合

- AC-001: QA依頼前にbranch、HEAD、upstream/default branchとstaged・unstaged・untrackedを確認し、既存変更を保持してclean baselineへ導くこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-002: 初回QA依頼で初回基準SHA、reviewed SHA、全受入基準、変更対象パスを固定し、後続HEAD変更で対象がずれないこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-003: 受入基準の全件が依頼とレビューMarkdownに列挙され、完全一致が機械検証されること | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-004: 必須検証をargv/cwd/env/timeout/exit code付きで実行し、Evidenceと未実施理由を区別しPASSを捏造しないこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-005: クラウドQA公開は許可対象だけのQA専用commitと新規topic branchの通常pushに限定し、機密・ローカルパス・remote ancestry・衝突を検査すること | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-006: レビュー結果は指定先のMarkdown一つで回収し、依頼ID・repo・全基準・SHA・cycle・Finding・根拠・修正タスク・確認方法を照合して原文保持すること | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-007: Finding修正前に計画を作り、人の承認hash・path・methodに結びつけ、承認外の変更をsubmit/re-QA snapshotへ混入させないこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-008: 再QAで元依頼・全受入基準・前回Findingと履歴を継承し、解消Evidenceと未解決/未検証事項を正しく判定すること | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-009: 終了判断は人間に残し、自動merge/deploy/closeや実施者によるQA結果改変を行わないこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載
- AC-010: 旧blind-qa-cycleとの互換経路は読取専用とし、新しい一Markdown契約と矛盾しないこと | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載

各行のID・基準原文・順序を保持し、判定と対象版の根拠を記載してください。

## 実施した検証

実行した方法・結果・根拠を記載。実行していない場合は「なし」。各指定checkについて、次のJSON行にargv、cwd、env、timeout、Python/tool runtime、status、exit_code、duration_ms、stdout/stderr excerpt、各SHA-256、output_truncatedを記録してください。statusはPASS/FAIL/NOT_RUN/ERRORです。

- CHECK-PYTHON: {"type":"python-version","argv":["python3","--version"],"cwd":".","env":{},"timeout_seconds":30,"python_minimum":"3.10","status":"NOT_RUN","runtime":"Python/tool version","reason":"未実行理由"}
- CHECK-QUALITY-LOOP: {"type":"command","argv":["pytest","tests","-q"],"cwd":"quality-loop","env":{"PYTHONDONTWRITEBYTECODE":"1","PYTHONPATH":"."},"timeout_seconds":900,"status":"NOT_RUN","runtime":"Python/tool version","reason":"未実行理由"}

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

- 対象: なし

## 残余事項

改善提案、残る確認と返却参照を記載。ない場合は「なし」。

````
