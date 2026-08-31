# リポジトリルート文書整理・公開Git履歴クリーンアップ計画

created: 2026-08-31 19:55 (JST)
update: 2026-08-31 20:20 (JST)
author: Codex (GPT-5)

## 1. 目的

リポジトリルートの文書をREADMEとAGENTSに集約し、利用者が最初に読む情報とAI作業時の必須規則を最小化する。過去の設計・実装・QA経過はArchiveへ分類して保存し、不要な個人用・一時用資料は削除する。

## 2. 合意済みの設計判断

- ルートには原則として`README.md`と`AGENTS.md`だけを残す。
- `docs/Archives/README.md`を履歴資料の入口とする。
- Quality Loop、spec-driven-qa、QA、設計、その他、temporaryを分類する。
- `Codex.md`、`GPT-findings.md`、Gemini設計資料、`make-size-compact.md`、`test-prompt.md`、`test-prompt-2.md`は内容を保存してArchiveへ移す。
- `memo-ghostty.md`、`NEXT_ACTION_PLAN.md`、`NEXT_SESSION_MEMO.md`は破棄する。
- `garmin_live.ics`はGit未追跡・ignore対象のため、ファイルシステムから破棄する。
- Gemini設計資料は`docs/Archives/spec-driven-qa/design/Gemini-Flash.md`へrenameする。
- 誤記されたGemini名は、公開文書・公開Git履歴で`Gemini-Flash`へ訂正する。
- Quality Loopの実装、QA結果、実装経過は公開Git履歴に残す。

## 3. 添付Skillの扱い

`grilling`および`grill-with-docs`による設計対話を実施し、Archive構成、正本、削除対象、履歴保持範囲をユーザーと合意した。添付Skillの指示は設計整理の方法として扱い、リポジトリの承認境界、既存変更保護、外部pushの安全条件を上書きしない。

## 4. 変更対象

### 4.1 新規作成・更新

- `docs/Archives/README.md`
- `docs/Archives/spec-driven-qa/design/Gemini-Flash.md`
- Archive内の分類先へ移動する各履歴資料
- `README.md`（100行以内を目安に再構成）
- `AGENTS.md`（50〜70行程度の実務ルールへ整理）
- 必要に応じたArchive方針ADRと用語整理`CONTEXT.md`

### 4.2 移動・renameする資料

- `Codex.md` → `docs/Archives/spec-driven-qa/design/Codex.md`
- `GPT-findings.md` → `docs/Archives/spec-driven-qa/design/GPT-findings.md`
- Gemini設計資料 → `docs/Archives/spec-driven-qa/design/Gemini-Flash.md`
- `make-size-compact.md` → `docs/Archives/spec-driven-qa/compact/make-size-compact.md`
- `test-prompt.md`、`test-prompt-2.md` → `docs/Archives/spec-driven-qa/qa/`

既存の`docs/Archives/archived_summary_*.md`とQA受入サマリーは、Quality Loop履歴として現行の分類方針から辿れるようにする。既存原本ZIP・tarballは`archives/quality-loop/`から移動・削除しない。

### 4.3 破棄する資料

- `memo-ghostty.md`
- `NEXT_ACTION_PLAN.md`
- `NEXT_SESSION_MEMO.md`
- `garmin_live.ics`

前三者はGit履歴からも除去する。`garmin_live.ics`はGit履歴に存在しないため、ファイルシステム上の削除だけを行う。`memo-ghostty.md`には現在未コミット変更があるため、その変更も破棄対象である。

## 5. Git履歴rewriteとforce push

### 5.1 対象

公開プロジェクト参照である`refs/heads/master`と`refs/remotes/origin/master`を対象に、次を行う。

- 破棄対象3 Markdownを全履歴から除去する。
- Gemini設計資料のファイル履歴をArchive上の`Gemini-Flash.md`へrenameする。
- 公開文書内の誤記されたGemini名を`Gemini-Flash`へ置換する。

Codexアプリ管理と考えられる`refs/codex/turn-diffs/...`は変更しない。Gitオブジェクト、reflog、他clone、GitHubキャッシュからの絶対的な消去は保証しない。

### 5.2 安全手順

1. 作業ツリー、branch、remote、refs、対象ファイルの追跡状態を記録する。
2. `/private/tmp`にrewrite前の復元用Git bundleを作成する。
3. bundleの存在、サイズ、checksum、復元可能性を確認する。
4. 文書の移動・更新・削除を反映した作業状態を作る。
5. 履歴rewrite後、公開参照から破棄対象Markdownの履歴が消え、誤記されたGemini名が残っていないことを確認する。
6. `master`へ`--force-with-lease`でpushする。
7. `master`と`origin/master`の同期、現行ファイル、Archive、リンクを確認する。
8. 全検証成功後、復元用bundleを`/private/tmp`から削除する。

履歴rewriteツールの実行前に、利用可能な公式・標準的手段と、未コミット変更を巻き込まない適用方法を確認する。対象を誤認した場合は停止し、bundleから復元する。

## 6. README/AGENTSの正本関係

- `README.md`: 人間・初回利用者・Reviewer・Owner向けの入口。目的、利用、現行Quality Loop、Archive入口、承認境界を記載する。
- `AGENTS.md`: AIが常時守る承認、差分保護、Artifact、QA、Git操作の規則を記載する。
- `quality-loop/README.md`と`FUNCTIONAL_SPEC.md`: 現行Quality Loopの利用・仕様の正本とする。
- `docs/Archives/README.md`: 過去の設計・実装・QA・一時資料の分類と経緯の入口とする。
- Archive内の本文は作成時点の履歴として保存し、現行状態の説明で上書きしない。

## 7. 受入条件

- ルート直下の文書はREADME.mdとAGENTS.mdだけである。
- Archive READMEから全保存資料へ相対リンクで到達できる。
- Gemini設計資料は現行ツリーと公開Git履歴で`Gemini-Flash.md`へrenameされている。
- 破棄対象3 Markdownは公開Git履歴から除去されている。
- `garmin_live.ics`はファイルシステムから存在しない。
- READMEとAGENTSが簡潔で、現行Quality LoopとArchiveの正本関係を説明している。
- Quality Loop実装、テスト、Schema、案件正本、既存QA記録を意図せず変更していない。
- rewrite前bundle、force push結果、同期状態、最終リンク検証のEvidenceが残る。
- 作業後に未コミット差分が残る場合は、今回の変更と既存ユーザー変更を区別して報告する。自動commitは行わない。

## 8. 承認境界

本計画の作成と設計対話は完了したが、文書移動、削除、履歴rewrite、force pushは本計画の明示的な承認後に開始する。`force push`は、別途その実行を明示承認する。

## 9. 追加承認による対象拡張

2026-08-31にユーザーから追加承認を受け、次を本計画へ追加する。

- `.gitignore`をルート限定の`/.agents/`へ訂正する。
- Git管理済みのリポジトリルート`.agents/`（OpenSpec用10ファイル）を現行ツリーから削除する。
- `.agents/`を公開Git履歴から除去する。
- OpenSpecは将来、必要な環境で`openspec init`により再生成する方針とする。

この追加は、外部Skill配置の削除ではなく、本リポジトリ内の補助Skill資産とその履歴の削除である。OpenSpec本体の履歴、Quality Loopの実装・QA履歴、その他のArchiveは保持する。追加範囲を含むPlan 018の実行および`origin/master`へのforce pushについて、ユーザーの明示承認を得ている。

## 10. 実施・検証完了記録

2026-08-31に承認済み範囲を実施した。

- ルート文書をArchiveへ分類し、`README.md`と`AGENTS.md`を現行入口・AI作業規則として整理した。
- `docs/Archives/README.md`とArchive方針ADRを作成した。
- Gemini設計資料を`Gemini-Flash.md`へrenameし、公開文書の旧表記と参照を訂正した。
- `memo-ghostty.md`、`NEXT_ACTION_PLAN.md`、`NEXT_SESSION_MEMO.md`、`.agents/`を現行ツリーから削除した。
- `.gitignore`をルート限定の`/.agents/`へ訂正した。
- `master`と`origin/master`の公開履歴から、破棄対象3 Markdownと`.agents/`を除去し、Gemini設計資料のrenameを反映した。
- rewrite前の復元用bundleを作成・検証し、検証完了後に一時退避を削除した。

最終確認:

- `master`と`origin/master`は`e73123d`で一致。
- ルート直下の文書は`README.md`と`AGENTS.md`のみである（`.gitignore`を除く）。
- 公開参照に破棄対象パスおよび旧Gemini表記は存在しない。
- `Gemini-Flash.md`、Archive README、方針ADR、Quality Loop資料は保持されている。
- Archive内の相対リンク検査と`git diff --check`は成功した。
- Codex内部参照、Quality Loop実装、QA正本、外部配置は変更していない。
