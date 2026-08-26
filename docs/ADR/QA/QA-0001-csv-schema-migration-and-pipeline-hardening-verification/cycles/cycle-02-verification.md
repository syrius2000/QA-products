---
case_id: QA-0001
cycle: 2
action: reviewer-verification
performed_by:
  agent_id: "codex-reviewer"
  role: reviewer
  tool: "Codex GPT-5"
completed_at: "2026-08-24T23:45:00+09:00"
base_revision: "8a8770480aad7d939ec03ecca835e7c8720b97ed"
reviewed_revision: "3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3"
outcome: partially-fixed
next_cycle_required: true
---

# Reviewer Verification — Cycle 2

## 検証対象

Cycle 2 Author Responseが提出したrevision `3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3`を、前回reviewer verificationのrevision `8a8770480aad7d939ec03ecca835e7c8720b97ed`との差分、実装、テスト、設定およびQA証拠台帳と照合した。Author Responseの主張だけでは判定していない。

## QA-0001-F01 — `partially-fixed`（継続）

### 確認できた是正

- `omron_collector.py`の`--influx-token`既定値は空文字となり、未設定時は`parser.error`で停止する。
- `storage_influx.py`のtoken未設定時`ValueError`と既存のfail-closedテストは維持されている。
- `qnap/deploy_qnap.sh`は`QNAP_PASS`および`INFLUXDB_TOKEN`未設定時に終了する。読み取り専用の空環境プローブでは、それぞれ終了コード1を確認した。
- `qnap/docker-compose.yml`、Grafanaデータソース、memo、QNAP READMEから前回のInfluxDB token文字列は除去されている。
- `python3 -m unittest -v tests/test_pipeline.py`は7件成功し、`bash -n qnap/deploy_qnap.sh bin/omronCollector.sh`も成功した。

### 未解決事項

1. `qnap/deploy_qnap.sh:74-76`の成功メッセージに、InfluxDBおよびGrafanaの固定ユーザー・パスワードが残っている。これは「全資格情報の直書き撤廃」という主張と矛盾する。
2. Composeは`INFLUXDB_PASSWORD`と`GRAFANA_PASSWORD`を必須展開するが、`deploy_qnap.sh`はこれらを事前検証せず、`.env.example`にも両変数の設定例がない。未設定時に空値で起動を試みるため、デプロイ経路全体のfail-closedは未証明である。
3. `bin/omronCollector.sh`は`INFLUXDB_TOKEN`を`sudo env ...`のコマンド行へ展開し、`qnap/deploy_qnap.sh`もQNAPパスワードとInfluxDB tokenをSSH経由のコマンド文字列へ埋め込む。秘密値のプロセス一覧・シェル展開への露出を避ける設計になっていない。
4. Author Responseが主張するPi上の未設定fail-closedと`.iot_env`権限600は、今回のローカル証拠台帳には新しい実機取得記録がなく、独立に再現できないため`AUTHOR-CLAIM`／`UNVERIFIED`として扱う。
5. リポジトリ全体の「資格情報0件」という表現は、対象範囲をIoTデプロイ経路に限定するなら再定義が必要である。対象外候補の`bin/NASmount.sh`、`bin/qnap1`、`config/vim/after/plugin/vimrc02plugin.vim`、`update-pizero.md`にも平文または固定資格情報が残る。

### 判定

F01は`fixed-and-verified`ではなく`partially-fixed`とする。High Findingを解消するには、QNAP／Collectorの全起動経路でsecret fileまたは環境変数を安全に参照し、必須変数を起動前に検証し、成功メッセージとプロセス／SSHコマンド行への秘密値露出を除去する必要がある。実運用資格情報のローテーション実施記録も、値を記載せずに別Evidenceとして提出する。

## 検証制約

- Docker CLIがローカル環境にないため、Composeの実展開結果とQNAP上の起動は検証していない。
- QNAP／Piへの書き込み、資格情報ローテーション、サービス再構成は実施していない。
- 既存のCycle 1記録は履歴として保持し、今回の判定で上書きしていない。

## Cycle 2結果

QAケースは`author-action-required`／`conditionally-accepted`のままとする。F01の追加修正と、同一revisionに対するCycle 3 reviewer-verificationが必要である。自動サイクル上限に達した場合は、親Skillの規則に従い`adjudication-required`へ移行する。
