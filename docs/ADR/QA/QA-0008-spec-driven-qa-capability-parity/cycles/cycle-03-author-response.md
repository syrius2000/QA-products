# QA-0008 Cycle 3 Author Response

created: 2026-08-27 04:35 (JST)
update: 2026-08-27 04:35 (JST)
author: Codex (GPT-5)

## 提出情報

- ケースID: QA-0008
- サイクル: 3
- 行動: author-response
- agent_id: `codex-author-20260827-qa0008`
- 役割: implementer
- 対応方針: 自動修正サイクルを停止し、人間裁定へ移行
- QAケースのクローズ: 実施しない

## Finding別回答

### QA-0008-F01

- Disposition: `deferred`
- 技術状態: Candidateの空Evidence受理を専用Probeで観測済み（`expected=reject`、`actual=accept`）
- 対応: Candidate／Legacyを改造せず、`candidate-contract-probe.json`へ結果を固定した
- 人間判断: Candidate validatorを別Changeで修正するか、compactとの意図的非互換として裁定するか

### QA-0008-F02

- Disposition: `deferred`
- 技術状態: Candidateのstale semantic digest、content digest、digest version回帰の適用範囲が未確定
- 対応: `contract-applicability.json`へ`evidence-gap`／`not-applicable`として分離した
- 人間判断: Candidateの適用可能契約だけを追加検証するか、compact固有契約として裁定するか

## 返却条件

F01／F02はReviewerが検証可能な修正または人間の明示裁定を受けるまで、`fixed-and-verified`、`accepted`、`closed`へ変更しない。
