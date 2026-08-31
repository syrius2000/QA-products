# OpenSpec移行期資料 統合アーカイブ要約

created: 2026-08-28 18:49 (JST)
update: 2026-08-28 18:49 (JST)
author: Codex (GPT-5)

## 対象期間

2026-08-25 〜 2026-08-27

## アーカイブの目的

本書は、旧`spec-driven-qa` 2 Skillの圧縮、Contract v1.2、OpenSpec Change、Legacy比較を扱った完了済み計画を一冊に集約した記録である。現行の正本は人間中心の`quality-loop/`であり、旧OpenSpec契約は実行時依存ではない。

## アーカイブ元

- `external_ai_comparison_execution_prompt_001_0826.md`
- `implementation_plan_005_0825.md`
- `implementation_plan_006_0826.md`
- `implementation_plan_007_0826.md`
- `implementation_plan_008_0827.md`
- `implementation_plan_009_0827.md`
- `implementation_plan_010_0827.md`

## 経緯と成果

### 1. コンパクト化と共有コア

旧Reviewer／Author Skillの機能台帳、サイズ計測、比較fixtureを整備し、共有コアと二つの役割入口を持つ候補を検証した。役割分離、handoff、状態遷移、Evidence、失敗時停止を維持しながら、配布物を縮小する方針を定めた。

### 2. Contract v1.2の安全境界

Authorの自己クローズ禁止、未知Finding拒否、digestとrevisionの鮮度確認、Reviewerの独立検証、Owner裁定を契約化した。semantic/content digestの同値問題は後続Changeで分離し、旧形式の受理を拒否する検証を追加した。

### 3. 外部AI比較とEvidence

複数AIの結果は`agent_id`と`run_id`単位で隔離し、静的検証と動的AI実行を混同しない運用を定めた。比較結果、Token、Latencyは、実測できない環境では`unverified`として扱う原則を固定した。

### 4. Legacy互換性の判定

旧130ファイル由来の公開機能を対応表で確認したが、Legacyの挙動を安全契約より優先しない方針を採った。互換不能または未観測の差分は、合格とせず`intentional-noncompatibility`または`evidence-gap`として記録した。

## 現行方針への継承

次の考え方は現行Quality Loopへ継承されている。

- ReviewerがFindingを作り、Implementerが回答・修正を提出し、別InvocationのReviewerが検証し、Ownerが裁定する。
- Finding、Evidence、状態遷移を正本とし、品質要求を恣意的に上下させない。
- 実測できない事項を成功扱いにしない。
- 外部配備、旧版削除、commit、pushは明示承認を必要とする。

一方、OpenSpec Change、旧Bundle、Contract v1.2のdigest形式、Legacy完全互換性は、`quality-loop/`初期版の実行要件ではない。必要な知見だけを参照し、旧実装をそのまま再利用しない。

## 参照先

- 人間中心Quality Loopの実装履歴: [archived_summary_003_0831.md](archived_summary_003_0831.md)
- v1.4.0最終独立QA: [qa_acceptance_summary_001_0831.md](qa_acceptance_summary_001_0831.md)
