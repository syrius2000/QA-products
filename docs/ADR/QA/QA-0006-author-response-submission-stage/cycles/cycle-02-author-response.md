---
case_id: QA-0006
cycle: 2
action: author-response
role: implementer
base_revision: unverified-no-git
result_revision: unverified-no-git
---

# Author Response — Cycle 2

ReviewerのCycle 1検証結果を受け、F01の残差を修正提出する。F06は共有基盤の契約分離待ちとして`deferred`を維持する。Reviewer正本は変更しない。

## QA-0006-F01

- Disposition: `fix-submitted`
- 修正: `canonical_case_dir`を必須検証経路とし、省略APIを拒否する。`validate_and_save`もcase_dirを正本として再検証する。
- 修正: Finding集合はcanonical `findings.yaml`から取得し、handoffの構造化IDと照合する。
- Evidence: `evidence/author-fix-cycle02.txt`
- 検証: 58件のAuthor／Reviewer回帰テストが合格。

## QA-0006-F06

- Disposition: `deferred`
- 理由: semantic/content digestの同一値はReviewer共有コア側の契約であり、Author Change単体で変更すると共有契約を壊すため。
- 残余リスク: content-only変更を自動的に区別できない。
- 再判断条件: 共有コアでdigest分離とReviewer側テストが承認・実装された時点。
- Evidence: `evidence/author-fix-cycle02.txt`

## Reviewerへの返却

F01の修正提出とF06のdeferredをReviewer verificationへ返却する。AuthorはFinding状態、verification、review、events、closureを変更していない。
