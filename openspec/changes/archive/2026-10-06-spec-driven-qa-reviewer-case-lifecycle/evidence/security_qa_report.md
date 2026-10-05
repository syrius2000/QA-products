# Reviewer 独立QA・権限分離・安全性レポート

作成日: 2026-08-26
対象Change: `spec-driven-qa-reviewer-case-lifecycle`

## 安全性・権限境界の検証メトリクス

| 評価項目 | 期待動作 | 観測結果 | 判定 |
|---|---|---|---|
| Author による自己クローズ要求 | 契約違反として拒否（ValueError / exit code 1） | 0件受理（完全拒否） | PASS |
| 未知 Finding ID の提出 | 契約違反として拒否（正本不変） | 0件受理（完全拒否） | PASS |
| Author による正本ファイル書込み | `allowlist.py` / PermissionError で拒否 | 0件書込み（完全拒否） | PASS |
| 履歴不変性 (Append-only) | `events.jsonl` への過去イベント改ざんなし、追記のみ | 5/5 イベント追記確認 | PASS |
| 実行時依存関係 | Python 3.10+ 標準ライブラリのみ使用（PyYAML等不使用） | stdlibのみ確認 (`test_imports_std_only.py`) | PASS |

## 残余リスクと運用境界
- **外部Skill未配備**: 本Change配下の `stage/` のみで検証しており、グローバルSkill領域への配備は未実施。
- **旧版削除・commit・push未実施**: 変更は本Change内に閉じている。
- **未検証項目 (`unverified` / `evidence-gap`)**:
  - Token使用量・ネットワークLatency実測
  - shared_core とアーカイブの「差分空」条件（意図的改変あり。digest は capability_matrix に記録）
- **後続 Change で部分消化（2026-08-26）**:
  - stale digest 拒否の専用自動テスト → `reviewer-verification-integrity-hardening`
  - verify における `test_evidence` パス実在、`modified_files` 非空必須 → 同上
  - **Workspace 境界** → QA-0005-F01 `fix-submitted`（独立 verification 待ち。消化済みとしない）
