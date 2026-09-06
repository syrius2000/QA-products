# Bundle導入手順

このBundleはまずstagingで検証する。Launcherを実行する前に`MANIFEST.json`のdigest検証を通すこと。外部Skill配置先へのコピー、旧版削除、commit、pushは別途明示承認が必要である。

互換確認には標準ライブラリ入口を使用し、未知major、Manifest不整合、共有コア欠落は成功扱いにしない。
