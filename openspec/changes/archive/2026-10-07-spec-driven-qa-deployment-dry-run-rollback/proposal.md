# Proposal

## Why

通常QAの入口である`quality-qa`と、正式Quality Loop案件のReviewer／Implementerで使う`quality-review`／`quality-response`を複数リポジトリから利用できるよう、承認済みの配布元を個人グローバル領域へ配置する。配置先衝突、部分コピー、元リポジトリ依存を避け、rollback可能な範囲を固定する。

## What Changes

- `quality-qa`、`quality-review`、`quality-response`の3 Skillを、必要なruntime、CLI、references、templates、VERSIONを含めて`~/.agents/skills/`へコピーする。
- 3 Skillと必要ファイルのSHA-256 manifestを固定し、既存先がないことを確認してから一時領域へ配置・検査し、rollbackを試行する。
- 正式QA記録に残る残余リスクと今回のOwner明示指示を区別して記録する。`blind-qa-cycle`、既存Skill、他のパスは変更しない。
- 配置ガイドとQuality Loop READMEを3 Skillの用途・対象・検査・rollbackに一致させる。

## Capabilities

### New Capabilities

なし。

### Modified Capabilities

- `quality-loop-skill-deployment`: `quality-qa`を配布可能なSkillとグローバル配置対象に追加し、3 Skillの配置検査とrollback契約を定める。

## Impact

- OpenSpec capability `quality-loop-skill-deployment`、`quality-loop/README.md`、`quality-loop/SKILL_DEPLOYMENT_GUIDE.md`。
- 個人グローバル領域`~/.agents/skills/quality-qa/`、`quality-review/`、`quality-response/`。
- 既存のQA-0008残余リスク記録、Owner裁定、`blind-qa-cycle`には変更を加えない。
