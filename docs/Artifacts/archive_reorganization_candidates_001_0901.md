# アーカイブ整理候補一覧

created: 2026-09-01 22:00 (JST)
update: 2026-09-01 22:00 (JST)
author: Codex (GPT-5)

## 目的

現行の利用導線を簡潔にしながら、開発経緯・設計判断・QA記録を失わないための候補一覧です。候補はリンク、正本、Git履歴を確認してから移動または現行導線から除外します。

## 現時点の分類

| 対象 | 現在の位置 | 方針 | 状態 |
| --- | --- | --- | --- |
| zip、tar.gz、原本パッケージ | `archives/` | バイナリ・原本アーカイブとして維持 | 移動不要 |
| 統合アーカイブ要約 | `docs/Archives/archived_summary_*.md` | `history/`から索引する | 既存リンク保護のため現位置維持 |
| 最終独立QA受入サマリー | `docs/Archives/qa_acceptance_summary_*.md` | `history/`から索引する | 既存リンク保護のため現位置維持 |
| Quality Loop実装・QA資料 | `docs/Archives/quality-loop/` | `history/`または`decisions/`候補 | リンク調査待ち |
| 旧spec-driven-qa資料 | `docs/Archives/spec-driven-qa/` | 旧版分類として維持 | 現行導線から分離済み |
| OpenSpecのarchive Change | `openspec/changes/archive/` | OpenSpecの履歴正本として維持 | 移動不要 |
| 開発計画・QA Artifact | `docs/Artifacts/` | 現行作業記録として維持 | 個別の正本確認が必要 |

## 削除しないもの

- 既存Git履歴と関連コミット・タグ
- 既存QAのEvidence、Owner裁定、ケース正本
- 原本zip、tar.gz
- 現行の検証に必要な仕様・テスト・Skill runtime
