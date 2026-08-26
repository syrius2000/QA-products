# ステージング配備手順

この手順は、Contract v1.2候補Bundleを本番Skillへ配置せず、dry-run、差分、backup、rollbackを検証するためのものである。

## 安全境界

- 既定操作はdry-runであり、Candidate Bundleや既存Skillを変更しない。
- `target`と`backup`は明示した絶対パスだけを使う。
- ホームディレクトリ、その親、ルートディレクトリは対象にできない。
- backupは既存ディレクトリを上書きしない。
- rollbackの実行には、対象絶対パスと一致する`--confirm-target`が必要である。
- 実際のグローバルSkill配備はTask 6.5以降の別承認対象であり、この手順では実施しない。

## dry-runと差分

一時ディレクトリを対象に、Candidate Bundleの計画をJSONで確認する。

```bash
python3 stage/deploy_tool.py plan \
  --source stage \
  --target /private/tmp/qa-skill-target
```

差分だけを表示する。

```bash
python3 stage/deploy_tool.py diff \
  --source stage \
  --target /private/tmp/qa-skill-target
```

Manifest、cache、bytecodeを配布対象から除外し、追加・置換・削除・変更なしを記録する。

## backup

既存のsandbox targetを明示的なbackup先へ保存する。

```bash
python3 stage/deploy_tool.py backup \
  --target /private/tmp/qa-skill-target \
  --backup /private/tmp/qa-skill-backup-YYYYMMDD-HHMM
```

成功時はbackup先に`backup-manifest.json`を保存する。片側保存やManifest保存に失敗した場合はexit code 2で停止し、既存targetを変更しない。

## rollback dry-run

```bash
python3 stage/deploy_tool.py rollback \
  --target /private/tmp/qa-skill-target \
  --backup /private/tmp/qa-skill-backup-YYYYMMDD-HHMM
```

既定では`DRY-RUN`だけを返し、targetを変更しない。

## rollback実行（sandbox検証専用）

```bash
python3 stage/deploy_tool.py rollback \
  --target /private/tmp/qa-skill-target \
  --backup /private/tmp/qa-skill-backup-YYYYMMDD-HHMM \
  --apply \
  --confirm-target /private/tmp/qa-skill-target
```

実行時は現在のtargetを`.pre-rollback-<id>`へ退避してから、backupを同一親ディレクトリ内の一時ディレクトリ経由で復元する。復元に失敗した場合は新しい変更を停止し、一時ディレクトリを残さない。

## 検証コマンド

```bash
cd openspec/changes/improve-spec-driven-qa-contract-v1-2/stage
/Users/myamaguchi/.local/venvs/ide/bin/python -B -m pytest \
  --assert=plain -p no:cacheprovider -q \
  spec_driven_qa_reviewer/tests \
  spec_driven_qa_author_response/tests \
  test_deploy_tool.py
```

この検証はsandbox内だけでbackupとrollbackを実行する。グローバルSkillパスへの書込みを含まない。
