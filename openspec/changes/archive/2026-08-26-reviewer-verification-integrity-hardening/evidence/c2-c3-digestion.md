# C2/C3 消化メモ

date: 2026-08-26 (JST)
update: 2026-08-26 (JST) — QA-0005-F02 是正
change: reviewer-verification-integrity-hardening

## QA-0004 Acceptance Conditions

| ID | 内容 | 結果 |
|---|---|---|
| C2 | stale digest 拒否の自動テスト | **消化**: `tests/test_verification_integrity.py`（semantic / content negative + fresh golden） |
| C3 | test_evidence パス実在 / modified_files 必須 **および Workspace 境界** | **部分消化 + evidence-gap（境界は QA-0005-F01 で修正提出、Reviewer verification 待ち）** |

C3 の「欠落パス拒否・空 `modified_files` 拒否・相対パス実在」は実装済み。  
**Workspace 外絶対パス／`../`／symlink 脱出の拒否は、当初「消化」と誤記していた。** 当該境界は QA-0005-F01 の fix-submitted 対象であり、独立 reviewer-verification 前に C3 全体を消化済みとしない。

## pytest

- baseline: 21 passed（`baseline-pytest.txt`）
- after hardening (pre-F01): 31 passed（`pytest-after-hardening.txt`）
- after F01 workspace boundary: 34 passed（`pytest-after-f01-boundary.txt`）

## 実装箇所

- `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/spec-driven-qa-review/lifecycle.py`
  - `compute_handoff_digests` / `classify_evidence_ref` / `resolve_in_workspace` / `require_workspace_existing_path`
- MANIFEST.json の該当 sha256 を更新（launcher digest 検証用）
