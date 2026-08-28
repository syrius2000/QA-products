# Quality Loop

人間Owner、Reviewer、Implementerが、FindingとEvidenceを使って改善を前進させる最小QMS協働ループです。

## 公開操作

公開する操作は次の6つだけです。

1. `create-case`
2. `review`
3. `submit-response`
4. `verify`
5. `adjudicate`
6. `status`

詳細な契約は[機能仕様](FUNCTIONAL_SPEC.md)を参照してください。

## 最初の案件を開始する

`create-case`には、Owner、案件ID、Purpose、要求、受入基準、対象成果物、対象revisionが必要です。`actor_id`と`owner`は同じOwner識別子にします。最小入力は[templates/intake.json](templates/intake.json)から作成できます。

```bash
cd quality-loop
cp templates/intake.json create-case.json
# create-case.jsonのcase_id、owner、baselineを対象案件に合わせて更新する
python3 -B -m quality_loop.cli --case-root ../qms-cases create-case --input create-case.json
```

成功時のJSONにある`next_role`、`next_action`、`handoff`を次工程へ渡します。案件正本`case.json`は直接編集しません。

## 開発時の実行

```bash
cd quality-loop
python3 -B -m unittest discover -s tests -v
python3 -B -m quality_loop.cli --help
```

Python標準ライブラリだけを使用します。旧OpenSpec実装や旧Skillコードはimportしません。

## AI Skill

- `skills/quality-review/`: 初回レビューと修正後の独立検証
- `skills/quality-response/`: Finding回答と許可範囲内の修正提出

どちらも最初に`status`を確認し、CLIが返した次Roleとhandoffを次工程へ渡します。Skillは案件正本`case.json`を直接編集しません。
