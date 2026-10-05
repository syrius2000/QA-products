# Git branch・worktree整理計画

created: 2026-10-05 04:48 (JST)
update: 2026-10-05 04:48 (JST)
author: Codex (GPT-6)

## 目的

QA-productsで並行しているbranchとworktreeを、未コミット変更・未push commit・QA記録を失わず整理する。QA-003の独立レビューが完了するまでは、その対象と結果回収経路を維持する。

## 現状

| worktree | branch / HEAD | 状態 | 扱い |
|---|---|---|---|
| リポジトリ本体 | `master` / `ad6ca1e` | origin/masterより3 commit先行。staged 1、unstaged 148、untracked 12 | 既存差分を保持。clean/reset/restoreしない |
| `qa-skill-integration/QA-products` | `codex/qa-skill-integration` / `ad6ca1e` | upstreamなし。staged 1、unstaged 8、untracked 20 | 既存差分を保持し、内容の持ち主を確認する |
| `qa-skill-integration-cloud-qa` | `codex/qa-skill-integration-cloud-qa` / `928ef88` | QA-001状態JSONがuntracked。remoteの同名branchは`2492819`でlocalより1 commit先行。local upstreamは誤って`origin/master` | 古いQA結果を保全し、upstreamと目的を確認する |
| `qa-loop-implementation/QA-products` | `codex/unify-qa-skill-workflow` / `418dcb9` | origin同名branchの`d6f8462`と1 commitずつ分岐。local commitはQA-001/002の下書き・状態を含み、QA-003依頼書自体はremote版と同一 | QA-003レビュー中はworktreeを維持。余分なcommitを公開しない |

## 整理方針

1. QA-003の独立レビュー結果を取得し、対象SHA `d9bad5c125791306e38bca8830b4082f7f38fc6b` と一致することを確認する。
2. primary `master` と `codex/qa-skill-integration` の差分をpath単位で照合し、重複・固有変更・削除予定を人が分類する。分類前に統合・退避・削除しない。
3. cloud QA-001 branchはlocal/remoteの履歴とレビュー成果物を保全したまま、追跡先の修正可否を決める。QA-001記録をQA-003へ混ぜない。
4. QA-003 branchはremote先端を正とするか、local追加commitを別保存するかを決めてから分岐を解消する。force-push、reset、commit改変は行わない。
5. 保持対象がなくなったworktreeだけをアーカイブし、branch削除は各worktreeの差分・未push commit・remote参照がないことを確認してから別途行う。

## 実行順と確認

- 読み取り専用のpath別差分・commit ancestry・remote参照一覧を作る。
- primaryとQA integrationのpath分類、および各未追跡ファイルの由来を確認する。
- QA-003独立レビュー終了後、対象branchの採用履歴と不要worktreeを明示してから保全・統合する。
- 最後に`git worktree list --porcelain`、`git branch -avv`、全worktreeの`git status --short --branch`、remote tipを再確認する。

## 承認境界

この計画の作成と現状棚卸しは読み取り専用で実施した。承認後も、path分類・対象範囲を越えるreset、force-push、既存差分の破棄、branch削除は行わない。既存の未コミット変更やローカル固有commitを統合・アーカイブ・削除する段階では、対象一覧を示して個別に確認する。

## 未確認事項

- primaryと`codex/qa-skill-integration`にある未コミット変更の所有者・最終目的
- QA-001レビュー成果物を今後参照する必要性
- QA-003のlocal-only追加commitに含まれるQA-001/002下書き・状態ファイルの保持期間
- どのworktreeを最終的なQA-products開発checkoutとして残すか
