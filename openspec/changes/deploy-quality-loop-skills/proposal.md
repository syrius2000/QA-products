## 背景

`quality-loop`で開発済みの`quality-review`と`quality-response`は、現在のディレクトリ構成と作業ディレクトリを前提に`quality_loop` Python共通基盤を呼び出しており、Skillディレクトリだけをグローバルまたは別リポジトリへコピーしても利用できない。2つのSkillを自己完結した配布単位へ整え、任意の対象へ安全にコピーして利用できる契約が必要である。

## 変更内容

- `quality-review`と`quality-response`の各Skillに、`quality_loop` Pythonパッケージ全体と配置場所基準のCLI実行ラッパーを同梱する。
- 各Skillを`~/.agents/skills/`または指定リポジトリの`.agents/skills/`へ単純コピーして利用できるようにする。
- `quality-loop/quality_loop/`を開発正本とし、各Skillの同梱runtimeを同期対象として扱う。
- 同名Skillが存在する場合は、同一内容なら配置を省略し、差異があれば上書きせず停止する配置契約を定義する。
- Reviewer／ImplementerのRole境界、案件条件、非発火条件を強化し、他のレビュー・回答Skillとの誤発火を抑止する。
- 手動コピー、更新、衝突確認、最小検査、Rollbackを説明する専用デプロイガイドを整備する。
- ルート`README.md`を「使い方から始まり、現在の状態、設計思想、評価上の注意へ続く」利用優先の構成へ再編する。
- 自動テストスイートは追加せず、frontmatter、同梱runtime、import、CLI起動、配置先構成を確認する最小検査を定義する。
- 実際のグローバル配置、他リポジトリへの配置、旧版削除、commit、pushはこのChangeの実装対象外とする。

## 機能契約（Capability）

### 新規Capability

- `quality-loop-skill-deployment`: Quality LoopのReviewer／Implementer Skillを、Python共通基盤込みの自己完結した配布単位としてグローバルまたはリポジトリローカルへ安全に配置し、利用可能性と誤発火防止を確認する契約。

### 変更対象Capability

なし。

## 影響範囲

- 対象: `quality-loop/skills/quality-review/`、`quality-loop/skills/quality-response/`、`quality-loop/quality_loop/`、`quality-loop/SKILL_DEPLOYMENT_GUIDE.md`、ルート`README.md`、配置・検査手順文書。
- 公開操作: 各Skillに同梱するCLI実行ラッパーと、Skill本文に記載する呼出し方法。
- 依存関係: Python標準ライブラリのみを維持し、新規外部依存は追加しない。
- 配置先: 将来の明示承認後に`~/.agents/skills/`または`<repo>/.agents/skills/`を使用するが、このChange内では外部配置しない。
- 互換性: Quality Loopの既存CLI契約とRole分離を変更せず、配布形態のみを追加する。
