# Cycle 01 Independent Review

- **Case ID:** `QA-0007`
- **Target:** `openspec/changes/separate-semantic-content-digests`
- **Reviewer:** `reviewer` (Antigravity)
- **Implementer:** `codex` / `author`
- **Date:** 2026-08-26 23:36:00 (JST)
- **Profile:** `standard`
- **Status:** `accepted-with-residual-risk`

---

## 1. 独立評価サマリ

`separate-semantic-content-digests` Change は、先行する QA-0006 で指摘された F06（`semantic_digest` と `content_digest` の同値縮退問題）を解消するために、共有コアにおける名前空間分離および入力正規化境界を実装したものである。

独立検証として以下を確認した：

1. **名前空間と算出入力の分離 (`shared_core/digest.py`):**
   - `semantic_digest`: `namespace="qa-semantic-v1"` により意思決定構造（case_id, open_finding_ids, cycle, case_revision）から算出。
   - `content_digest`: `namespace="qa-content-v1"` により正規化された handoff 本文（volatileフィールド除外後）から算出。
   - 同一入力において `semantic_digest != content_digest` が担保されることを確認。
2. **本文変更の検知と非終端性 (`submission.py`):**
   - 本文のみが変更された場合、`handoff content_digest does not match handoff content` として正しく拒否されることを確認。
3. **旧同値digestおよび未知versionの拒否 (`submission.py`, `digest.py`):**
   - 旧形式の同値digestに対して `legacy equivalent semantic/content digest is not accepted` エラーを返出。
   - `v1` 以外の未知 digest version は `unsupported-digest-version` として例外送出。
4. **秘密値防御 (`_reject_secrets`):**
   - `api_key`, `token`, `password` 等が digest 入力に含まれる場合に `secret-in-digest-input` を送出。
5. **テスト実行と回帰確認:**
   - 関連テスト全67件が cache-free 環境下でパスすることを確認（[pytest-results.txt](../evidence/pytest-results.txt)）。
   - 独立プローブによる動作確認（[probe-verification.txt](../evidence/probe-verification.txt)）。

---

## 2. Findings

新規の未解決 Finding は 0 件（Critical: 0, High: 0, Medium: 0, Low: 0）。

---

## 3. 残余リスク（明示）

1. **外部Skill未配備:** 外部Skillディレクトリへの配置、旧版削除、commit、pushは実施せず、別Changeへ引き継ぐ。
2. **リビジョン固定制約 (`unverified-no-git`):** Gitリポジトリ未初期化環境のため、コミットSHAによる固定ではなくファイル内容に基づく検証を実施。
