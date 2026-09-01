# QA-products配布・開発分離整理計画

created: 2026-09-01 21:42 (JST)
update: 2026-09-01 22:51 (JST)
author: Codex (GPT-5)

## 1. 目的

QA-productsを、Quality Loopの開発正本・検証・開発経緯の保存場所として整理する。実務者向けの利用成果物は、別リポジトリであるProductivity-Skillへ確定版だけを取り込み、利用者がclone後にそのまま使える構造にする。

## 2. 対象リポジトリと役割

### QA-products

- Quality Loopの開発正本を保持する。
- 開発用Skill、Python runtime、Schema、Template、examples、テスト、仕様、QA記録を必要な範囲で保持する。
- 開発史を`docs/Archives/history/`、設計判断を`docs/Archives/decisions/`へ整理する。
- 成果物同期およびruntime同一性検査のスクリプトを`scripts/`に置く。
- 利用成果物の同期記録、コミット、タグ、SHA-256を開発側で管理する。

### Productivity-Skill

- 実務者が利用する成果物だけを保持する。
- `.agents/skills/quality-review/`と`.agents/skills/quality-response/`をリポジトリ直下に置く。
- QA-productsの開発史、設計判断、同期スクリプト、内部QA資料は取り込まない。
- clone直後にプロジェクト内Skillとして利用できる状態にする。
- 必要な利用者だけが、2つのSkillを`~/.agents/skills/`へコピーできるようにする。

## 3. 実施内容

### 3.1 現行構造とリンクの棚卸し

- 作業開始時点のGit差分、tracked/untrackedファイル、対象ディレクトリを記録する。
- `quality-loop/`、`archives/`、`docs/Archives/`、`openspec/`、`qms-cases/`、`improve-contract-evidence/`の用途とリンクを確認する。
- 正本、重複、作業途中資料、旧QA、完了済み計画、実装報告、原本アーカイブを分類する。
- 移動・削除候補一覧を作成し、移動前後の相対リンクを確認する。

### 3.2 QA-products READMEの再構成

- README冒頭で、QA-productsは開発・検証・履歴保存用であり、利用成果物はProductivity-Skillにあることを明示する。
- Quality Loopの成果物、開発正本、利用先の関係をMermaidで図示する。
- 開発者向けの同期手順、検証条件、アーカイブ索引への導線を整理する。
- 利用者をQA-productsへ直接誘導する表現を避ける。

### 3.3 Skillパッケージの利用者向け整備

- `quality-review`と`quality-response`を、各ディレクトリ単独でコピー可能な構造に整える。
- 各Skillに`SKILL.md`、CLIラッパー、`runtime/quality_loop/`コアモジュール、必要referencesを含める。
- CLIラッパーはSkill自身のディレクトリを基準にruntimeを解決し、開発元リポジトリのPythonパッケージを参照しない。
- 外部pipパッケージを要求せず、Python 3.10以上の標準ライブラリだけで動作する方針を明記する。
- Python 3.10および現行Python環境で同じ基本検証を実行し、未検証環境を対応済みと記載しない。
- `__pycache__`、`*.pyc`、`.pytest_cache`などの生成物を成果物から除外する。
- 開発・検証用のテスト、仕様、詳細examplesはQA-products側に保持し、利用Skillへ不要な資料を混在させない。

### 3.4 同期・同一性検査ツール

- QA-productsの`scripts/`に、Productivity-Skillの管理対象2Skillを同期するツールを追加する。
- 標準対象は次の2パスに限定する。
  - `Productivity-Skill/.agents/skills/quality-review/`
- `Productivity-Skill/.agents/skills/quality-response/`
- 対象リポジトリと対象パスは明示引数で受け取り、対象外パスへの更新は拒否する。
- `--dry-run`でコピー予定ファイル、追加・変更・削除、SHA-256差分を表示する。
- 宛先Gitワークツリーがdirtyの場合は通常実行を拒否し、`--force`指定時だけ管理対象2ディレクトリの上書きを許可する。
- 宛先省略時は`../Productivity-Skill`を候補とするが、Git remote URLまたは識別ファイルでProductivity-Skillであることを検証する。
- 管理対象2ディレクトリは、検査完了後の同期時に上書きする。
- コピー元・コピー先・Skill名・日時・コピー元コミット・タグ・SHA-256を記録する。
- runtime同一性検査に失敗した場合は同期を開始せず、非ゼロ終了する。
- Productivity-Skill側には同期スクリプトを配置しない。

### 3.5 アーカイブ整理

- `archives/`と`docs/Archives/`の用途・リンク・原本性を確認する。
- `archives/`はtar.gz、zipなどのバイナリ・原本アーカイブ、`docs/Archives/`はMarkdown形式の開発史・設計判断・QA記録を基本とする。
- Markdownの開発史は`docs/Archives/history/`、設計・方針判断は`docs/Archives/decisions/`を基本とする。
- `docs/Archives/README.md`を索引とし、必要に応じて下位索引を置く。
- 旧計画、旧QA、旧OpenSpec、実装報告、重複資料は、候補一覧とGit履歴を確認してから移動または現行導線から除外する。
- 過去資料のGit履歴、移動理由、関連コミット・タグを失わない。

## 4. 検証計画

- `quality-loop`の既存テストを実行する。
- Python 3.10および現行Python環境で既存テストとCLI起動を確認する。
- 2つのSkillのCLI `--help` をコピー前後で確認する。
- 合成FixtureでReviewer・Authorの基本経路と拒否経路を非破壊で確認する。
- runtime同一性、Skill構造、必須ファイル、実行権限を検査する。
- Markdown相対リンクとREADMEからの導線を専用検査で確認する。コードブロック内、外部URL、`mailto:`、画像、アンカー付きリンクを適切に扱う。
- アーカイブ移動前後で相対リンク解決結果を比較し、リンク切れを検出した場合は移動・削除を開始しない。
- 各Skillを開発元リポジトリ外の一時隔離ディレクトリへ単体コピーし、親リポジトリのパスや開発用環境変数に依存せず、`--help`と合成Fixtureの基本経路・拒否経路が成功することを確認する。
- Productivity-Skillへの同期後、同期記録とSHA-256を確認する。
- 既存案件の正本、既存Skill、ユーザーの作業中ファイルを変更しないことを確認する。

## 5. 変更・復旧境界

- 作業開始時、各編集ラウンドの開始時・終了時に`git diff`と対象範囲を確認する。
- ユーザーが開始時点で持つ変更は保持し、復元対象に含めない。
- アーカイブ候補の移動・削除前に、対象パス、リンク、Git履歴を固定する。
- 同期対象外のパス、既存の別Skill、対象不明のリポジトリは変更しない。
- 事前検査または同一性検査に失敗した場合は、同期・削除・上書きを開始せず停止する。
- 途中失敗時は新しい変更を追加せず、失敗対象・実施済み操作・復旧条件を記録する。
- commitは整理結果を確定する段階で行う。remoteへのpushは本計画の実施対象外とし、別途明示承認を得る。
- 開発継続期間は履歴を保持し、安定後に保存タグ・ブランチを作成してからSquashを検討する。

## 6. 実施しないこと

- remoteへのpush
- Productivity-Skill以外の外部リポジトリへの同期
- 既存Skillの無関係な上書き・削除
- 実案件の`case.json`、Evidence、Owner裁定、既存QA記録の改変
- 未検証版を利用成果物としてProductivity-Skillへ取り込むこと

## 7. 成果物

- 整理済みのQA-products `README.md`
- Mermaidによる役割・同期・利用経路の図
- 単独コピー可能な2つのQuality Loop Skill
- QA-products内の同期・同一性検査ツール
- `docs/Archives/README.md`および整理済み履歴・判断資料
- 同期記録、検証結果、残余リスクを含む実装報告

## 8. 完了条件

- QA-productsとProductivity-Skillの役割がREADMEから一読で分かる。
- Productivity-Skillをcloneした直後に、`.agents/skills/`の2つのSkillを利用できる。
- 2つのSkillが開発元リポジトリ外でも自立して動作する。
- CLI、基本経路、拒否経路、リンク、runtime同一性の検証が成功する。
- 旧資料の現行導線からの除外と履歴保存が確認できる。
- QA-products側に同期元・同期先・版・日時・SHA-256が記録される。
- 整理結果をcommitとして記録する。ただしremoteへのpushは未実施とする。
