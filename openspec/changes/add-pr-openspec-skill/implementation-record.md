# 実装記録: add-pr-openspec-skill

## 実施内容（2026-10-25）

- 計画第5版を反映（`design.md`）。全要求台帳と承認済み除外、P2の権限境界の評価を追加。
- 実装（`quality-loop/skills/pr-openspec/`、VERSION 0.1.0）:
  - `scripts/validate_review_reply.py`: 回答（Markdownの```json block 1個、または回答JSON）を期待値manifestと照合する決定的checker。終了コード 0=PASS、1=FAIL、2=INCONCLUSIVE、3=使用法の誤り。
  - `scripts/build_ledger.py`: 監査対象HのspecデルタからR・Sの全台帳を作る（git blob SHA付き）。
  - `references/review_reply.schema.json`: 回答JSONの形式（条件付きの必須はcheckerが検証）。
  - `SKILL.md`、`assets/review_request_template.md`。
  - `evals/evals.json`: 起動評価4件、権限境界を含む評価6件。
- テスト: `python3 -m pytest tests`（pr-openspec）→ 33件通過。
  - 最低ケース一覧に対応するフィクスチャ25件（`tests/fixtures/`）。
  - 必須基準の`out_of_scope`規則を一時的に壊すとテストが失敗することを確認（変更を戻すと通過）。
  - 台帳作成は、一時gitリポジトリ（ADDED・MODIFIED・RENAMED、不正な順序、対象外のセクション）で試験。
- 実在の change（`add-pr-openspec-skill`、HEAD）に対して`build_ledger.py`を実行し、18件（R 7、S 11）の台帳を得た。

## 未実施・未確認

- **1.1 独立レビュー（計画第5版）:** 未実施。別系統のAI Reviewerによる独立レビューが必要。作成側である私の検証では代替できない。
- **4.1 起動評価の実行:** 評価ケースは作成したが、Skillの起動判定を実モデルで実行していない。
- **5.1 模擬ケースの確認:** 公開操作を伴う手順（H→P、head変化、遅延回答など）を、模擬リポジトリで実行していない。checker単体の判定（回答の不一致、遅延回答の版違い等）はフィクスチャで確認済み。
- **Medium（生成物の日本語・JSTヘッダー・連番規則）:** 規則の出どころが未確認。依頼書テンプレートは、現時点では規則を含まない。
- **proposal・tasks の第3版参照:** 第5版へ更新済み。

## 既知の注意点

- このブランチ（`feat/pr-openspec-skill`）は、アーカイブ前の`main`から分岐している。`add-in-agent-review-controls`の未アーカイブ状態が残っているため、`main`へ入れる前に`main`を取り込み、重複を解消する必要がある。
- `build_ledger.py`は除外を作らない。除外は、利用者の承認を依頼書に記載した上で、manifestへ人が入力する。
