---
case_id: QA-0006
cycle: 1
action: author-response
role: implementer
base_revision: unverified-no-git
result_revision: unverified-no-git
---

# Author Response — Cycle 1

Reviewerのhandoffに基づき、F01〜F05は修正提出、F06は`deferred`として回答する。Reviewer正本は変更せず、検証とクローズをReviewerへ返却する。

## QA-0006-F01

- Disposition: `fix-submitted`
- 理由: `findings.yaml`を正本として読み、正本Finding集合・cycle・handoff digestを検証する経路を追加した。
- Evidence: `evidence/author-fix-cycle01.txt`
- 検証: Author 23件、Reviewer 34件が合格。

## QA-0006-F02

- Disposition: `fix-submitted`
- 理由: handoff全文のFinding ID正規表現抽出を廃止し、構造化`open_finding_ids`と正本Finding集合を照合する。
- Evidence: `evidence/author-fix-cycle01.txt`
- 検証: 本文中の未知IDが許可集合へ入らないnegativeテストを追加。

## QA-0006-F03

- Disposition: `fix-submitted`
- 理由: 公開CLIへ`--case-dir`、`--cycle`、`--save`を追加し、検証成功後にAuthor許可先へ回答とsubmissionを保存する。
- Evidence: `evidence/author-fix-cycle01.txt`
- 検証: CLI保存配線テストが合格。

## QA-0006-F04

- Disposition: `fix-submitted`
- 理由: submission保存にもAuthor Write Allowlist検査を適用し、Reviewer所有ファイルを拒否するFS境界テストを追加した。
- Evidence: `evidence/author-fix-cycle01.txt`

## QA-0006-F05

- Disposition: `fix-submitted`
- 理由: `file://` Evidenceを拒否する専用negativeテストを追加した。
- Evidence: `evidence/author-fix-cycle01.txt`

## QA-0006-F06

- Disposition: `deferred`
- 理由: 現行Reviewer共有コアの`compute_handoff_digests`がsemantic/contentへ同一値を返すため、Author Change単体で別契約へ変更しない。content/semanticの完全分離は共有基盤の別Changeで扱う。
- Evidence: `evidence/author-fix-cycle01.txt`
- 再判断条件: 共有コアでsemantic/content digestの別アルゴリズムとReviewer側の対応テストが承認・実装された時点。

## Reviewerへの返却

F01〜F05の修正提出とF06のdeferredをReviewer検証へ返却する。AuthorはFindingの`fixed-and-verified`、QAケースの`closed`、`review.md`、`findings.yaml`、`events.jsonl`を変更していない。
