---
case_id: QA-0001
cycle: 3
action: reviewer-verification
performed_by:
  agent_id: "codex-reviewer"
  role: reviewer
  tool: "Codex GPT-5"
completed_at: "2026-08-25T00:05:00+09:00"
base_revision: "3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3"
reviewed_revision: "0088b8c256878aff4e58ea9b474538693f4d93fa"
outcome: adjudication-required
next_cycle_required: false
---

# Reviewer Verification — Cycle 3

## 検証対象

Cycle 3 Author Responseが提出したrevision `0088b8c256878aff4e58ea9b474538693f4d93fa`を、Cycle 2の指摘、実装差分、テスト、静的検証結果と照合した。Author Responseおよび実機主張だけでは判定していない。

## 確認できた是正

- `qnap/deploy_qnap.sh`の固定資格情報表示は除去された。
- `QNAP_PASS`、`INFLUXDB_PASSWORD`、`INFLUXDB_TOKEN`、`GRAFANA_PASSWORD`の未設定検証が追加された。4段階の読み取り専用fail-closedプローブで、各不足変数の終了コード1を確認した。
- `bin/omronCollector.sh`の`sudo env INFLUXDB_TOKEN=...`形式は除去された。
- `.env.example`にQNAP／InfluxDB／Grafanaの設定項目が追加された。
- `python3 -m unittest -v tests/test_pipeline.py`: 7件成功。
- `bash -n qnap/deploy_qnap.sh bin/omronCollector.sh bin/NASmount.sh bin/qnap1`: 成功。

## 残存する重大な不一致

1. `qnap/deploy_qnap.sh:51`および`:103`は、`echo '${QNAP_PASS}' | sudo -S`をSSHコマンド文字列へ埋め込む。Cycle 3の「SSHコマンド行への秘密値露出を完全排除」という主張と直接矛盾する。ShellCheckもSC2029を指摘している。
2. `bin/NASmount.sh:26-28`はCIFSパスワードを`mount -o password=...`へ展開し、`bin/qnap1:29`はpasswordをexpectスクリプトへ展開する。周辺スクリプトを外部化しただけで、プロセス引数・ログ経路への露出を排除していない。
3. `omron_collector.py:46-70`の`load_env_file`は`.iot_env`のmode 600を検証せず、権限が緩いファイルも読み込む。Pi上のmode 600はAuthor Claimであり、コード上の安全条件ではない。
4. Docker CLIがローカルにないためCompose展開、QNAP上の実コンテナ環境変数、Pi上の`ps`と`.iot_env`権限600は独立再現できない。これらは`AUTHOR-CLAIM`／`UNVERIFIED`である。

## 判定と状態遷移

F01は`fixed-and-verified`ではなく`partially-fixed`のままとする。High FindingがCycle 3終了時点で未解決であり、親Skillの「最大3自動サイクル」規則に従い、これ以上の自動Author Response／Reviewer Verificationは継続しない。

QAケースは`adjudication-required`、resultも`adjudication-required`とする。人間または権限を持つadjudicatorが、QNAP認証方式（SSH鍵・sudo設定・secret file等）、周辺スクリプトの対象範囲、資格情報ローテーション、実機Evidenceの受入条件を決定するまでクローズ不可である。

## 検証制約

- QNAP／Piへの書き込み、サービス再構成、資格情報ローテーションは実施していない。
- 実機の成功ログ・ファイル権限は提出文の主張としてのみ扱った。
- 既存Cycle 1〜3の履歴は削除・改名していない。
