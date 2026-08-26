# QA-0008 三版QA機能互換性とLegacy互換性の独立レビュー

created: 2026-08-27 01:56 (JST)
update: 2026-08-27 05:20 (JST)
author: Codex (GPT-5)

## レビュー識別情報

- ケースID: QA-0008
- 対象: `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/`
- サイクル: 1
- 行動: independent-review
- agent_id: `codex-reviewer-20260827-qa0008`
- 役割: reviewer
- 実行環境: Codex / Python 3.14 / macOS / リポジトリ内ステージ環境
- 基準時点: 2026-08-27 01:56 JST
- Git正本: 未検出（`unverified-no-git`）

## 目的と比例性

目的は、Legacyを改造せず、Candidateとcompactの安全性・互換性差分をEvidence化し、compact採用可否を人間が判断できる状態にすることである。対象はQA補助Skillの比較ハーネスとステージBundleであり、外部Skill配備は範囲外とした。

運用プロファイルは、実機・外部AI API・本番Skill環境の接続が確認できないため、`standard`相当で評価した。動的Token・Latencyおよび未取得のAgent項目は`unverified`または`evidence-gap`とし、推定値をObservedへ変換していない。

## 独立確認の結果

- `python3 -B -m unittest discover -s stage/tests -p 'test_*.py'`: 49件成功。
- Bundle Manifestの再検証: 成功。
- `safety-regression.json`: Candidate／compactの安全回帰とQA-0006／QA-0007回帰はObserved。
- `size-report.json`: Legacy 3,407行、Candidate 5,953行、compact 878行。compactは1,760行目安内。
- `agent-aggregate.json`: 5 Agent／Runを分離集計。Token・Latencyは全件`unverified`。
- `overall-report.json`: `evidence-gap`、`human-adjudication-required`、配備不可。Candidate空Evidence受理の観測違反とAgent／Run必須項目の欠測が残る。

## 判定

- 技術的判定: `accepted-with-residual-risk`
- ケース状態: `closed`
- 受入結果: `accepted-with-residual-risk`
- 未解決Finding: 0件（F01は技術的にfailedのままrisk-accepted）
- 残余リスク: F01のCandidate固有違反、Legacy後発契約の意図的非互換、動的性能未検証、Agent Evidence項目の不均一、外部配備未実施

## Findings

- QA-0008-F01: Candidateが空Evidenceを受理する観測違反。`spec-drift`、High、技術判定`failed`、Owner裁定`risk-accepted`。
- QA-0008-F02: Candidateの実在semantic digest回帰を確認し、content digest／version不在を適用外として分離した。`fixed-and-verified`。
- QA-0008-F03: Agent／Runの必須項目判定を値レベルへ拡張し、欠測を正しく`unverified`として集計した。`fixed-and-verified`。
- QA-0008-F04: Source Manifestにより元EvidenceのSHA-256、追加・削除・改変・秘密値を検証し、再集計できることを確認した。`fixed-and-verified`。
- QA-0008-F05: 5.2の追加Evidence後にtasks.mdの完了表示を更新し、正本整合を確認した。`fixed-and-verified`。

## Cycle 2以降のReviewer Verification

別コンテキストのLunaがAuthor修正後を再検証し、F02・F03・F04・F05を`fixed-and-verified`と判定した。F01は`reopened`である。Cycle 4の再検証でも同じ判定を確認した。詳細はCycle 2以降の検証記録を参照する。

- テスト: 47件成功
- 最新Cycle 4テスト: 49件成功
- Source Manifest検証: Observed
- Manifest経由Agent集計: 5 Agent／Run、`observed-with-unverified`
- pytest: 未導入のため未実行

## Candidate契約Probe

`candidate-contract-probe.json`で、Candidateの空Evidence入力を`expected=reject`として投入した結果、`actual=accept`を観測した。これは未検証ではなく、現行Candidateに対する再現可能な契約違反である。Candidate／Legacyの実体は変更していない。

## 独立性の制限

本レビューは実装と同一Codexセッションで実施しているため、Skill文書が要求するAI-1／AI-2の強い運用分離を満たさない。この記録は予備的な観点の成果であり、別コンテキストのLunaによるCycle 4検証を含めても、F01の人間裁定が完了するまで最終受入とはしない。

## 別コンテキストReviewerの確認

別コンテキストのLunaサブエージェント（`01a03f07-0a5b-79b3-9731-8cfb717f3605`）が読み取り専用で再レビューした。F01は観測違反として残り、F02〜F05は検証済みである。詳細は`cycles/cycle-01-independent-review.md`以降のCycle記録を参照する。

## Cycle 5 Human Adjudication

Ownerは選択肢A（条件付き受入）を選択した。QA-0008-F01は`risk-accepted`として受け入れるが、技術状態は`failed`、Reviewer判定は`fixed-and-verified`ではない。QA-0008は`closed / accepted-with-residual-risk`とする。compactの採用候補化は許可するが、本番配置、Legacy削除、commit、pushは別Changeと明示承認が必要である。裁定の正本は`cycles/cycle-05-adjudication.md`および`stage/evidence/human-adjudication.json`である。
