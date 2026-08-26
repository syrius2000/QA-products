# Task 6.4 配備準備Evidence

created: 2026-08-26 09:11 (JST)
update: 2026-08-26 09:11 (JST)
author: Codex (GPT-5)

## 実施範囲

Contract v1.2 Candidate stageを一時sandboxへ配置する想定で、次を検証した。

- dry-run計画
- 差分表示
- backupとbackup-manifest.json
- rollback dry-run
- 厳密なtarget確認付きrollback実行
- 既存Skill・グローバルSkillを変更しないこと

実際の`~/.gemini/config/skills/`、`~/.agents/skills/`、`~/.codex/skills/`への書込みは行っていない。

## 実装

- [deploy_tool.py](../stage/deploy_tool.py)
- [test_deploy_tool.py](../stage/test_deploy_tool.py)
- [DEPLOYMENT.md](../stage/DEPLOYMENT.md)

`deploy_tool.py`は、cache/bytecodeを配布計画から除外し、既存backupを上書きせず、rollback実行時に明示的な絶対パス確認を要求する。backupの監査Manifestと復元payloadは別に保存する。

## 検証結果

### pytest

既存78件に配備ツールの3件を加え、次の結果を得た。

```text
81 passed in 0.19s
exit code: 0
```

### sandbox CLI

- `plan --json`: `dry-run`、130件の追加差分を検出
- cache/bytecode: 計画結果への混入なし
- `diff`: 214,533 bytesの差分表示を生成
- `backup`: `COMPLETE`、`backup-manifest.json`生成
- `rollback`既定: `DRY-RUN`、target変更なし
- `rollback --apply --confirm-target`: `COMPLETE`
- 復元前のtarget退避: `.pre-rollback-<id>`を生成
- rollback確認用の一時marker: 復元後に除去

機械可読な記録は[deployment-dry-run-20260826.json](deployment-dry-run-20260826.json)に保存した。

## 残余リスク

- 実グローバルSkillへの配備は行っていない。
- 本番環境の権限、容量、同時実行、ユーザー承認は未検証である。
- stage内には既存の`.pytest_cache`、`__pycache__`、`.pyc`が残っているため、配布前のBundle ValidatorとManifest除外確認が必要である。

## 判定

Task 6.4の「stageからのdry-run、差分表示、backup、rollback手順を作成し、既存Skillへ変更を加えずに再現できること」は完了とする。

Task 6.3（比較Evidenceの未検証項目）とTask 6.5（実装・評価・配備差分の最終記録、明示承認）は未完了のまま保持する。
