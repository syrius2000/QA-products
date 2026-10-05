# 独立QAの依頼

created: 2026-10-04 12:15 (JST)
update: 2026-10-04 12:15 (JST)
author: Codex (GPT-6)

## 目的と受入基準

3つのQAスキルを使いやすい入口に統合し、クラウド／ローカルQA、結果確認、承認後のローカル修正、再QAの次工程を明確にする変更をレビューする

前提: 未指定

- 初回依頼からQA方式、担当、対象、受入基準、保存先、次の操作までを日本語で案内し、専門用語だけに依存しないこと
- クラウドQAが固定されたGitHub対象を読み、指定された日本語Markdown一つだけを提出する契約とし、クラウド側へローカル修正・Python実行環境を要求しないこと
- クラウド公開は承認対象だけを通常のtopic branchに送り、対象外差分・無関係な履歴・個人のローカルパスを混入させないこと
- 通常QAの契約と既存のquality-review／quality-response正式case契約、blind-qa-cycleの役割、OpenSpec正本との境界が矛盾しないこと
- テスト、仕様、配布スクリプトが相互に整合し、未検証のPython 3.10実行や実クラウドQAを完了扱いしないこと

## 対象と担当

リポジトリ: syrius2000/QA-products
開発ブランチ: codex/qa-skill-integration-cloud-qa
初回基準: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
差分基準: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
対象版: 7d8880b2558cfabcc517b95b10b87b5ccebae03a
依頼ID: QA-001
サイクル: 1

実装担当 `Codex / QA-skill-integration` とは別の担当・チャットでレビューしてください。元要求との対応、修正差分と周辺影響、前回指摘を確認し、必要なら元実装にも遡ってください。

## 差分の選別

製品対象:
- AGENTS.md
- README.md
- openspec/specs/proportional-qa-gates/spec.md
- openspec/specs/reviewer-verification-integrity/spec.md
- openspec/specs/spec-driven-qa/spec.md
- quality-loop/FUNCTIONAL_SPEC.md
- quality-loop/README.md
- quality-loop/SKILL_DEPLOYMENT_GUIDE.md
- scripts/sync_productivity_skills.py
- docs/Artifacts/implementation_plan_024_1004.md
- docs/Artifacts/implementation_plan_025_1004.md
- openspec/changes/unify-qa-skill-workflow/.openspec.yaml
- openspec/changes/unify-qa-skill-workflow/design.md
- openspec/changes/unify-qa-skill-workflow/proposal.md
- openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md
- openspec/changes/unify-qa-skill-workflow/tasks.md
- openspec/specs/README.md
- openspec/specs/quality-loop-skill-deployment/spec.md
- openspec/specs/unified-qa-workflow/spec.md
- quality-loop/REQUIREMENTS.md
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
- quality-loop/skills/quality-qa/runtime/qa_workflow/__init__.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/cli.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/github.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/gitops.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/legacy.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/review.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/store.py
- quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
- quality-loop/skills/quality-qa/templates/qa_review.md
- quality-loop/tests/test_qa_package.py
- quality-loop/tests/test_qa_workflow.py

登録済み運用成果物（製品差分から選別し、根拠として保持）:
- docs/Artifacts/qa_state_001_1004.json: ローカル状態
- docs/Artifacts/qa_invite_001_1004.md: QA依頼
- docs/Artifacts/qa_review_001_1004.md: レビュー予約先

対象外の判断:
- docs/Artifacts/qa_baseline_001_1004.json: QAパッケージ内部の基準スナップショットで、製品要件ではない運用メタデータ
- docs/Artifacts/qa_candidate_001_1004.json: QAパッケージ内部の候補スナップショットで、製品要件ではない運用メタデータ
- docs/Artifacts/qa_implementation_001_1004.md: 本QA対象の実装者側検証記録であり、独立レビュー対象の製品ではない
- docs/Artifacts/qa_independent_review_001_1004.md: 本QA以前の独立確認記録であり、今回のクラウドレビュー成果物ではない
- docs/Artifacts/spec_alignment_001_1004.md: 実装前の仕様整合記録であり、今回のレビュー成果物ではない

初回基準からの差分と今回差分に同じ個別パスの選別を適用してください。DIR全体の除外、未分類パスの黙示的除外は行わず、改名は旧新パスを確認します。

## 前回指摘と必要な検証

前回指摘なし

- 必須確認: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quality-loop pytest quality-loop/tests（実行環境でpytestを利用できない場合は未実施理由を記録）

## 保存と返却

変更してよいファイルは `docs/Artifacts/qa_review_001_1004.md` の日本語Markdown 1ファイルです。製品コード・依頼・管理状態は変更せず、指定先に結果を保存してください。Python・Quality Loop CLI・スキル導入・JSON作成は不要です。指定ブランチが基本ですが、別ブランチ・PR・本文返却も可能です。取得元commitとパス、または本文返却であることを返信してください。レビュー成果物だけのtopic公開は依頼先の規則と許可に従い、main/masterへ統合しないでください。

指摘0件でも確認範囲と根拠を記載し、必要な確認を実行できない場合は必須確認を未完了にして未検証事項へ残してください。重大未解決・要求未達とPASSを併記しないでください。

## レビュー記載例

````markdown
# 独立QAレビュー

created: 2026-10-04 12:15 (JST)
update: 2026-10-04 12:15 (JST)
author: 担当AI (実際のモデル名)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-001
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/qa-skill-integration-cloud-qa
- 初回基準SHA: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
- 差分基準SHA: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
- 対象SHA: 7d8880b2558cfabcc517b95b10b87b5ccebae03a
- サイクル: 1
- 要件指紋: a85bad11b55caa0140297df2be9cee37d0fc99ed299912684dc27855437f7d0c
- 担当: 別のレビュー担当名
- 実行経路: クラウド
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_001_1004.md
- 結論: INCONCLUSIVE
- 必須確認: 未完了

## 確認範囲

確認した対象版のファイルと要件、根拠を記載。

## 実施した検証

実行した方法・結果・根拠を記載。実行していない場合は「なし」。

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

## 前回指摘の再確認

- 対象: なし

## 残余事項

改善提案、残る確認と返却参照を記載。ない場合は「なし」。

````
