# Reviewer・Author Skill 棚卸し記録

created: 2026-08-25 21:19 (JST)
update: 2026-08-25 21:19 (JST)
author: Codex (GPT-5)

## 目的

Contract v1.2 の実装対象を確定するため、グローバル環境にあるReviewer SkillとAuthor Response Skillを読み取り専用で棚卸しした。今回の実装では、グローバル配置先を変更せず、リポジトリ内のstage領域を使用する。

## 調査対象

| Skill | 調査元 | 通常ファイル数 | MANIFEST SHA-256 |
|---|---|---:|---|
| Reviewer | `/Users/myamaguchi/.agents/skills/spec-driven-qa-review/` | 62 | `74f0682e2c5678b7c86037e36220a2130342abb40aa8f7f7bd51de375c01957e` |
| Author Response | `/Users/myamaguchi/.agents/skills/spec-driven-qa-author-response/` | 27 | `a8a1481f5a9acfc70fa4aa80f4c1068ec4abd5d886c3cde49e054835e0cd58be` |

通常ファイル数は`.pytest_cache/`と`__pycache__/`を除いて数えた。両SkillにはPython bytecodeとpytest cacheが存在するため、stage対象から除外する。

## Stage対象一覧

各Skillの`MANIFEST.txt`に記載された通常ファイルを対象とする。MANIFEST自体もstage対象に含め、stage後のManifest検証に使用する。

### Reviewer Skill

- 基本文書: `CHANGELOG.md`、`INSTALL.md`、`MANIFEST.txt`、`README.md`、`SKILL.md`、`pyproject.toml`
- Adapter: `adapters/`
- Schema: `schemas/`
- Template: `templates/`
- Script: `scripts/*.py`
- Test: `tests/`
- Example: `examples/`
- Reference: `references/`
- Integration: `integrations/`
- Evaluation: `evals/`

### Author Response Skill

- 基本文書: `CHANGELOG.md`、`INSTALL.md`、`MANIFEST.txt`、`README.md`、`SKILL.md`、`pyproject.toml`
- Script: `scripts/validate_author_response.py`
- Test: `tests/test_author_response.py`
- Example: `examples/`
- Reference: `references/`
- Evaluation: `evals/evals.json`

## namespace分離の対象

ReviewerとAuthorの両方に同名のトップレベル共有モジュールは確認されなかった。ただしReviewer側には` scripts/common.py `が存在するため、stageではSkill固有namespace配下へ配置し、トップレベルimportに依存しない構成へ移行する。Author側の検証処理は`author_response`固有namespaceへ配置する。

## 作業開始時点の既存差分

以下は2026-08-25 21:19 JST時点で、今回の実装開始前から存在した差分である。これらは今回のTask 1.1では変更しない。

- 追跡済み変更: `Gemini-Flash.md`、`README.md`、`docs/Artifacts/`配下、既存archive、`openspec/changes/cron-csv-to-influx-sync/`、Grafana dashboard
- 未追跡変更: `.agents/`、`Codex.md`、`backup/home_pi_full/`、追加Artifact、対象Change、`references/Grafana-config.md`
- 対象Change自身の既存ファイル: `proposal.md`、`specs/`、`design.md`、`tasks.md`、`.openspec.yaml`

## 除外規則

- グローバルSkillの直接編集・削除・配備は行わない。
- `.pytest_cache/`、`__pycache__/`、`*.pyc`はManifestおよびstage対象から除外する。
- 実データ、認証情報、外部システム状態はstageへ複製しない。
- 既存Git差分・未追跡ファイルは復元、削除、上書きしない。

## 判定

Task 1.1に必要な棚卸し、stage対象一覧、既存差分、cache・bytecode除外規則を記録した。次のTask 1.2では、この記録に基づき、stage内でReviewerとAuthorのnamespace分離を実装する。
