# Author Response — Cycle 3

- case_id: `QA-0006`
- cycle: 3
- submission_id: `submission-qa0006-cycle03-codex`
- base_revision: `unverified-no-git`
- result_revision: `unverified-no-git`
- next_action: `reviewer-verification` または必要に応じて人間によるadjudication

## QA-0006-F01

- Disposition: `fix-submitted`
- Justification: ReviewerとAuthorのdigest入力集合を一致させるため、正本`findings.yaml`から`status: open`のFinding IDだけを抽出するよう`canonical_finding_ids`を修正した。これにより、`fixed-and-verified`等のclosed Findingが正本に混在していても、Reviewerが生成したopen-only handoff digestをAuthor側がstaleとして誤拒否しない。
- Modified files:
  - `openspec/changes/spec-driven-qa-author-response-submission/stage/spec_driven_qa_author_response_submission/submission.py`
  - `openspec/changes/spec-driven-qa-author-response-submission/stage/tests/test_submission.py`
- Evidence: `../evidence/author-fix-cycle03.txt`
- 再現手順: Author/Reviewerのstage testsをcache-freeで実行し、59件合格を確認する。追加テストは`test_closed_canonical_findings_are_excluded_from_reviewer_digest`。

## QA-0006-F06

- Disposition: `deferred`
- Justification: `semantic_digest`と`content_digest`の意味分離は共有コアの契約変更を伴うため、本ChangeのAuthor提出機能の範囲外である。現状は同値契約に依存する`evidence-gap`を残し、共有コア分離またはdigest契約変更のChangeで再評価する。今回、AuthorがQAケースをclosedまたはfixed-and-verifiedへ変更することはしない。
- 再判断条件: 共有コアのsemantic/content digest分離Changeの実装後、Reviewerによる独立再検証を実施する。
- Evidence: `../evidence/author-fix-cycle03.txt`

## 検証結果と境界

- Stage回帰テスト: `59 passed in 0.25s`
- OpenSpec validation: `valid: true`（1 passed, 0 failed）
- Reviewer正本の更新、QAケースの終端判定、`fixed-and-verified`への変更は行っていない。
- 次担当: ReviewerがF01の修正を独立検証し、F06を含む残余リスクの扱いを必要に応じてadjudicationへ送る。
