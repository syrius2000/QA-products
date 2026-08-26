# 証拠台帳

この台帳は、QA-0001の再現可能な観測結果を要約する。秘密情報、トークン、パスワードは記録しない。

## EV-LOCAL-TEST-01

- 実行: `python3 -m unittest -v tests/test_pipeline.py`
- 結果: 4 tests / 4 passed。CSV旧11列移行、Line Protocol/CSVエスケープ、モックHTTP Bulk Write復旧とキューclearを含む。
- 分類: `CONFIRMED`（実行済みテスト）。実InfluxDBではなくローカルモック。

## EV-LOCAL-SYNTAX-01

- 実行: `PYTHONPYCACHEPREFIX=/private/tmp/raspi-qa-pycache python3 -m compileall -q omron_envsensor tests; bash -n qnap/deploy_qnap.sh`
- 結果: 成功。作業後に一時pycacheは削除した。
- 分類: `CONFIRMED`。

## EV-OPENSPEC-01

- 実行: `openspec validate --all --json`
- 結果: main spec 3件、passed 3、failed 0。アーカイブ済みchangeはactive changeとして列挙されない。
- 分類: `CONFIRMED`。構文・構造の検証であり実装完了の証明ではない。

## EV-PI-CODE-01

- 実行: `ssh -o BatchMode=yes pi@raspberryZERO.local`で対象ファイルのSHA-256を取得。
- 結果: Pi上`storage_csv.py`=`5a9f765d...372e13`、`omron_collector.py`=`fa79e8d...31ed8`。同じハッシュがローカルにも存在。
- 分類: `CONFIRMED`（配備コード同一性）。ハッシュは秘密情報を含まない。

## EV-PI-CSV-01

- 実行: Pi上の`data/env_202608.csv`を読み取り、ヘッダー列数・全データ列数・sequence集計をawkで確認。
- 結果: ヘッダー15列、データ176行、不正行0。`env_202608.csv.bak`は移行前11列ヘッダー・173行。
- 追加観測: CSV全体のSeq 0は98行。プロセス起動時刻（21:31:35）後にSeq 178が21:32:06に記録され、起動前の21:30:07にも同じSeq 178が存在する。再起動境界のdedup永続化は確認できない。
- 分類: `CONFIRMED`（実機読み取り）。CSV全体の重複には移行前履歴が含まれるため、F02は再起動境界の時系列証拠に限定している。

## EV-PI-RUNTIME-01

- 実行: Pi上`ps`、`collector.log`、`/proc/meminfo`を読み取り。
- 結果: `omron_collector.py`稼働、RSS 17,424 KiB。起動後ログはSeq 178、179、180を各1回処理。
- 分類: `CONFIRMED`（実機ランタイム）。停止・再起動は行っていない。

## EV-QNAP-HEALTH-01

- 実行: `curl --max-time 5 http://192.168.0.110:8086/health`およびGrafana `/api/health`、PiからのTCP接続確認。
- 結果: InfluxDB HTTP 200 / `pass` / v2.7.12、Grafana HTTP 200、Piから8086/3000接続成功。
- 分類: `CONFIRMED`（疎通）。バケット保持期間とデータ値の再検証は今回の対象外。

## EV-CREDENTIAL-01

- 対象: `omron_envsensor/storage_influx.py:18-22`、`qnap/deploy_qnap.sh:8-18,41-52`、`qnap/docker-compose.yml:18-25,40-43`。
- 結果: 環境変数参照はあるが、認証情報の直書きまたは安全でないフォールバックが残る。値は本台帳に記録しない。
- 分類: `CONFIRMED`（コード読解）。実運用での有効性・ローテーション状態は未確認。

## EV-VERIFICATION-LOCAL-01

- revision: `8a8770480aad7d939ec03ecca835e7c8720b97ed`
- 実行: `PYTHONPYCACHEPREFIX=/private/tmp/... python3 -m unittest -v tests/test_pipeline.py`
- 結果: 7 tests / 7 passed。F01 fail-closed、F02 CSV sequence復元、F03 MAC単位dedupテストを含む。
- 追加検証: `python3 -m compileall -q omron_envsensor tests`も一時pycache出力先で成功。
- 分類: `CONFIRMED`（実行済みテスト）。test_06は復元mapの取得を検査するが、新Delegate再生成後の同一sequence抑止そのものは単独では検査しない。

## EV-VERIFICATION-PI-01

- 実行: `raspberryZERO.local`へ読み取り専用SSHし、配備ハッシュ、プロセス、collector.log、CSVを確認。
- 結果: Pi上の`storage_influx.py`、`storage_csv.py`、`omron_collector.py`のSHA-256がrevision `8a87704`のローカル実装と一致。
- 実機ログ: 21:53:55に`omron-01 -> Seq 182`のdedup状態復元を記録し、その後Seq 183〜186を各1回処理。
- CSV: ヘッダー15列、データ182行、不正列0、Seq 182〜186は各1行。
- 分類: `CONFIRMED`（実機読み取り）。停止・再起動の操作は行っていない。

## EV-VERIFICATION-AUTH-01

- F01変更の確認: `storage_influx.py`のtoken未設定時fail-closedと`test_05_auth_fail_closed`は実装・実行とも確認。
- 未解消: `omron_collector.py`のCLI token default、QNAPデプロイスクリプト、Docker Compose、その他の資格情報直書きは残存。
- 運用制約: Pi上の`/home/pi/.iot_env`とcollectorディレクトリの`.env`は存在しなかった。起動ラッパーは環境変数をsourceするが、sudo越しに全変数が保持されることをコードだけでは保証できない。
- 分類: `CONFLICT`。部分修正は確認できるが、F01要求「全資格情報の外部化・未設定時fail-closed」は未達。

## EV-VERIFICATION-F02-F03-01

- F02: CSVからの直近sequence復元コード、7件テスト、Pi起動ログの三者が整合。
- F03: MACをdedup keyとするコードと異なるMAC・同一sequenceのテストが整合。
- 分類: `CONFIRMED`（F02/F03は今回revisionでfixed-and-verified）。複数センサーの再起動復元は未検証の残余リスク。

## EV-VERIFICATION-CYCLE2-01

- reviewed revision: `3b8f5d23d1150ff4bc87eb0a2bf2ec6724f4dcd3`
- 実行: `python3 -m unittest -v tests/test_pipeline.py`、`bash -n qnap/deploy_qnap.sh bin/omronCollector.sh`、資格情報未設定の`deploy_qnap.sh status`読み取り専用プローブ。
- 結果: Python 7件成功、シェル構文成功、`QNAP_PASS`または`INFLUXDB_TOKEN`未設定時は終了コード1。Docker CLIはローカル環境にないためComposeの実展開は未実施。
- コード照合: Collector CLIのtoken既定値撤廃は確認できたが、`qnap/deploy_qnap.sh:74-76`に固定資格情報の表示が残り、`INFLUXDB_PASSWORD`／`GRAFANA_PASSWORD`の事前検証がない。`bin/omronCollector.sh`とSSHデプロイ経路は秘密値をコマンド文字列へ展開する。
- 分類: `CONFIRMED`（ローカルコード・テスト・失敗経路）。Pi上のCycle 2起動ログと資格情報ローテーションは`AUTHOR-CLAIM`／`UNVERIFIED`として扱う。秘密値は記録していない。

## EV-VERIFICATION-CYCLE3-01

- reviewed revision: `0088b8c256878aff4e58ea9b474538693f4d93fa`
- 実行: `python3 -m unittest -v tests/test_pipeline.py`（7件成功）、`bash -n qnap/deploy_qnap.sh bin/omronCollector.sh bin/NASmount.sh bin/qnap1`（成功）、4段階の未設定環境fail-closedプローブ。
- 確認: QNAP／InfluxDB／Grafana必須変数の事前検証、固定認証情報表示の除去、Collector launcherのinline token展開除去。
- 未解消: `qnap/deploy_qnap.sh`の`echo '${QNAP_PASS}' | sudo -S`、`NASmount.sh`のmount password引数、`qnap1`のexpect password展開、`.iot_env` mode 600のコード上未検証。ShellCheck SC2029も残存。
- 分類: `CONFIRMED`（ローカルコード・テスト・静的検証）。QNAP／Pi実機の成功状態と資格情報ローテーションは`AUTHOR-CLAIM`／`UNVERIFIED`。秘密値は記録していない。
