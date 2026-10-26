# 実装記録: add-pr-openspec-skill

## 実施内容（2026-10-25）

- 計画第5版を反映（`design.md`）。全要求台帳と承認済み除外、P2の権限境界の評価を追加。
- 実装（`quality-loop/skills/pr-openspec/`、VERSION 0.1.0）:
  - `scripts/validate_review_reply.py`: 回答（Markdownの```json block 1個、または回答JSON）を期待値manifestと照合する決定的checker。終了コード 0=PASS、1=FAIL、2=INCONCLUSIVE、3=使用法の誤り。
  - `scripts/build_ledger.py`: 監査対象HのspecデルタからR・Sの全台帳を作る（git blob SHA付き）。
  - `references/review_reply.schema.json`: 回答JSONの形式（条件付きの必須はcheckerが検証）。
  - `SKILL.md`、`assets/review_request_template.md`。
  - `evals/evals.json`: 起動評価4件、権限境界を含む評価6件。
- テスト: `python3 -m pytest tests`（pr-openspec）→ 53件通過。
  - 回答JSONのスキーマ検証（必須・型・const・空文字・許容外フィールド・items）を標準ライブラリで実装し、スキーマ違反11件の試験を追加。旧checkerに対しては10件が失敗することを確認した。
  - 最低ケース一覧に対応するフィクスチャ25件（`tests/fixtures/`）。
  - `kept_findings`は、nonconformingの基準IDに加え、回答のfinding本文（observation・impact・how_to_verify）を残す（2026-10-26）。
  - 必須基準の`out_of_scope`規則を一時的に壊すとテストが失敗することを確認（変更を戻すと通過）。
  - 台帳作成は、一時gitリポジトリ（ADDED・MODIFIED・RENAMED、不正な順序、対象外のセクション）で試験。
- 実在の change（`add-pr-openspec-skill`、HEAD）に対して`build_ledger.py`を実行し、18件（R 7、S 11）の台帳を得た。

## 完了記録と残件（2026-10-26更新）

- **1.1 計画の独立レビュー:** PR #11 のレビュー対応と第8版で対応完了（範囲限定の PASS）。
  - 第5版（2c344b4）: 別系統レビュー005で「指摘あり」（STD-001、SPEC-001〜003）。
  - 第6版（67f8c8f）: レビュー006で「指摘あり（修正が必要）」。
  - 第7版（9e1edd5）: レビュー007で、P1二件の修正を対象とする範囲限定再レビューがPASS。
  - 第8版（05cfae4）: レビュー008で、指摘三件（1.0の誤判定、改訂履歴、実装記録）の範囲限定再レビューがPASS。
  - **計画全体を対象とするPASSは得ていない。** 範囲限定PASSの系列で指摘を解消したとみなすことは、利用者が2026-10-26に承認した。
  - 記録: `docs/Artifacts/pr_openspec_plan_review_008_1025.md`（Mac側、未追跡）に保存。
- **1.2 既存Skillの参照先の照合（実コード）:** 2026-10-26に再確認し、design.md 52〜54行の参照先はすべて実在。
  - `state.json`: `runtime/spec_review_loop/session.py`、`finish.py`で読み書き。
  - `Spec-Review-Round`: `gitops.py:14`（`ROUND_TRAILER`）。
  - `criteria.json`: `session.py`、`criteria.py`。
  - `r<N>_prompt.md`: `session.py:133`。`r<N>_review.json`: `session.py:256`。
- **4.1 起動評価の実行:** Deferred to v0.2。v0.1の対象外として利用者が承認（2026-10-26）。`evals/evals.json`の4件（起動）と6件（権限境界）は定義済みだが、実モデルでの実行はしていない。v0.2以降で扱う。
- **5.1 模擬ケース:** Deferred to v0.2。v0.1の対象外として利用者が承認（2026-10-26）。checker単体の判定（回答の不一致、遅延回答の版違い等）はフィクスチャで確認済み。公開操作を伴う手順（H→P、head変化など）は模擬していない。v0.2以降で扱う。
- **6.2 本記録:** テスト件数、評価の状態、残件、利用者判断の事項を、この節で区別して記録した。
- **Medium（生成物の日本語・JSTヘッダー・連番規則）:** 出典は利用者の申告（Global Agent Rules、ユーザー環境側の共通規約、リポジトリ外）。リポジトリ内の文書では確認していない。依頼書テンプレートへの適用と厳格化は Deferred to v0.2。

## 既知の注意点

- このブランチ（`feat/pr-openspec-skill`）は、アーカイブ前の`main`から分岐していたが、`main`（33584de、PR #10）を取り込み済み（f63d43b）。`add-in-agent-review-controls`は`main`でアーカイブ済みで、`openspec/specs/spec-review-loop/spec.md`に反映されている。
- `kept_findings`は、nonconformingの基準IDに加え、回答のfinding本文（observation・impact・how_to_verify）を保持する。v0.1で実装・試験済み（61c6a8e、PR #12）。Known Limitation ではない。
- `build_ledger.py`は除外を作らない。除外は、利用者の承認を依頼書に記載した上で、manifestへ人が入力する。
