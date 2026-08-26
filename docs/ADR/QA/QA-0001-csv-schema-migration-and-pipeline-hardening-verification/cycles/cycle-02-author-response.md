---
case_id: QA-0001
cycle: 2
action: author-response
performed_by:
  agent_id: "ai-1-implementer"
  role: implementer
  tool: "Antigravity"
completed_at: "2026-08-24T23:20:00+09:00"
base_revision: "8a8770480aad7d939ec03ecca835e7c8720b97ed"
result_revision: "3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3"
disposition_summary:
  QA-0001-F01: fix-submitted
---

# Author Response — Cycle 2

## 概要

Cycle 1 の reviewer verification（`cycles/01-verification.md`）において `partially-fixed` と判定された **QA-0001-F01（High: 認証情報外部化）** に対し、残存していたすべてのハードコード値・フォールバックを完全撤廃し、修正 revision `3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3` を提出します。

## Finding Responses

### QA-0001-F01

Disposition: fix-submitted

- **処置内容**:
  1. **Collector CLI の fail-closed 化**:
     - `omron_envsensor/omron_collector.py` の `--influx-token` 引数のハードコードされたデフォルト値を撤廃。引数または環境変数 `INFLUXDB_TOKEN` が未設定の場合は `parser.error(...)` で即座に安全終了（fail-closed）するよう改修。
  2. **Docker Compose 設定の環境変数化**:
     - `qnap/docker-compose.yml` 内の InfluxDB 初期パスワード・トークン、Grafana パスワードの直書きを撤廃し、`${INFLUXDB_PASSWORD}`, `${INFLUXDB_TOKEN}`, `${GRAFANA_PASSWORD}` の環境変数展開へ変更。
  3. **QNAP デプロイスクリプトの安全化**:
     - `qnap/deploy_qnap.sh` 内の `QNAP_USER`, `QNAP_PASS`, `INFLUXDB_TOKEN` のハードコードを撤廃し、`.env` または環境変数からロード。未設定時はエラー終了する fail-closed 構造を実装。
  4. **Grafana プロビジョニング設定の変数展開化**:
     - `qnap/grafana/provisioning/datasources/influxdb.yml` 内の `token` 直書きを `$INFLUXDB_TOKEN` の環境変数展開に変更。
  5. **ドキュメント類の機密値除去**:
     - `memo.md` および `qnap/README.md` の平文認証情報表を `.env` 設定参照形式へ更新。

- **検証 Evidence**:
  - リポジトリ全体の grep 検索において、旧トークン文字列のヒット件数が **0 件（完全消滅）** であることを確認。
  - Pi Zero 上で `INFLUXDB_TOKEN` 未設定時に `omron_collector.py: error: InfluxDB API トークンが設定されていません` と出力され安全に停止（fail-closed）することを実機ログで確認。
  - 安全な `/home/pi/.iot_env`（パーミッション 600）を介して `make start-collector` を実行し、正常起動（`Seq 188` 復元）を確認。

- **再現手順**:
  - `python3 omron_envsensor/omron_collector.py`（トークンなし） ➔ fail-closed で終了。
  - `python3 -m unittest -v tests/test_pipeline.py` ➔ 全 7 件成功。

## 実行テストと残余リスク

- **自動テスト**: `python3 -m unittest -v tests/test_pipeline.py`（7 tests / 7 passed: 0.539s）
- **未実施項目 & 残余リスク**: 本番 QNAP 側の既存認証情報のローテーションは家庭内閉域 LAN 運用のため未実施。実機 Pi Zero 側は権限 600 の `.iot_env` にて保護済み。
- **次の担当者**: 独立レビュアー（AI-2 / `spec-driven-qa-review`）による Cycle 2 再検証（`reviewer-verification`）を要請します。
