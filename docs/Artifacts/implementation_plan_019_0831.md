# Quality Loop Skill自己完結配布 実装計画

created: 2026-08-31 23:27 (JST)
update: 2026-09-01 00:20 (JST)
author: Codex (GPT-5)

## 1. 目的

OpenSpec Change `deploy-quality-loop-skills`に従い、`quality-loop`で開発済みの`quality-review`と`quality-response`を、それぞれ単独で`~/.agents/skills/`または任意リポジトリの`.agents/skills/`へコピーして利用できる自己完結したSkillへ整備する。

本計画はリポジトリ内の配布元整備と最小配置検査だけを対象とし、実際のグローバル配置、他リポジトリへの配置、旧版削除、commit、pushは行わない。

## 2. 対象Changeと現在状態

- Change: `deploy-quality-loop-skills`
- Schema: `spec-driven`
- Planning Artifact: `4/4 complete`
- 実装Task: `0/22 complete`
- Capability: `quality-loop-skill-deployment`
- OpenSpec strict validation: 合格

関連文書:

- [Proposal](../../openspec/changes/deploy-quality-loop-skills/proposal.md)
- [仕様](../../openspec/changes/deploy-quality-loop-skills/specs/quality-loop-skill-deployment/spec.md)
- [設計](../../openspec/changes/deploy-quality-loop-skills/design.md)
- [Tasks](../../openspec/changes/deploy-quality-loop-skills/tasks.md)

## 3. 実装対象

### 3.1 `quality-review`

- `quality-loop/skills/quality-review/SKILL.md`
- `quality-loop/skills/quality-review/bin/quality-review-cli`
- `quality-loop/skills/quality-review/runtime/quality_loop/*.py`
- `quality-loop/skills/quality-review/references/`内の自己完結に必要な参照資料

### 3.2 `quality-response`

- `quality-loop/skills/quality-response/SKILL.md`
- `quality-loop/skills/quality-response/bin/quality-response-cli`
- `quality-loop/skills/quality-response/runtime/quality_loop/*.py`
- `quality-loop/skills/quality-response/references/`内の自己完結に必要な参照資料

### 3.3 配置・検査文書とEvidence

- グローバル配置とローカル配置の日本語手順
- 同名Skillの不存在・同一・差異ありを区別するFail-Closed手順
- 開発正本と同梱runtimeの相対パス・SHA-256比較記録
- frontmatter、import、CLI `--help`、想定配置構成の最小検査記録
- 実装報告Artifact

### 3.4 利用者向け文書

- `quality-loop/SKILL_DEPLOYMENT_GUIDE.md`（新規）
- リポジトリルート`README.md`（利用優先の構成へ再編）

## 4. 実装方式

### 4.1 Python共通基盤の同梱

`quality-loop/quality_loop/`を唯一の開発正本とし、そこにあるPythonソース全体を両Skillの`runtime/quality_loop/`へ同一内容で配置する。

同梱対象は`.py`ソースに限定し、次を含めない。

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- テスト生成物
- その他の一時ファイル

正本、`quality-review`同梱runtime、`quality-response`同梱runtimeの3者について、相対パス一覧とSHA-256を比較する。ファイル数だけでは一致と判定しない。

### 4.2 配置場所基準のCLIラッパー

各Skillの`bin/`に薄いPOSIX shellラッパーを追加する。ラッパーは自身の配置場所からSkillルートを解決し、同梱`runtime/`を`PYTHONPATH`の先頭へ設定して、利用者の引数を変更せず次へ渡す。

```text
python3 -B -m quality_loop.cli "$@"
```

Quality Loopの状態判断、JSON生成、Role判定はラッパーへ実装せず、既存CLIとSkill本文の責務として維持する。

### 4.3 参照資料の自己完結化

現行SkillがSkill外の`quality-loop/references/qms-foundations.md`を参照しているため、必要な参照資料を各Skillの`references/`へ同梱し、参照先をSkill内相対パスへ変更する。コピー後に開発元リポジトリへの参照を残さない。

### 4.4 誤発火防止

frontmatterの`description`に正の発火条件と負の非発火条件を併記する。

- `quality-review`: 明示されたQuality Loop案件、`next_role=reviewer`、`review`、`review-plan`、`verify`、`assess-risk`だけを対象とする。
- `quality-response`: 明示されたQuality Loop案件、`next_role=implementer`、`submit-plan`、`submit-response`だけを対象とする。
- 一般レビュー、一般回答、OpenSpec一般、他のQAワークフロー、Owner裁定、自己クローズ、Role外操作を対象外として明記する。

実行時にも既存の`status`確認を維持し、Skill discoveryとCLI実行の二段階で誤操作を防ぐ。

### 4.5 手動配置契約

インストーラー、同期CLI、npm、PyPI、pipxは導入しない。Skillディレクトリ全体を手動コピーする手順を提供する。

配置先に同名Skillがある場合は次のように扱う。

1. 不存在: 新規コピー可能
2. 同一内容: コピーを省略
3. 差異あり: 差分を示して停止し、上書きしない

### 4.6 READMEと専用ガイドの役割分担

ルート`README.md`は、初見利用者が設計思想や開発履歴より先に利用開始手順へ到達できる入口とする。冒頭を次の順に構成し、その後に現在の記載内容を整理して続ける。

1. Quality Loopでできること
2. Skillをグローバルまたはローカルへ配置する入口
3. `quality-review`と`quality-response`の使い分け
4. 最初の案件を開始する最短手順
5. 現在の状態
6. Quality Loopの設計思想
7. 中座・変更観測、他AI評価、開発者向け情報、変更時の注意

詳細手順は`quality-loop/SKILL_DEPLOYMENT_GUIDE.md`へ分離する。同ガイドには次を番号付き、コピー＆ペースト可能、期待結果付きで記載する。

- 前提条件
- グローバル配置とローカル配置の選択基準
- 配置元と配置先の固定
- 同名Skillの衝突確認
- 手動コピー
- 配置後の`--help`とファイル確認
- 開発正本更新後の再コピー判断
- 問題発生時の停止とRollback
- 外部配置、削除、commit、pushの承認境界

## 5. 実装順序

1. 開始時の`git status`、対象ファイル一覧、正本PythonソースのSHA-256を記録する。
2. Python共通基盤と必要な参照資料を両Skillへ同梱する。
3. 各SkillへCLIラッパーを追加し、実行権限を設定する。
4. 2つの`SKILL.md`の発火条件、非発火条件、CLI例、参照先を更新する。
5. 専用デプロイガイドを作成し、ルートREADMEを利用優先の入口へ再編する。
6. グローバル・ローカル配置、衝突保護、runtime更新、最小検査の文書内容を相互確認する。
7. リポジトリ内だけで最小配置検査を実施する。
8. 実装報告を作成し、OpenSpec Taskのうち実際に完了した項目だけを`[x]`へ更新する。
9. 終了時の`git diff`とOpenSpec状態を確認する。

## 6. 検証計画

自動テストスイートと実案件E2Eは実行しない。次の最小配置検査だけを行う。

- 両`SKILL.md`のfrontmatter構文とSkill名
- 正の発火条件と負の非発火条件
- 必須ファイルとSkill内相対参照の存在
- 正本と両同梱runtimeの相対パス・SHA-256完全一致
- 同梱ディレクトリに生成物がないこと
- 開発元Bundleルート外からのruntime import
- 各ラッパーの`--help`
- 空白を含む一時配置パスからのラッパー起動
- グローバル／ローカル配置構成の静的確認
- ルートREADMEから専用デプロイガイド、Quality Loop README、機能仕様、Templateへの相対リンク確認
- 専用デプロイガイドのコマンド、期待結果、衝突時停止、承認境界の確認
- `openspec validate deploy-quality-loop-skills --strict`
- `git diff --check`

動的なSkill発火選択、実案件の状態遷移、グローバルとローカルが同時存在する場合の実際の優先順位は、今回確認できなければ`unverified`または`evidence-gap`として残す。

## 7. 受入条件

- `quality-review`と`quality-response`が、それぞれ単独コピー可能なディレクトリ構成を持つ。
- 各Skillの同梱runtimeが開発正本と完全一致する。
- ラッパーが呼出し元の作業ディレクトリに依存せず同梱CLIを起動する。
- Skill外のPythonパッケージと参照資料を要求しない。
- 一般レビュー、一般回答、OpenSpec一般、他QAとの誤発火を抑える境界が明記される。
- 同名Skillを明示承認なしに上書きする手順が存在しない。
- ルートREADMEの冒頭から利用開始、Skill選択、案件開始へ進める。
- 専用デプロイガイドだけで手動配置、検査、更新、Rollback判断を行える。
- README再編後も現在状態、設計思想、評価・開発情報、正本リンクが保持される。
- 最小配置検査の結果と未検証事項が区別して記録される。
- リポジトリ外、他リポジトリ、旧版、commit、pushを変更していない。

## 8. Rollback境界

実装中のRollbackは、この実装ラウンドで追加または変更した次の対象だけに限定する。

- 2つのSkill内に新規追加した`bin/`、`runtime/`、参照資料
- 2つの`SKILL.md`に対する今回の変更
- 今回新規作成する配置手順、Evidence、実装報告
- 今回新規作成する`quality-loop/SKILL_DEPLOYMENT_GUIDE.md`
- ルート`README.md`に対する今回の再編変更
- 今回更新するOpenSpec Taskチェック

作業開始前から存在するユーザー変更、他Change、既存QA記録、案件正本を復元・削除しない。ファイル全体の復元が必要な場合は、今回の変更だけを破棄できることを確認してから実施する。

## 9. 明示的な非対象

- `~/.agents/skills/`への実コピー
- 他リポジトリの`.agents/skills/`への実コピー
- Quality LoopのSchema、状態遷移、公開CLI契約の変更
- 外部Python依存の追加
- インストーラーまたは同期CLIの開発
- 自動テストスイートまたは実案件E2Eの実行
- 旧Skillの削除・上書き
- OpenSpec ChangeのArchive
- commit、push、deployment

## 10. 承認境界

本計画書の作成、読み取り専用調査、差分確認は実装に含めない。本計画の内容に対するユーザーの明示承認を得るまで、`quality-loop/skills/`、`quality-loop/quality_loop/`その他の実装対象を変更しない。

本計画の承認はリポジトリ内の配布元整備、専用デプロイガイド、ルートREADME再編、最小配置検査だけに有効であり、グローバル配置、他リポジトリへの配置、旧版削除、commit、pushを許可しない。

2026-08-31 23:47 (JST)にユーザーから手動デプロイ文書とルートREADMEの利用優先化が追加要望されたため、本計画を更新した。追加範囲を含むPlan 019への再承認後に実装を開始する。

2026-09-01 00:20 (JST)に、ユーザーから更新版Plan 019の明示承認を得た。承認範囲は本計画に記載したリポジトリ内の配布元整備、専用デプロイガイド、ルートREADME再編、最小配置検査に限定する。
