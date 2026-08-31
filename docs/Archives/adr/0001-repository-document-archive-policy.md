# ADR-0001: リポジトリルート文書と履歴資料の分離

created: 2026-08-31 19:55 (JST)
update: 2026-08-31 19:55 (JST)
author: Codex (GPT-5)

## 状態

Accepted（2026-08-31、ユーザー合意）

## Context

ルート直下に、現行利用の入口、Quality Loopの実装履歴、旧spec-driven-qaの設計資料、QAプロンプト、一時メモ、個人用設定メモが混在していた。これにより、初回利用者が読むべき正本と、過去の経緯・破棄対象を区別しにくかった。

## Decision

- ルートの利用入口は`README.md`、AI作業規則は`AGENTS.md`に限定する。
- 過去の設計・実装・QA資料は`docs/Archives/`配下に分類する。
- `README.md`は目的、最小利用手順、現行成果物、Archiveへの導線に限定する。
- `AGENTS.md`は承認境界、既存変更保護、QAとOwner裁定の分離、Git操作規則に限定する。
- Quality Loopの実装・QA経過は履歴として保持する。
- 個人用または一時用の`memo-ghostty.md`、`NEXT_ACTION_PLAN.md`、`NEXT_SESSION_MEMO.md`は破棄する。
- 誤記されたGemini設計資料のファイル名は、正しい名称`Gemini-Flash.md`へ全公開履歴でrenameする。

## Consequences

初回利用時の探索範囲が小さくなり、現行正本と履歴資料を混同しにくくなる。一方、過去資料を読むにはArchive READMEを経由する必要がある。また、不要資料の全履歴除去とrenameにより、公開コミットIDは変更され、既存cloneには再同期が必要になる。

## Boundary

この判断は外部Skill配置、Quality Loop仕様の変更、QA結果の改変を意味しない。公開Git履歴のrewriteは`master`と`origin/master`に限定し、Codex内部参照は変更しない。reflog、Gitオブジェクト、他clone、GitHubキャッシュからの絶対的な消去は保証しない。
