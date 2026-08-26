---
case_id: QA-0001
cycle: 1
action: independent-review
performed_by:
  agent_id: "codex-reviewer"
  role: reviewer
  tool: "Codex GPT-5"
started_at: "2026-08-24T21:42:26+09:00"
completed_at: "2026-08-24T21:48:00+09:00"
input_revision: "d0178d8b2327ee6dfa3f3df6a71e4de2554c26c1"
blind_first: false
outcome: findings-issued
---

# 独立レビュー — サイクル1

## 実際に確認した入力

### 含めたもの

- 前回QA記録の目的・指摘・判定
- アーカイブ済み是正changeのproposal、design、spec、tasks
- 昇格後main spec
- `storage_csv.py`、`omron_collector.py`、`storage_influx.py`、`models.py`、`deploy_qnap.sh`、`docker-compose.yml`
- `tests/test_pipeline.py`の実行結果
- Pi Zero、QNAP、Grafana/InfluxDBの読み取り専用状態

### ブラインド段階で除外したもの

- なし。依頼文に実装者の完了報告が含まれていたため、完全なブラインド段階は成立しなかった。

## 観測した実装意図

起動時またはCSV追記時にヘッダーを検査し、旧11列をバックアップして15列へ再生成する。コレクターはプロセス内の`last_seq`と現在のsequenceを比較し、同じ場合はCSV/InfluxDB処理をスキップする。InfluxDBはバケットごとに最大100件のメモリdequeを持ち、送信成功時にclearする。

## Purpose / Spec / Plan / Implementation / Evidenceの比較

- CSVスキーマ移行: 実装、ローカルテスト、Pi実機状態が整合し、前回C-01は是正された。
- Bulk Write: モックHTTP回帰テストは実装されたが、実サービスの障害復旧とプロセス再起動を含まない。
- sequence dedup: 同一プロセス内は成立するが、状態の永続化がなく、実機で再起動境界の重複を確認した。
- 認証情報外部化: 依頼文の主張はコードの直書き・フォールバック残存と矛盾する。
- 複数センサー: `last_seq`が単一値で、異なるdevice/MACを識別しない。将来拡張のPurposeとテストが不足する。

## 発行したFinding

- `QA-0001-F01`: High / 認証情報外部化の不一致
- `QA-0001-F02`: Medium / 再起動境界のsequence重複
- `QA-0001-F03`: Medium / センサー単位でないdedupキー

## レビュー制約

- 実機操作は読み取り専用。Piの停止・再起動、CSV書き込み、QNAP再構成は行っていない。
- `192.168.0.200`はタイムアウトし、`raspberryZERO.local`でのみ実機確認した。
- 実InfluxDBへの認証付きクエリ・書き込みは行っていない。
- 完了報告、tasksの`[x]`、`valid: true`は補助情報であり、実装証拠として単独採用していない。
