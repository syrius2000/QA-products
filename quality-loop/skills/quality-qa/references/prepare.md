# 依頼を準備する

最初に親SkillのPhase 0に従ってread-only Git preflightを実施する。対象DIRのGit、README、適用AGENTSを読み、目的、利用前提、全受入基準、製品対象、必須／任意検証、QA方式を整理する。取得済み情報を聞き直さず、不足・曖昧な点だけ確認する。dirty checkoutを自動cleanにせず、今回対象・無関係・不明を分類する。対象はファイル単位に展開し、通常は現在の製品内容を対象にする。

内部操作例:

```text
quality-qa-cli prepare --purpose "依頼の目的" --criterion "観察できる受入基準" --target src/product.py --implementer 実装チャットの識別 --author "実際のツール (モデル名)" --audience cloud
```

`--criterion`、`--target` は必要数指定する。実行確認は一意ID・種類・必須性・argv配列・cwd・明示env・timeout・期待終了codeを持つJSONとして `--check-json` に渡す。shell command文字列は使わない。例: `--check-json '{"id":"CHECK-PYTEST","type":"command","required":true,"argv":["python","-m","pytest","tests"],"cwd":"quality-loop","env":{"PYTHONDONTWRITEBYTECODE":"1"},"timeout_seconds":600,"expected_exit_codes":[0]}'`。`--assumptions` は利用前提、`--baseline` は明示された開始点。既存commitだけをレビューする合意がある場合だけ `--reviewed <完全SHA>` を使い、追加のローカル差分が対象外であることを示す。

差分に未分類のファイルがあれば製品対象へ追加するか、理由を確認して `--exclude PATH=理由` を記録する。運用成果物の登録はruntimeが行う。同じDIRの製品要件書をまとめて除外しない。改名は旧・新パスの両方を分類する。

ローカルQAは `--audience local`。別担当へ渡し、pushは行わない。クラウドはGitHubの固定対象と依頼本文を読み、指定したMarkdown一つだけを書く。依頼ID、基準、対象、初回要件、製品／運用集合、前回指摘、保存先、記載例は生成された依頼に含まれる。

下書きの `reviewed` は未確定。正式手渡しと結果取込へ進めず、[対象確定](publish.md)を案内する。確定済みなら生成した文書の本文を示す。クラウド公開の指示がある場合だけ公開へ進める。AIの起動・送信はユーザーが行う。
