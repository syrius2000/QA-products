---
document_type: spec-driven-qa-handoff
handoff_contract_version: "1.2"
case_id: QA-0006
generated_at: "2026-08-26T22:20:48+09:00"
source_revision: "unverified-no-git"
case_revision: 4
recipient_role: adjudicator
workflow: adjudication
status: adjudication-required
current_cycle: 3
implementation_permission: none
origin_role: reviewer
open_finding_ids:
  - QA-0006-F06
semantic_digest: pending-human-adjudication-f06
content_digest: pending-human-adjudication-f06
---

# QA Handoff — Human Adjudication

## 状況

自動cycle（3）完了。技術Finding F01–F05は`fixed-and-verified`。残オープンは **QA-0006-F06**（medium / deferred）のみ。

pytest最終確認: **59 passed**（`evidence/verification-cycle03-probes.txt`）。

## 裁定対象

### QA-0006-F06

content_digest と semantic_digest が共有コアで同一値のため、「内容だけ変更」シナリオを機械区別できない。Author/Reviewerとも本Change範囲では契約変更せず deferred。

```text
REQUIRED:HUMAN-ADJUDICATION:QA-0006-F06:CYCLE-3
```

### 選択肢

| 選択肢 | 結果イメージ |
|---|---|
| A. risk-accepted | 残余を明示して条件付きクローズ（metadata必須） |
| B. 保留 | 共有基盤Changeまでケース維持 |
| C. 追加修正許可 | 共有コア分離を前提に再オープン |

## 参照

- `cycles/cycle-03-verification.md`
- `findings.yaml`（F06）
- `review.md`
