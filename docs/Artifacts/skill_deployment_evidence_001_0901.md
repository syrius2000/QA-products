# Quality Loop Skill自己完結配布 Evidence

created: 2026-09-01 00:20 (JST)
update: 2026-09-01 00:24 (JST)
author: Codex (GPT-5)

## 1. 記録目的

OpenSpec Change `deploy-quality-loop-skills`の実装前後に、Python共通基盤、2つのSkill、手動配置文書、および最小配置検査のEvidenceを記録する。

## 2. 実装開始前の状態

- 承認済み計画: `docs/Artifacts/implementation_plan_019_0831.md`
- 実装開始日時: 2026-09-01 00:20 (JST)
- 開発正本: `quality-loop/quality_loop/`
- `quality-review`と`quality-response`に`runtime/`および`bin/`は存在しない。
- 両SkillのCLI例は、Bundleルートを作業ディレクトリとする`python3 -B -m quality_loop.cli`を記載している。
- 両Skillは`../../references/qms-foundations.md`を参照しており、単独コピー後にはSkill外参照となる。
- 作業開始時のGit差分は、今回作成済みのOpenSpec ChangeとPlan 019だけである。

## 3. 開発正本PythonソースのSHA-256

| 相対パス | SHA-256 |
| --- | --- |
| `__init__.py` | `4e61c78060aaee97d3d543957db24da41ac7757f6615265106c76b8532275e39` |
| `authorization.py` | `16be8c5c8648dc0b8904f522fd37b84464dd4f756ce956288644ba73220700a8` |
| `case_store.py` | `e3e58bfa1eba7030f35c846bf2f6a20294580668e733f61edcf76b83ef01d4b7` |
| `cli.py` | `ab282be13b8b59248c57e868fa30983f338186e7f3c1c9bc304032aa5366838c` |
| `engine.py` | `13230e63a34cde93f9276a3598a9977d811e1ab5db59b3fe2ba2c4088a042889` |
| `errors.py` | `d0afe9548caf512f0fe1faf964f7c8444a754009e72e4f63afa07af1b1d67cda` |
| `evidence.py` | `68459c4732cea90e61639b3d3eb9f47c3a90f904d5a0b8f9100f6e5d6cf5d2a3` |
| `handoff.py` | `72176f50dae59be5cfcf9291e1a039091ed044aa4b171389a420b871b32b807f` |
| `markdown_report.py` | `c5c5dace241c2fbb04a0509774a1c0a805710fa73ab479d6c91517a88e38caca` |
| `model.py` | `07c52ac5a9872ff5a755ea4c67138526ee2ddb457c6958d8411309d5719c87cf` |
| `observation.py` | `c5a2355040565c3bad6ee8d568485b9977e67730737e8d723b790fb74218cdac` |
| `transitions.py` | `6685ccc2cb60038a3e2deaeca6c807b03a9ae823ef9e77fbbff68a5d5c731c7c` |

## 4. 未検証事項

- 実際のグローバル配置および他リポジトリへの配置は本Changeの対象外であり、`unverified`である。
- グローバルとローカルが同時存在する場合の実行環境における優先順位は、実環境の確認を行わない限り`unverified`である。

## 5. 実装内容

- `quality-review`と`quality-response`へ、正本のPythonソース12件を`runtime/quality_loop/`として同梱した。
- 両Skillへ、配置場所を基準に`PYTHONPATH`を設定するPOSIX shellラッパーを`bin/`へ追加した。
- 両Skillへ`references/qms-foundations.md`を同梱し、Skill外の`../../references/`参照を除去した。
- frontmatterへ正の発火条件と負の非発火条件を明記し、一般レビュー、一般回答、OpenSpec一般、Role外操作との境界を明確化した。
- `quality-loop/SKILL_DEPLOYMENT_GUIDE.md`を新規作成し、手動コピー、衝突時停止、更新、最小検査、Rollback判断を記載した。
- ルート`README.md`を、利用開始、Skill選択、案件開始、現在状態、設計思想、評価・開発情報の順へ再編した。

## 6. 最小配置検査結果

| 検査項目 | 結果 | Evidence |
| --- | --- | --- |
| 両Skillのfrontmatterと非発火条件 | pass | `name`維持、一般レビュー・一般回答・OpenSpec一般・Role外を対象外として記載 |
| Skill外Python／参照資料への依存除去 | pass | `../../references/`、`cd quality-loop`、直接`python3 -B -m quality_loop.cli`の記載なし |
| runtimeのPythonソース一覧 | pass | 正本、Reviewer、Implementerで各12件 |
| runtimeのSHA-256比較 | pass | 正本と両同梱runtimeで相対パス・SHA-256完全一致 |
| 不要な生成物の不在 | pass | 2つのSkill内に`__pycache__`、`*.pyc`、`.pytest_cache/`なし |
| 空白を含む一時コピー先からの起動 | pass | `/private/tmp/quality-loop-skill-smoke.aHQKfN/copy space/`の2つのラッパーで`--help`成功 |
| READMEとガイドのリンク先 | pass | 専用ガイド、Quality Loop README、機能仕様、Template、Archiveへの相対リンク先が存在 |
| 既存グローバルSkillへの書込み | pass | `~/.agents/skills/quality-review`および`quality-response`へ書込みを行っていない |
| OpenSpec strict validation | pass | `openspec validate deploy-quality-loop-skills --strict --json`で`valid: true` |

## 7. 未実施・未検証

- 自動テストスイートは、承認済みPlan 019に従い実行していない。
- 実案件E2E、Skill discoveryの動的発火選択、グローバルとローカルが同時存在する環境の優先順位は`unverified`である。
- グローバル配置、他リポジトリへのローカル配置、既存Skillとの差分更新、旧版削除、commit、pushは実施していない。
