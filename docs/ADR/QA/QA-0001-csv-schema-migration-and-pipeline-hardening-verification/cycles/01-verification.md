---
case_id: QA-0001
cycle: 1
action: reviewer-verification
performed_by:
  agent_id: "codex-reviewer"
  role: reviewer
  tool: "Codex GPT-5"
completed_at: "2026-08-24T22:11:33+09:00"
reviewed_revision: "8a8770480aad7d939ec03ecca835e7c8720b97ed"
outcome: partially-fixed
next_cycle_required: true
---

# Reviewer Verification — Cycle 1

## 検証対象

作成者回答が参照するrevision `8a8770480aad7d939ec03ecca835e7c8720b97ed`を対象に、ソース、回帰テスト、Pi Zeroの配備ハッシュ・起動ログ・CSVを再確認した。作成者回答本文だけでは判定していない。

## QA-0001-F01

- 判定: `partially-fixed`
- 確認済み: `storage_influx.py`のtoken未設定時fail-closed、`test_05_auth_fail_closed`、`.env.example`。
- 未解決: `omron_collector.py:153`のtokenフォールバック、`qnap/deploy_qnap.sh`の資格情報、`qnap/docker-compose.yml`のInfluxDB/Grafana認証情報が残る。
- 制約: 実資格情報の有効性・ローテーション状態は確認せず、値も記録しない。
- 次の要求: 全資格情報をsecret fileまたは環境変数のみへ移行し、collector起動経路を含む未設定時fail-closedテストを提出する。

## QA-0001-F02

- 判定: `fixed-and-verified`
- 根拠: `get_last_sequences()`、`last_seq_map`、7件テスト、PiログのSeq 182復元、Seq 183〜186各1回処理。
- 残余リスク: 現在月以外のCSV、月跨ぎ、複数センサーの再起動後復元は未検証。

## QA-0001-F03

- 判定: `fixed-and-verified`
- 根拠: MACをdedup keyとする実装、異なるMAC・同一sequenceの独立処理、同一MAC再受信の抑止テスト。
- 残余リスク: 複数センサーの再起動後復元は未検証。

## 実行結果

- `python3 -m unittest -v tests/test_pipeline.py`: 7 tests / 7 passed。
- 一時pycache出力先を用いた`compileall`: 成功。
- Pi配備ハッシュ: 対象3ファイルがローカルrevisionと一致。
- 外部システムへの書き込み、Pi停止・再起動、資格情報ローテーションは未実施。

## Cycle結果

F02/F03は検証済み、F01は未解決Highのため、caseは`author-action-required` / `conditionally-accepted`に留める。F01対応後にCycle 2のauthor-responseとreviewer-verificationを行う。
