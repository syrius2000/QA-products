# 共有Bundle

このBundleは外部Skill配置前の検証用ステージング成果物である。ReviewerとAuthorは役割別Launcherを持ち、契約・認可・Manifest検証は`shared_core`へ集約する。

Launcherは自身の実ファイル位置からBundleルートを決定し、Manifestに記載されたファイルのSHA-256を検証する。検証失敗時は標準エラーへ構造化診断を返し、終了コード2で停止する。外部配置先への書込みは行わない。

導入手順は[INSTALL.md](INSTALL.md)、変更履歴は[CHANGELOG.md](CHANGELOG.md)、差分評価は`../scripts/compare_versions.py`、サイズ評価は`../scripts/measure_size.py`を参照する。
