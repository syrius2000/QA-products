# Tasks

## 1. 配備契約と対象の固定

- [x] 1.1 proposal、spec delta、design、tasksを整え、Ownerの今回の3パス配置指示とQA-0008残余リスクを分離したauthorization evidenceを保存して検証する
- [x] 1.2 `quality-qa`、`quality-review`、`quality-response`のsource file list、VERSION、file mode、SHA-256 manifestを作成し、必要パーツとCLI `--help`を確認する
- [x] 1.3 `~/.agents/skills/`の実体、3配置先の不存在、既存`blind-qa-cycle`のSHA-256をbackup/inventory evidenceへ記録し、既存パスが1件でもあれば停止する

## 2. 配置手順と一時検証

- [x] 2.1 READMEとSkill配置ガイドを3 Skillの用途、必要パーツ、対象パス、衝突停止、検査、rollbackに更新し、記載コマンドとファイル一覧を照合する
- [x] 2.2 一時領域へ3 Skillをコピーし、source/stageのpath・file type・mode・サイズ・SHA-256一致とCLI `--help`を検証して結果を記録する
- [x] 2.3 一時領域だけにrollbackを実行し、stageが消え、グローバルbaselineと既存`blind-qa-cycle`が不変であることを確認する

## 3. 対象限定グローバル配置

- [x] 3.1 配置直前に対象3パスが不存在であることとsource manifest一致を再検査し、`~/.agents/skills/quality-qa/`、`quality-review/`、`quality-response/`だけへ新規コピーする
- [x] 3.2 配置後のfile list、mode、SHA-256、必須ファイル、CLI `--help`を検査し、既存`blind-qa-cycle`と他のSkillが不変であることを記録する
- [x] 3.3 OpenSpec strict validation、`git diff --check`、repo statusを確認し、外部配置・旧版削除・commit・pushの実績と残余リスクを報告する

## Workflow follow-up

- archive the change after required review and Owner closure are recorded.
