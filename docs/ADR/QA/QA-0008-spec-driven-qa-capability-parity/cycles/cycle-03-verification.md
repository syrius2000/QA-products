# QA-0008 Cycle 3 Candidate契約Probe検証

created: 2026-08-27 04:20 (JST)
update: 2026-08-27 04:20 (JST)
author: Lunaサブエージェント

## 検証情報

- ケースID: QA-0008
- サイクル: 3
- 行動: reviewer-verification
- agent_id: `01a03f07-0a5b-79b3-9731-8cfb717f3605`
- 役割: reviewer
- 実行方式: Codexから分離した別コンテキストのLuna
- 対象: Candidateの空Evidence契約ProbeとQA-0008残存Finding

## 実行結果

- `python3 -B -m unittest discover -s stage/tests -p 'test_*.py'`: 48件成功
- Candidate Probe: `expected=reject`、`actual=accept`、`status=observed-violation`
- Source Manifest検証: `observed`
- Manifest経由Agent集計: `observed-with-unverified`、5 Agent／Run、エラー0件

## Finding判定

- QA-0008-F01: `reopened`。Candidate validatorが空Evidenceを受理する再現可能な契約違反であり、Candidate修正または人間裁定が必要。
- QA-0008-F02: `adjudication-required`。Candidate digest回帰範囲の不足が残る。
- QA-0008-F03: `fixed-and-verified`。必須項目のnull・空値・欠測語判定と再集計を確認。
- QA-0008-F04: `fixed-and-verified`。Source ManifestのSHA-256、追加・削除・改変・秘密値検証と再集計を確認。
- QA-0008-F05: `fixed-and-verified`。5.1／5.2の未完了表示とEvidence gapの整合を確認。

## 残存タスクと判断

- 5.1: Candidateの空Evidence受理を修正または明示裁定するまで未完了。
- 5.2: Candidate digest回帰が未完了。
- 6.1: 全Agent／Runの必須項目完全充足が未確認。
- 7.5: F01／F02の裁定と配備前確認が未完了。

compactの無条件採用は不可。Candidateの不備をLegacyへ遡及せず、compact単体の安全性と差分を人間裁定へ送る。
