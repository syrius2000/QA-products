# modern-iot-data-pipeline QAレビュー記録

created: 2026-08-24 21:26 (JST)
update: 2026-08-24 21:26 (JST)
author: Codex (GPT-5)

## 1. レビュー概要

対象変更は `modern-iot-data-pipeline`。再レビュー時点では、変更はコミット `977cf8f` により `openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/` へアーカイブ済みであった。

アクティブ変更としての `openspec status` と `openspec instructions apply` は対象変更なしで実行できなかったため、アーカイブ済みArtifact、昇格後のmain spec、実装、テスト、Pi Zero、QNAP、InfluxDB、Grafanaの状態を直接突き合わせた。

レビューは読み取り専用で実施した。コード、設定、データ、外部システム、Git履歴の変更は行っていない。

## 2. 総合判定

| 観点 | 判定 |
|---|---|
| タスク完了 | OpenSpec上10/10、証拠ベース9/10 |
| 要件適合 | 4件中2件適合、1件部分適合、1件不適合 |
| シナリオ | 4件中3件成立、CSVシナリオは実機不成立 |
| 自動テスト | 5/5成功。ただし復旧Bulk Writeと既存CSV移行は未検査 |
| OpenSpec main spec | 3件すべて `valid: true` |
| アーカイブ判定 | **CRITICAL 1件。クローズ不可** |

### 最終評価

アーカイブ済みだが、現行実機CSVがmain specのCSV永続化要件を破っている。CSVスキーマ移行を含む是正changeを作成し、修正後に再検証する必要がある。

## 3. 検証したArtifactと実装

### OpenSpec

- [アーカイブ済みproposal](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/proposal.md)
- [アーカイブ済みdesign](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/design.md)
- [アーカイブ済みspec](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/specs/iot-data-pipeline/spec.md)
- [アーカイブ済みtasks](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/tasks.md)
- [昇格後main spec](../../openspec/specs/iot-data-pipeline/spec.md)

### 実装・設定

- [データモデル](../../omron_envsensor/models.py)
- [パーサー](../../omron_envsensor/parser.py)
- [InfluxDBストレージ](../../omron_envsensor/storage_influx.py)
- [CSVストレージ](../../omron_envsensor/storage_csv.py)
- [コレクター](../../omron_envsensor/omron_collector.py)
- [Grafanaダッシュボード](../../qnap/grafana/provisioning/dashboards/omron_dashboard.json)
- [QNAPデプロイスクリプト](../../qnap/deploy_qnap.sh)

## 4. 実行した検証と結果

### ローカル検証

- `python3 -m unittest -v tests/test_pipeline.py`: **5 tests / 5 passed**
- Python対象モジュールの `py_compile`: 成功
- `bash -n bin/omronCollector.sh qnap/deploy_qnap.sh`: 成功
- JSON構文検査: 成功
- `openspec validate --all --json`: main spec 3件すべて成功
- `git diff --check HEAD`: 成功
- `shellcheck`: エラーなし。QNAP既存スクリプトにSC2029、SC2162の注記あり

### 独立Store & Forward検証

送信失敗2回後に3観測を蓄積し、復旧時に確認した。

- `sensor_data`: 6 Lineを1 HTTPリクエストで送信
- `sensor_data_1y`: 3 Lineを1 HTTPリクエストで送信
- 復旧後の両キュー: 0件
- 容量10へ11件投入した場合: キューは10件、最古データは破棄

前者は実装動作として成立するが、後者はspecの「欠損ゼロ」と矛盾する。

### Pi Zero実機

読み取り時点でコレクターは稼働中だった。

- プロセス: `omron_collector.py` が稼働
- 配備済み主要ファイルのSHA-256: ローカル実装と一致
- 実行RSS: 17,560 KiB
- `env_202608.csv`: 旧11列99行、新15列63行
- 同一sequence番号が約1分間隔で複数回記録されている

### QNAP / InfluxDB / Grafana

- InfluxDBヘルス: `pass`、v2.7.12
- `sensor_data`: 無期限保持
- `sensor_data_1y`: 31,536,000秒（365日）保持
- 3 Measurementの最新データを確認
- 最新データは同一タイムスタンプ、`device_id`、`location`、`mac`、`gateway`を保持
- DI Fluxクエリ: HTTP 200、値79.61
- WBGT近似Fluxクエリ: HTTP 200、値26.61
- UV Fluxクエリ: HTTP 200、値0.01
- QNAP上のGrafana JSONとローカルJSONのSHA-256: 一致
- Grafanaヘルス: `ok`、v13.2.0

## 5. 要件別評価

### 要件1: 生データの型安全な抽出

**適合。** パーサー、dataclass、異常パケット拒否、派生値をInfluxへ保存しない構造を確認した。正常・異常パーサーテストも成功した。

### 要件2: 3 Measurementと共通タグ

**適合。** [models.py](../../omron_envsensor/models.py) の共通タグ生成により、`env_metrics`、`device_telemetry`、`motion_events`の全Measurementへ同じタグとタイムスタンプが付与される。実機InfluxDBでも確認した。

### 要件3: Store & Forward

**部分適合。** 通信復旧時のバケット別Bulk Writeは成立する。一方、`deque(maxlen=100)`の上限超過時とプロセス再起動時には未送信データを失う。designにもこの制限が記載されているため、specの欠損ゼロ表現を修正するか、永続スプールを追加する必要がある。

### 要件4: ローカルCSV二重永続化

**実機不適合。** [storage_csv.py](../../omron_envsensor/storage_csv.py) はファイル存在だけを確認し、既存ヘッダーの列構成を検査しない。その結果、Pi Zero上で旧11列と新15列が混在した。

## 6. CRITICAL

### C-01: 実機CSVのスキーマ混在

対象: [storage_csv.py:24](../../omron_envsensor/storage_csv.py:24)、[main spec:29](../../openspec/specs/iot-data-pipeline/spec.md:29)

現行CSVは旧11列ヘッダーの下に新15列行が追記され、CSVとして一貫した表構造になっていない。現在もコレクターが稼働しているため、不整合データが増加する可能性がある。

推奨対応:

1. 既存ヘッダーと期待スキーマを比較する。
2. 不一致時は既存ファイルを保持したままローテーションする。
3. 新15列ヘッダーのファイルへ追記を開始する。
4. 旧11列ファイルからの移行または明示的な取り扱いを決める。
5. 既存CSVを入力にした移行テストを追加する。

実データのローテーション、移行、削除は別途承認を得てから実行する。

## 7. WARNING

### W-01: 欠損ゼロの仕様と上限超過破棄の矛盾

対象: [spec:22](../../openspec/specs/iot-data-pipeline/spec.md:22)、[storage_influx.py:45](../../omron_envsensor/storage_influx.py:45)、[design:49](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/design.md:49)

100件を超えた未送信データは最古から破棄される。仕様を「キュー容量以内」と限定するか、CSVからの自動再送または永続スプールを実装する。

### W-02: 復旧Bulk Writeの回帰テスト不足

対象: [tests/test_pipeline.py:124](../../tests/test_pipeline.py:124)

既存テストは送信失敗とキュー上限を検査するが、復旧時の1リクエストBulk Write、部分バケット成功、キューclearを検査しない。独立検証で成立したケースを自動テストへ移す。

### W-03: 同一sequenceの重複保存

対象: [omron_collector.py:94](../../omron_envsensor/omron_collector.py:94)

実機InfluxDBで同じsequenceが約1分間隔で繰り返し保存されている。sequence更新まで抑制するのか、RSSI再サンプリングとして許容するのかを仕様化する。

### W-04: メモリ目標超過

対象: [design.md:10](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/design.md:10)

設計目標15MB以下に対し、実機RSSは17,560KiBだった。測定条件を固定し、目標値または実装を見直す。

### W-05: 認証情報のリポジトリ埋め込み

対象: [storage_influx.py:22](../../omron_envsensor/storage_influx.py:22)、[deploy_qnap.sh:10](../../qnap/deploy_qnap.sh:10)

環境変数対応は追加されたが、実トークン・QNAPパスワードのフォールバックやスクリプト埋め込みが残る。デフォルトを未設定エラーにし、既存資格情報をローテーションする。

### W-06: バケット初期化失敗を隠蔽

対象: [deploy_qnap.sh:41](../../qnap/deploy_qnap.sh:41)

バケット一覧取得と作成が失敗しても `|| true` で成功終了する。作成後に保持期間を再確認し、失敗時は非0終了する。

## 8. SUGGESTION

### S-01: Line ProtocolとCSVのエスケープ

`device_id`、`location`、`gateway`にカンマ、空白、改行が入る場合のエスケープを追加する。

### S-02: Artifact記載の実ファイル名整合

[proposal.md:39](../../openspec/changes/archive/2026-08-24-modern-iot-data-pipeline/proposal.md:39) の `bin/omronService.sh` は実在する `bin/omronCollector.sh` と一致しない。

### S-03: 日次／月次表現の統一

`env_YYYYMM.csv` は月次ファイルであるため、spec・design・運用文書の「日次」表現を月次へ統一する。

## 9. タスク別評価

| タスク | 評価 | 根拠 |
|---|---|---|
| 1.1 | 確認済み | QNAPに365日保持バケットあり |
| 1.2 | 確認済み | UV、DI、熱中症危険度を含むJSONが配備済み |
| 2.1 | 確認済み | dataclassモデルとテスト |
| 2.2 | 確認済み | 正常・異常パーサーテスト |
| 2.3 | 部分確認 | 通常復旧は成立、上限超過は破棄 |
| 2.4 | **不適合** | 実機CSVが11列／15列混在 |
| 2.5 | 確認済み | 実機プロセス稼働、配備ハッシュ一致 |
| 3.1 | 確認済み | Makefileと起動スクリプト |
| 3.2 | 確認済み | 3 Measurement、共通タグ、Fluxクエリを実機確認 |
| 3.3 | 確認済み | update-pizero.md、memo.md更新済み |

## 10. 他AIによる再評価用結論

次の結論を独立に再判定すること。

1. 現行Pi ZeroのCSVは、旧11列と新15列の混在によりCSV永続化要件を満たすか。
2. `deque(maxlen=100)`で上限超過時に破棄する実装は、「データ欠損ゼロ」と両立するか。
3. 既存5テストだけで、specの4シナリオを十分に回帰できるか。
4. 現行アーカイブをクローズ済みとして扱えるか。

## 11. 作業境界

- 読み取り専用レビュー。
- コード変更なし。
- データ変更なし。
- Pi Zeroの停止・再起動なし。
- QNAPの停止・再構成なし。
- commit、pushなし。
- 作業開始時点の未追跡 `.agents/` と `backup/home_pi_full/` を保持。
