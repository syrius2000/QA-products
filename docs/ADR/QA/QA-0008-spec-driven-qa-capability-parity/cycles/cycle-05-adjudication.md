# QA-0008 人間裁定記録（Cycle 5）

- case_id: `QA-0008`
- cycle: 5
- 裁定者: `human-owner`
- 裁定日時: `2026-08-27 05:20 JST`
- 選択肢: `A 条件付き受入`
- 裁定結果: `accepted-with-residual-risk`
- ケース状態: `closed`

## 裁定

QA-0008-F01について、Candidateが空Evidenceを受理する観測違反は技術的に解消されていない。ただし、これはアーカイブ済みCandidate固有の差分であり、Legacyを変更せずcompactの採用候補を判断する本Changeの目的に照らして、Ownerの残余リスク受入とする。F01の技術判定は`failed`のまま保持し、`fixed-and-verified`へ変更しない。

QA-0008全体を`closed / accepted-with-residual-risk`とする。compactの安全境界とサイズは採用候補の根拠として使用できるが、Legacy完全互換や無条件の安全性を宣言しない。

## 条件

- compactを本番候補とし、Candidateを本番フォールバックとして使用しない。
- compactの`empty-or-missing-evidence`は`not-applicable`であり、安全契約の合格証拠とは扱わない。
- Token、Latency、外部LLM正答率、Agent／Run必須項目の欠測は`unverified`または`evidence-gap`のまま保持する。
- 外部Skill配置、Legacy削除、commit、pushは別Changeでbackup、dry-run、配置後検証、rollback、明示承認を完了するまで行わない。

## 参照Evidence

- `../../../../../openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/stage/evidence/human-adjudication.json`
- `../../../../../openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/stage/evidence/overall-report.json`
- `../handoff.md`
