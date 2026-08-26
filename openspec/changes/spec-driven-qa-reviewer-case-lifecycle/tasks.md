## 1. ステージング骨格と共有コア取込

- [x] 1.1 本Change配下に `stage/` を作成し、`shared_core/`・`schemas/`・`spec-driven-qa-review/launcher.py`・`SKILL.md` の骨格を共有基盤アーカイブから取り込み、期待パスが存在することを `find stage -type f | sort` で確認する
- [x] 1.2 Manifest に digest を記録し、アーカイブと比較した（2026-08-26 再測）。**schemas**: 一致（`f95acb52…`）。**shared_core**: 不一致（archive `82380f7b…` / current `80e492a7…`）。原因は CLI 配線のための `runtime.py` 等の意図的改変。「差分が空（契約改変なし）」の当初完了条件は **未達=`evidence-gap`** として明示する（改変を無かったことにしない）
- [x] 1.3 Reviewer Launcher が Bundle ルート解決後に起動し、共有コア欠落時は非ゼロ終了と構造化エラーを返すことを `test_reviewer_launcher_missing_shared_core` で確認する

## 2. 正本 allowlist と操作写像

- [x] 2.1 Reviewer 正本書込み allowlist を実装し、許可外パスへの書込み拒否 unit test を通す
- [x] 2.2 `init` を共有 operation `review`（`action=init`）へ写像し、`handoff` / `verify` / `close` が既存 `REVIEWER_OPERATIONS` のみで認可されることを確認する
- [x] 2.3 Author 役割での正本・events・closure 書込みが拒否される negative test を通す

## 3. ケース初期化（init）

- [x] 3.1 有効な target・purpose・profile でケースDIRを作成し、初期化イベントが追記されることを確認する
- [x] 3.2 target または purpose 欠落時に拒否され、ケースDIRを作らないことを確認する

## 4. 独立レビューと Finding / traceability

- [x] 4.1 Finding 必須フィールドを強制し、独立レビュー cycle 成果物へ保存されることを確認する
- [x] 4.2 evidence / purpose classification 欠落を拒否し、既存正本が変わらないことを確認する
- [x] 4.3 `traceability.yaml` 更新と `events.jsonl` 追記を確認する（観測済み。専用アサーション強化は残余改善）

## 5. handoff 生成

- [x] 5.1 正本から `handoff.md`（origin / revision / digest / open Finding IDs / scoped permission）を生成することを確認する
- [x] 5.2 handoff 手編集非正本化・再生成・**stale digest 入力の拒否**を自動テストで確認する → **消化**（`reviewer-verification-integrity-hardening` / `tests/test_verification_integrity.py`、2026-08-26、31 passed）

## 6. Author提出の verify と拒否

- [x] 6.1 handoff 必須・base_revision 必須・revision 一致・非空 test_evidence で verify できることを確認する
- [x] 6.2 自己クローズ / 未知 Finding ID を拒否することを確認する
- 残余: C3 の **Workspace 境界**は QA-0005-F01 で修正提出（独立 verification 待ち）。欠落パス拒否・空 `modified_files` 拒否は実装済み。C3 全体を消化済みとしない。

## 7. cycle 制限と close

- [x] 7.1 profile 別 cycle 上限超過で `adjudication-required` へ遷移することを確認する
- [x] 7.2 REQUIRED 解消・Critical 解決（Finding単位）・High の 5要素 `risk-accepted` 検証付き close を確認する
- [x] 7.3 REQUIRED 残存 / 未解決 Critical の close 拒否を確認する

## 8. CLI互換・機能台帳・文書

- [x] 8.1 Reviewer 公開機能ID対応表を Evidence に起稿する（状態列は本ファイルおよび capability_matrix の注記に従う）
- [x] 8.2 `SKILL.md` / `README` / `MANIFEST` を更新し、主要リンク切れを解消する
- [x] 8.3 実行時依存が標準ライブラリのみであることを確認する

## 9. 独立QAと完了境界

- [x] 9.1 正常系 E2E（init → review → handoff → verify → close）を pytest で実行し、exit 0 を確認する（21 passed, 2026-08-26）
- [x] 9.2 拒否系・role firewall・履歴追記の独立QAを実施する
- [x] 9.3 未検証 / 境界を記録し、外部Skill配置・旧版削除・commit・push を実施していないことを確認する

### 9.3 明示する `unverified` / `evidence-gap`

| 項目 | 区分 | 内容 |
|---|---|---|
| shared_core vs アーカイブ差分空 | evidence-gap | task 1.2。意図的改変あり |
| Token / API Latency | unverified | 計測手段なし |
| 外部配備・rollback | out-of-scope | 後続 Change |
