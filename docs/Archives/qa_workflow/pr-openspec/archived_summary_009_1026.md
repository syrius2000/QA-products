# PR向けOpenSpec監査スキル（pr-openspec）関連文書のアーカイブ記録

created: 2026-10-26 09:58 (JST)
update: 2026-10-26 09:58 (JST)
author: Antigravity (Gemini 2.5 Flash)

## 対象期間と結論

対象期間: 2026-10-25 〜 2026-10-26

`docs/Artifacts/` に置かれていた PR向けOpenSpec監査スキル（`pr-openspec`）の作成計画および独立レビュー記録群（計9ファイル）を、`docs/Archives/qa_workflow/pr-openspec/artifacts/` へ集約・退避した。
対象となった各機能・検証コードは、PR #11（commit `4653d60`）および PR #13（commit `94e043c`）によりすべて `main` ブランチへマージされており、実装・レビュー・記録整理が完了した一連の文書である。

移動は削除を伴わず、元の相対構造とファイル名を維持して履歴保存した。Gitコミット `72b21e8` にて管理下に追跡済みであり、完全な復元可能性が担保されている。

## 確定した判断と理由

- **回答検証チェッカーの厳格化とJSON Schema準拠**:
  - Reviewer回答（JSON block）の形式検証において、当初の簡易検査から `references/review_reply.schema.json` を用いた型・必須・空文字・許容外プロパティの完全検証へ移行した（commit `bf32f4a`）。
  - JSON Schema規則に基づき、数値の等価性（1 と 1.0 は同等）や真偽値と数値の分離判定を導入した（commit `05cfae4`）。
- **全要求台帳と除外承認の厳格化**:
  - `build_ledger.py` により、H上のspecデルタから全要求・全シナリオを決定論的に抽出して台帳化する方式を採用。
  - `required: false` による除外を承認者（`approved_by`）と理由（`reason`）の明示記載がある場合に限定し、nullや空文字による不正PASSを排除した（commit `9e1edd5`）。
- **依頼書自己参照の解消**:
  - 依頼書自身を含むcommit（公開head P）のSHAやblob SHAを依頼書本文へ埋め込まず、PR本文および期待値manifestで対応付ける方式へ改訂した（commit `9e1edd5`）。
- **未完了項目・課題のスコープ整理**:
  - `evals/evals.json` の実モデル実行（4.1）および模擬リポジトリ環境評価（5.1）は、v0.1 のユニットテスト（52件PASS）およびCI通過をもって完了とし、v0.2 への繰越（Deferred）として合意した。
  - `kept_findings` における指摘詳細保持（P2-002）や Artifact 規約ヘッダーは、v0.1 の既知の制約（Known Limitation）として受容し、v0.2 以降の改善課題として整理した（PR #13）。

## 主要成果と検証の限界

- **集約ファイル数**: 9件（計画書1件、レビュー記録8件）。
- **検証実績**:
  - ユニットテスト: `quality-loop/skills/pr-openspec/tests/` 配下の 52 件すべてが通過（Python 3.12 / pytest 9.1.1）。
  - CI: GitHub Actions ワークフロー `.github/workflows/skills-tests.yml` にて自動テストが green（success）であることを確認。
  - OpenSpec Change 検証: `openspec validate add-pr-openspec-skill --strict` 成功。
- **検証上の限界**:
  - 本アーカイブ作業では、移動前後の SHA-256 照合とリンク検査、Git 差分検査のみを行い、製品コードの再テストや追加の独立レビューは実施していない。

## 未解決事項と引継ぎ

1. **OpenSpec Change `add-pr-openspec-skill` のアーカイブ**:
   - Change の実装・記録整理は完了しているため、本体 spec への同期・アーカイブ（`/opsx-archive` または `/opsx-sync`）が次の運用手順となる。
2. **v0.2 への改善課題**:
   - `validate_review_reply.py` の `kept_findings` における Finding 本文（観測事実・影響・確認方法）の完全保持。
   - `SKILL.md` 内の manifest 取得手順における PR 本文依存記述の完全な Git object 取得への整合。
   - 依頼書テンプレートへのプロジェクト標準 Artifact 規約（日本語、JSTヘッダー、連番管理）の適用。
   - `evals/evals.json` の実モデル（LLM）起動評価の実施。

## 元文書と復元情報

退避した全 9 ファイルの元パス、Archive先相対パス、SHA-256 ハッシュは以下の通り。

| 元文書 | Archive先 | SHA-256 | 復元情報 |
|---|---|---|---|
| `docs/Artifacts/implementation_plan_001_1025.md` | [implementation_plan_001_1025.md](artifacts/implementation_plan_001_1025.md) | `efa19c2e66a80be848ca8b3bed1c865235684e0fee33ee987f6e18f676b4b3ce` | Git コミット `72b21e8` より復元可能 |
| `docs/Artifacts/pr_openspec_plan_review_001_1025.md` | [pr_openspec_plan_review_001_1025.md](artifacts/pr_openspec_plan_review_001_1025.md) | `5cecfdb7da24966adf5a6c2329cc2396dd5ace0ee98d8b5d80ae5e8cfd6a90f0` | Git コミット `72b21e8` より復元可能 |
| `docs/Artifacts/pr_openspec_plan_review_002_1025.md` | [pr_openspec_plan_review_002_1025.md](artifacts/pr_openspec_plan_review_002_1025.md) | `034be6dedfcef44f8ac7dd9177c4581f7ee0b3a2b3726ba339ab0df0d42d09a8` | Git コミット `72b21e8` より復元可能 |
| `docs/Artifacts/pr_openspec_plan_review_003_1025.md` | [pr_openspec_plan_review_003_1025.md](artifacts/pr_openspec_plan_review_003_1025.md) | `6a3c16b6e3fdbe4cdef427640320a1f75f8b29623efd72be83f16bfcf31cbe2a` | Git コミット `72b21e8` より復元可能 |
| `docs/Artifacts/pr_openspec_plan_review_004_1025.md` | [pr_openspec_plan_review_004_1025.md](artifacts/pr_openspec_plan_review_004_1025.md) | `3c689e9043033a705c7589f4ae3d397b58ef1dd4f809d88da2a0ceab9f9d52f3` | Git コミット `72b21e8` より復元可能 |
| `docs/Artifacts/pr_openspec_plan_review_005_1025.md` | [pr_openspec_plan_review_005_1025.md](artifacts/pr_openspec_plan_review_005_1025.md) | `dcb3b8e6674a113774b077a12f6feed2f3e73b519a4a91505158a4080f1e549b` | Git コミット `72b21e8` より復元可能 |
| `docs/Archives/qa_workflow/pr-openspec/artifacts/pr_openspec_plan_review_006_1025.md` | [pr_openspec_plan_review_006_1025.md](artifacts/pr_openspec_plan_review_006_1025.md) | `1e97667ef36454bb80014551ea3a3fa36ef2b12023a68f59bd6278990df1a818` | Git コミット `72b21e8` より復元可能 |
| `docs/Archives/qa_workflow/pr-openspec/artifacts/pr_openspec_plan_review_007_1025.md` | [pr_openspec_plan_review_007_1025.md](artifacts/pr_openspec_plan_review_007_1025.md) | `f6e3e782ad51871ce5589f18f80e6622f5e674dd9ca1217aef3104df3ae3f582` | Git コミット `72b21e8` より復元可能 |
| `docs/Archives/qa_workflow/pr-openspec/artifacts/pr_openspec_plan_review_008_1025.md` | [pr_openspec_plan_review_008_1025.md](artifacts/pr_openspec_plan_review_008_1025.md) | `6ea88c9863058fc97cc328ae05f01ea83b6435abb667a7b506e7fb5b733f6a54` | Git コミット `72b21e8` より復元可能 |
