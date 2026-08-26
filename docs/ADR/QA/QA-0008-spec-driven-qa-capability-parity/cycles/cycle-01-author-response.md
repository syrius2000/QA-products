# QA-0008 Cycle 1 Author Response

created: 2026-08-27 02:55 (JST)
update: 2026-08-27 02:55 (JST)
author: Codex (GPT-5)

## 提出情報

- ケースID: QA-0008
- サイクル: 1
- 行動: author-response
- agent_id: `codex-author-20260827-qa0008`
- 役割: implementer
- base revision: `unverified-no-git`
- result revision: `unverified-no-git`
- QAケースのクローズ: 実施しない

## Finding別回答

### QA-0008-F01

- Disposition: `deferred`
- 理由: Candidateの空または欠落Evidence拒否は未検証であり、Candidate旧契約を改造してcompact契約へ合わせる判断は人間裁定が必要である。
- 提出内容: `contract-applicability.json`へ`evidence-gap`として固定した。
- 次の検証: Candidateの既存仕様を確認した上で、追加回帰または意図的非互換の裁定を行う。

### QA-0008-F02

- Disposition: `deferred`
- 理由: Candidateにcontent digest／digest version契約が存在するかを先に確定する必要があり、compactの契約をLegacy／Candidateへ遡及適用しない。
- 提出内容: Candidateのstale semantic digest不足を`evidence-gap`、content digest／version不在を`not-applicable`として固定した。
- 次の検証: Candidateの適用可能なdigestだけを追加実測するか、意図的非互換として裁定する。

### QA-0008-F03

- Disposition: `fix-submitted`
- 理由: Agent／Runを分離集計する既存機能に加え、必須項目ごとの`observed`／`unverified`を集計するよう修正した。
- 変更: `stage/agent_aggregator.py`、`stage/tests/test_agent_aggregator.py`
- Evidence: `stage/evidence/agent-aggregate.json`
- 検証: 標準ライブラリテスト43件成功。

### QA-0008-F04

- Disposition: `fix-submitted`
- 理由: 元Evidenceをコピー・改変せず、アーカイブ参照をハッシュ固定するSource Manifestと再検証経路を追加した。
- 変更: `stage/agent_source_manifest.py`、`stage/evidence/agents/README.md`、`stage/agent_aggregator.py`
- Evidence: `stage/evidence/agents/source-manifest.json`、`stage/evidence/agent-aggregate.json`
- 検証: Source Manifest作成・ハッシュ検証・Manifest経由の再集計が成功した。
- 注記: 元Evidenceの実体はアーカイブ側に残し、現Changeへ秘密値をコピーしていない。

### QA-0008-F05

- Disposition: `fix-submitted`
- 理由: 独立QAの指摘に従い、5.1／5.2の完了チェックを未完了へ戻し、Evidence gapが残ることを明記した。
- 変更: `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/tasks.md`
- Evidence: `stage/evidence/contract-applicability.json`
- 検証: OpenSpec validationはvalid。QA Reviewerによる再検証待ち。

## 残余リスク

- F01／F02は人間裁定まで未解決である。
- F03は必須項目が不均一な元Runを含むため、全Run完全充足ではない。
- F04はSource Manifestにより再現経路を追加したが、元Evidenceはアーカイブ参照であり、現Changeへの実体コピーではない。
- Token・Latency・動的正答率は`unverified`である。
