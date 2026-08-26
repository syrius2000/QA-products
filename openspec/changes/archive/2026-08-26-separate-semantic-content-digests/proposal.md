# semantic digest分離契約の導入

created: 2026-08-26 22:25 (JST)
update: 2026-08-26 22:25 (JST)
author: Codex (GPT-5)

## Why

現在の共有コアでは`semantic_digest`と`content_digest`が同じ値になるため、正本の意味構造を変えず本文だけを変更したケースを機械的に区別できない。QA-0006ではこの制約を残余リスクとして保留したため、共有基盤の契約を明確化し、AuthorとReviewerが内容変更を正しく検出できるようにする。

## What Changes

- 意味構造を表す`semantic_digest`と、文書内容を表す`content_digest`を異なる入力から決定的に算出する。
- Reviewerのhandoff生成とAuthorの提出検証で、両digestを同一契約に基づいて照合する。
- 意味変更、内容だけの変更、未変更、改ざん・古いhandoffを区別するテストを追加する。
- 旧形式の同値digestを受け取った場合の互換性・移行判定を明記する。

## Capabilities

### New Capabilities

### Modified Capabilities

- `openspec/specs/spec-driven-qa`: semantic digestとcontent digestの意味分離、およびhandoff鮮度判定の要件を変更する。

## Impact

- Reviewer lifecycleのhandoff digest生成とAuthor response submission検証。
- 共有コアのdigest実装、fixture、Reviewer/Authorの相互運用テスト。
- 既存の同値digestを前提とするstaging Evidenceは再評価が必要となる。
- 外部Skill配置、旧版削除、commit、pushは本Changeの範囲に含めない。
