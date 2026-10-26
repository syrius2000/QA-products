# pr-openspec 関連文書のアーカイブおよびブランチ整理計画

created: 2026-10-26 09:55 (JST)
update: 2026-10-26 09:55 (JST)
author: Antigravity (Gemini 2.5 Flash)

## 1. 目的と概要

`docs/Artifacts/` にある PR向けOpenSpec監査スキル（`pr-openspec`）の計画書および独立レビュー記録群（計9ファイル）は、PR #11（commit `4653d60`）および PR #13（commit `94e043c`）により `main` へ反映され、実装・レビュー・記録整理がすべて完了している。
本計画は、スキル `artifacts-archiver` の手順に基づき、これらの文書を `docs/Archives/qa_workflow/pr-openspec/` へ退避・集約（まとめ文書 `archived_summary_009_1026.md` 作成）した上でコミットし、ユーザーの指示に沿ってリモートへの Push およびブランチ整理（不要なリモートブランチの削除と prune）を実施するための計画書である。

---

## 2. 対象一覧 (Inventory)

`artifacts-archiver` 規約に基づく 7 列の対象一覧は以下の通り。全 9 ファイルが完了済みであり、アーカイブ対象とする。

| パス | 状態 | 候補/除外 | 根拠 | リンク確認 | 復元情報 | 必要な承認 |
|---|---|---|---|---|---|---|
| `docs/Artifacts/implementation_plan_001_1025.md` | 完了 (PR #11) | 候補 | OpenSpec Change `add-pr-openspec-skill` として実装完了・マージ済。 | 関連レビュー 001〜003 から参照あり。移動先で相対リンクを維持。 | コミット `72b21e8` で Git 追跡済み。アーカイブ先および Git 履歴から復元可能。 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_001_1025.md` | 完了 (PASS) | 候補 | 計画書初版のレビュー記録。指摘 R1〜R4 解消確認済。 | `implementation_plan_001_1025.md` を相対参照。 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_002_1025.md` | 完了 (PASS) | 候補 | 計画書第 2 版のレビュー記録。別意見 6 項目反映済。 | 同上 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_003_1025.md` | 完了 (PASS) | 候補 | 計画書第 3 版のレビュー記録。QL ケース `add-pr-openspec-skill-review`。 | 同上 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_004_1025.md` | 完了 (PASS) | 候補 | OpenSpec Change 第 4 版 (`b3a4848`) のレビュー記録。 | `openspec/changes/add-pr-openspec-skill/` を参照。 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_005_1025.md` | 完了 (PASS) | 候補 | 第 5 版計画 (`2c344b4`) のレビュー記録。 | 同上 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_006_1025.md` | 完了 (PASS) | 候補 | 第 6 版・実装 (`67f8c8f`) のレビュー記録。 | 同上 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_007_1025.md` | 完了 (PASS) | 候補 | 第 7 版 (`9e1edd5`) の範囲限定再レビュー記録。 | `006_1025.md` を参照。 | 同上 | 本計画書での明示承認 |
| `docs/Artifacts/pr_openspec_plan_review_008_1025.md` | 完了 (PASS) | 候補 | 第 8 版 (`05cfae4`) の範囲限定再レビュー記録。 | `7486903..05cfae4` を参照。 | 同上 | 本計画書での明示承認 |

※ 本計画書 `docs/Artifacts/implementation_plan_002_1026.md` 自体は、アーカイブ実行および完了確認が終わるまでアクティブな文書として保持する。

---

## 3. 変更計画と成果物

### 3.1 作成・移動・更新するファイル
1. **まとめ文書の作成**:
   - パス: `docs/Archives/qa_workflow/pr-openspec/archived_summary_009_1026.md`
   - 構成: 対象期間（2026-10-25 〜 2026-10-26）、対象と結論、確定した決定と理由、主要成果と検証の限界、未解決事項と引継ぎ、元文書と復元情報（各ファイルの元パス、退避先、SHA-256、復元方法）。
2. **元ファイルの退避**:
   - 退避先ディレクトリ: `docs/Archives/qa_workflow/pr-openspec/artifacts/`
   - 上記 9 ファイルを `docs/Artifacts/` から退避先へ `git mv` 移動。
3. **案内目録の更新**:
   - `docs/Archives/README.md` に `archived_summary_009_1026.md` の概要とリンクを追記。

---

## 4. Git 操作手順

ユーザーからの指示「まず文書をアーカイブしてローカルコミット。そしてPushした後、リモート、ローカルのブランチ整理」に基づき、以下の手順で実施する。

### 手順 A: アーカイブとローカルコミット
1. `git mv` により 9 ファイルを `docs/Archives/qa_workflow/pr-openspec/artifacts/` へ移動。
2. まとめ文書 `docs/Archives/qa_workflow/pr-openspec/archived_summary_009_1026.md` を新規作成。
3. `docs/Archives/README.md` を更新。
4. Markdown 相対リンクおよび `git diff --check` を検証。
5. コミットを作成:
   ```bash
   git add docs/Archives docs/Artifacts
   git commit -m "docs(archives): pr-openspec の計画・レビュー記録をアーカイブ（summary 009）"
   ```

### 手順 B: リモートへの Push
現在 `main` ブランチはローカルコミット `72b21e8`（"ClaudeでのPR経験"）を含み `ahead 1` の状態であるため、アーカイブコミットを含めて `main` をリモートへ Push する。
```bash
git push origin main
```

### 手順 C: リモートブランチ削除と prune
ユーザー指定の 5 ブランチについて、すべて `origin/main` にマージ済みであることを確認済み。
```bash
git push origin --delete chore/archive-add-in-agent-review-controls docs/pr-openspec-records feat/in-agent-review-controls feat/pr-openspec-skill fix/pr-openspec-consistency
git fetch --prune
```

---

## 5. テスト・検証計画

| 検証項目 | 確認方法 | 期待結果 |
|---|---|---|
| **移動元・先の整合性** | `git status -s` | 9 ファイルがすべて `R` (Rename) として認識され、想定外の変更がないこと。 |
| **空白・構文検査** | `git diff --check` | 空白エラーや構文不備が出力されないこと。 |
| **相対リンク検査** | まとめ文書内リンク確認 | まとめ文書から各退避ファイル、および `README.md` への相対リンクが正しく解決すること。 |
| **ブランチ削除の確認** | `git branch -a` | 指定した 5 つのリモートブランチが完全に消去され、`main` のみとなること。 |

---

## 6. 完了条件

1. `docs/Artifacts/` から完了済み 9 ファイルが移動され、まとめ文書 `archived_summary_009_1026.md` が作成されていること。
2. ローカルコミットが作成され、`origin/main` へ正常に Push されていること。
3. 指定された 5 つのリモートブランチが削除され、`git fetch --prune` により追跡ブランチが整理されていること。
