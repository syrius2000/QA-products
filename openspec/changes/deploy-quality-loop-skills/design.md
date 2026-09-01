## 背景と制約

動機は[proposal.md](proposal.md)の「背景」を参照する。現行の2つのSkillは、Bundleルートを作業ディレクトリとして`python3 -B -m quality_loop.cli`を実行するよう指示している。一方、Skillディレクトリには`quality_loop`パッケージが含まれず、任意の配置先へSkillだけをコピーするとimportできない。

Python共通基盤は標準ライブラリのみで構成され、開発正本は`quality-loop/quality_loop/`にある。配置先の自動検出やパッケージマネージャーは導入せず、2つのSkillディレクトリをそのままコピー可能な成果物にする。要求契約は[specs/quality-loop-skill-deployment/spec.md](specs/quality-loop-skill-deployment/spec.md)を参照する。

## 目標と対象外

**目標:**

- `quality-review`と`quality-response`をそれぞれ単独で移動可能な配布単位にする。
- 配置先や呼出し時の作業ディレクトリに依存せず、同梱runtimeからCLIを起動する。
- 開発正本と2つの同梱runtimeの対応関係を明確にする。
- Role境界と非発火条件をSkill discovery時点で判別可能にする。
- 同名Skillを保護するFail-Closedな手動配置手順と最小検査を用意する。
- 初見利用者が哲学より先に利用開始手順へ到達できるREADME導線を作る。

**対象外:**

- npm、PyPI、pipxその他のパッケージマネージャーによる配布。
- 配置・更新を自動化するインストーラーまたは同期CLI。
- Quality Loopの状態遷移、Schema、公開CLI、正本形式の変更。
- 自動テストスイートの追加または既存テストの再実行。
- `~/.agents/skills/`や他リポジトリへの実配置、旧版削除、commit、push。

## 設計判断

### 1. 各SkillへPythonパッケージ全体を同梱する

各Skillを次の構造へ統一する。

```text
quality-review/
├── SKILL.md
├── bin/
│   └── quality-review-cli
├── runtime/
│   └── quality_loop/
├── references/
└── evals/

quality-response/
├── SKILL.md
├── bin/
│   └── quality-response-cli
├── runtime/
│   └── quality_loop/
├── references/
└── evals/
```

`runtime/quality_loop/`には`quality-loop/quality_loop/`のPythonソース全体を含める。部分抽出は、間接importの見落としと将来変更時の欠落を招くため採用しない。共有runtimeをSkill外へ一度だけ配置する案は、単独コピー可能性を失うため採用しない。

### 2. 開発正本を一つに保ち、同梱runtimeを配布コピーとして扱う

`quality-loop/quality_loop/`だけを開発正本とする。両Skill内の`runtime/quality_loop/`は編集正本にせず、配布前に正本と一致させる同期対象とする。今回、同期インストーラーは作らず、対象ファイル一覧と比較手順を文書化する。

比較ではPythonソースの相対パスとSHA-256を確認し、`__pycache__`、`.pyc`、テストキャッシュを配布物から除外する。単純なファイル数だけを一致根拠にしない。

### 3. 配置場所基準の薄い実行ラッパーを同梱する

各`bin/<skill>-cli`は自分自身の実パスからSkillルートを解決し、`runtime/`を`PYTHONPATH`の先頭に設定して、次を実行する薄いPOSIX shellラッパーとする。

```text
python3 -B -m quality_loop.cli <利用者引数>
```

ラッパーは引数を変更せず転送し、Quality Loopの状態判断や入力生成を担当しない。Skill本文は開発元のBundleルートへ`cd`せず、このラッパーを明示パスで呼ぶ。PythonパッケージをOS環境へインストールする案は、環境差と更新責務を増やすため採用しない。

### 4. Skill discoveryをRoleと案件条件で限定する

各`SKILL.md`のfrontmatter `description`に、正の発火条件と負の非発火条件を併記する。

- `quality-review`: 明示されたQuality Loop案件、`next_role=reviewer`、`review`／`review-plan`／`verify`／`assess-risk`に限定する。
- `quality-response`: 明示されたQuality Loop案件、`next_role=implementer`、`submit-plan`／`submit-response`に限定する。
- 一般的なコードレビュー、一般的な文章回答、OpenSpec一般、旧spec-driven-qa、Owner裁定、自己クローズは対象外とする。

Skill本文の最初でも`status`によるRole確認を維持し、discoveryの誤選択と実行時の誤操作を二段階で防ぐ。Skill名の変更案は既存利用者の発火名を壊すため採用しない。

### 5. 配置は手動コピー契約とし、衝突時は停止する

グローバル配置は`~/.agents/skills/<skill-name>/`、ローカル配置は`<repo>/.agents/skills/<skill-name>/`とする。両方が存在するときはローカルを優先する運用を明記する。

配置前に対象パスを固定し、配置元と配置先のファイル一覧・SHA-256を比較する。配置先が不存在なら新規コピー可能、同一ならスキップ、差異ありなら停止とする。自動上書き、暗黙のバックアップ、削除は行わない。

### 6. 自動テストではなく最小配置検査を受入Evidenceとする

今回の受入確認は次に限定する。

1. 2つの`SKILL.md`のfrontmatterと発火境界
2. `runtime/quality_loop/`のPythonソース一覧と正本との一致
3. 生成物が配布物に含まれないこと
4. 各ラッパーからの`quality_loop` import
5. 各ラッパーの`--help`起動
6. 想定グローバル／ローカル配置構成の静的確認

実案件のQuality Loop操作や既存unittestは実行しない。未確認項目は`unverified`または`evidence-gap`として残す。

### 7. READMEと専用デプロイガイドを二層化する

ルート`README.md`は入口として簡潔に保ち、冒頭を次の順に再構成する。

1. Quality Loopでできること
2. すぐ使うための配置方法への導線
3. `quality-review`と`quality-response`の選択
4. 最初の案件作成と次Roleへの引き継ぎ
5. 現在の状態、設計思想、評価方法、開発者向け情報

詳細な操作は`quality-loop/SKILL_DEPLOYMENT_GUIDE.md`へ分離し、グローバル／ローカル配置、衝突確認、手動コピー、更新、検査、Rollbackを番号付きのコピー可能な手順で記載する。READMEへ全コマンドを重複させる案は入口を再び長くするため採用しない。専用ガイドだけを追加してREADMEの順序を変えない案は、利用者がガイドへ到達しにくいため採用しない。

## リスクとトレードオフ

- [2つのSkillにruntimeを重複同梱するため容量が増える] → 単独コピー可能性を優先し、正本とのSHA-256比較で一致を管理する。
- [手動同期で片方だけ古くなる可能性がある] → 両Skillのruntime比較を配布前の必須検査にする。
- [ラッパーのパス解決が空白や異なる作業ディレクトリで失敗する] → 自身の配置場所を引用符付きで解決し、呼出し元の作業ディレクトリを参照しない。
- [既存Skillとの名称競合または誤発火] → frontmatterと実行時Role確認の二段階制御、および差異時停止を適用する。
- [ローカル優先規則が実際のエージェント実装で異なる可能性がある] → 配置手順では運用契約として明示し、同時配置を避ける選択肢も示す。動的な優先順位確認が得られない場合は`unverified`とする。
- [最小検査だけでは実案件の全機能を保証しない] → 配置可能性と業務機能の受入を分離し、実案件E2Eを実施したとは報告しない。
- [README再編で現行の状態説明や設計思想が失われる] → 既存内容を削除せず、利用開始セクションの後へ再配置し、正本リンクを維持する。

## 移行計画

1. リポジトリ内で2つのSkillへ同一のPythonソースを同梱し、ラッパーと発火境界を整備する。
2. 専用デプロイガイドを作成し、ルートREADMEを利用優先の入口へ再編する。
3. リポジトリ内だけで最小配置検査を実施し、対象ファイル一覧と結果を記録する。
4. 独立QAで仕様、配布境界、誤発火防止、文書導線、最小検査Evidenceを確認する。
5. Ownerが残余リスクと外部配置可否を裁定する。
6. 別の明示承認後、指定されたグローバルまたはローカル配置先に新規コピーする。
7. 配置後に最小検査を再実行し、問題があれば追加変更せず停止する。

Rollbackは、新規配置した対象が今回のコピーで作成されたことを確認できる場合に限り、その対象だけを復元または削除する。既存Skillを上書きしないため、差異を検出した既存対象にはRollback操作を行わない。
