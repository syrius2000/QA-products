# インストール

このディレクトリをエージェント環境のSkillルートへ配置し、同じルートに`spec-driven-qa-review`を配置してください。

例:

```text
.agents/skills/spec-driven-qa-review/
.agents/skills/spec-driven-qa-author-response/
```

回答対象のQAケースはプロジェクト側の`docs/ADR/QA/`に置きます。実行時はPython 3.10以上の標準ライブラリだけを使用します。開発・テスト時のみ`pyyaml`を追加できます。
