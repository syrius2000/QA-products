# Quality Loop Skill手動配置ガイド

`quality-review`と`quality-response`を、グローバルまたは指定したリポジトリだけで利用するための手動コピー手順です。インストーラー、npm、PyPI、pipxは使用しません。

## 1. このガイドで行うこと

このガイドは、完成済みのSkillディレクトリをコピーして使う手順です。コピー元は、このリポジトリ内の次の2ディレクトリです。

```text
quality-loop/skills/quality-review/
quality-loop/skills/quality-response/
```

各ディレクトリには`SKILL.md`、`runtime/quality_loop/`、`bin/`、必要な`references/`が含まれます。コピー後に開発元リポジトリのPythonパッケージを参照する必要はありません。

実際のグローバル配置、他リポジトリへの配置、既存Skillの上書き、削除は、対象パスを特定した明示承認が必要です。このガイド自体は承認を代行しません。

## 2. 配置先を選ぶ

| 利用目的 | 配置先 | 使う場面 |
| --- | --- | --- |
| 複数リポジトリで共通利用 | `~/.agents/skills/` | 個人環境の共通Skillとして使う |
| 1つのリポジトリだけで利用 | `<対象リポジトリ>/.agents/skills/` | プロジェクト固有のSkillとして使う |

グローバルとローカルの両方に同名Skillを置く場合は、ローカルを優先する運用とします。ただし、実行環境が実際にどちらを優先するかは環境ごとの確認が必要であり、確認できない場合は`unverified`です。同じSkillを二重配置する必要がなければ、用途に合う片方だけを選んでください。

## 3. 配置前に確認する

以下は、このリポジトリのルートで実行します。`DEPLOY_TARGET`は実際の配置先へ置き換えてください。

```bash
SOURCE_SKILLS_DIR="$(pwd)/quality-loop/skills"
DEPLOY_TARGET="$HOME/.agents/skills"

for skill_name in quality-review quality-response; do
  if [ -e "$DEPLOY_TARGET/$skill_name" ]; then
    echo "停止: 既存Skillあり: $DEPLOY_TARGET/$skill_name"
  else
    echo "配置可能: $DEPLOY_TARGET/$skill_name"
  fi
done
```

期待結果は、両方について`配置可能`です。`停止: 既存Skillあり`が1件でも表示された場合はコピーしません。既存内容とコピー元の差分を確認し、同一なら配置を省略し、差異があれば上書きせずに停止してください。

同一性を確認するには、対象Skillごとに次を実行します。

```bash
diff -qr "$SOURCE_SKILLS_DIR/quality-review" "$DEPLOY_TARGET/quality-review"
diff -qr "$SOURCE_SKILLS_DIR/quality-response" "$DEPLOY_TARGET/quality-response"
```

出力がない場合だけ内容は同一です。差分が出た場合は、対象、差分、必要な更新内容を確認してから別途承認を得てください。

## 4. グローバルへ新規コピーする

前節で両Skillが不存在であることを確認し、グローバル配置の明示承認を得た場合だけ、次を実行します。

```bash
SOURCE_SKILLS_DIR="$(pwd)/quality-loop/skills"
GLOBAL_SKILLS_DIR="$HOME/.agents/skills"

mkdir -p "$GLOBAL_SKILLS_DIR"
cp -R "$SOURCE_SKILLS_DIR/quality-review" "$GLOBAL_SKILLS_DIR/quality-review"
cp -R "$SOURCE_SKILLS_DIR/quality-response" "$GLOBAL_SKILLS_DIR/quality-response"
```

期待結果は、次の2ディレクトリが新規に作成されることです。

```text
~/.agents/skills/quality-review/
~/.agents/skills/quality-response/
```

## 5. 指定リポジトリへ新規コピーする

前節で対象リポジトリと両Skillの不存在を確認し、ローカル配置の明示承認を得た場合だけ、`TARGET_REPO`を実パスへ置き換えて次を実行します。

```bash
SOURCE_SKILLS_DIR="$(pwd)/quality-loop/skills"
TARGET_REPO="/absolute/path/to/target-repository"
LOCAL_SKILLS_DIR="$TARGET_REPO/.agents/skills"

mkdir -p "$LOCAL_SKILLS_DIR"
cp -R "$SOURCE_SKILLS_DIR/quality-review" "$LOCAL_SKILLS_DIR/quality-review"
cp -R "$SOURCE_SKILLS_DIR/quality-response" "$LOCAL_SKILLS_DIR/quality-response"
```

期待結果は、次の2ディレクトリが対象リポジトリ内に新規に作成されることです。

```text
<対象リポジトリ>/.agents/skills/quality-review/
<対象リポジトリ>/.agents/skills/quality-response/
```

## 6. コピー後の最小検査

`SKILL_ROOT`を実際にコピーした`quality-review`または`quality-response`の絶対パスへ置き換えます。両Skillについて実行してください。

```bash
SKILL_ROOT="/absolute/path/to/quality-review"
test -f "$SKILL_ROOT/SKILL.md"
test -d "$SKILL_ROOT/runtime/quality_loop"
test -x "$SKILL_ROOT/bin/quality-review-cli"
"$SKILL_ROOT/bin/quality-review-cli" --help
```

`quality-response`では末尾を`quality-response-cli`へ置き換えます。期待結果は、各`test`が終了コード0となり、`--help`がQuality Loop CLIの使用方法を表示することです。

さらに、同梱runtimeが開発正本と同一であることを確認します。

```bash
SOURCE_RUNTIME="$(pwd)/quality-loop/quality_loop"
COPIED_RUNTIME="/absolute/path/to/quality-review/runtime/quality_loop"
diff -qr -x '__pycache__' -x '*.pyc' -x '.pytest_cache' "$SOURCE_RUNTIME" "$COPIED_RUNTIME"
```

出力がない場合だけ、配布対象のPythonソースが同一です。`__pycache__/`、`*.pyc`、`.pytest_cache/`は比較対象から除外していますが、コピー先にこれらの生成物が含まれている場合は、配布可能と判定せずに停止してください。

## 7. 開発正本を更新した後

開発正本`quality-loop/quality_loop/`を変更した場合は、先にリポジトリ内の2つの同梱runtimeを正本と一致させ、相対パスとSHA-256を比較します。その後、既存のグローバル・ローカル配置先には自動反映しません。

配置先が同一なら更新不要です。差異がある場合は、差分の内容と対象パスを示して別途承認を得るまで上書きしません。

## 8. 問題時の停止とRollback

次のいずれかを検出した場合は、追加コピーや上書きを行わず停止してください。

- 同名Skillが既に存在し、コピー元と差異がある
- `SKILL.md`、`runtime/quality_loop/`、`bin/`が欠けている
- ラッパーの`--help`が失敗する
- Pythonソースの差分または生成物を検出する
- 配置対象または承認範囲が不明である

今回新規に作成したコピーだけを取り消す必要がある場合も、対象パスと作成時の記録を確認し、削除実行の明示承認を得てから行ってください。既存Skillを上書きしない設計のため、差異を検出した既存SkillにRollback操作は行いません。

## 9. 次にSkillを使う

- Reviewer工程は`quality-review`を使い、最初に`status`で`next_role=reviewer`を確認します。
- Implementer工程は`quality-response`を使い、最初に`status`で`next_role=implementer`と対象`next_action`を確認します。
- 実案件の作成と公開CLIの詳細は[Quality Loop README](README.md)および[機能仕様](FUNCTIONAL_SPEC.md)を参照してください。
