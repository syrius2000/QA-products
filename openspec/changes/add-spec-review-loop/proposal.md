# Proposal

## Why

日常開発の大半はOpenSpecによるSDDで進み、changeごとに目的（proposal）、仕様Scenario（spec delta）、タスクと検証方法（tasks）が揃っている。一方、既存の独立QA経路は重い。`blind-qa-cycle`は監査ブランチ、Yip commit、4成果物、招待を前提とする。`quality-qa`はクラウドへの手渡しと人の承認を往復ごとに挟む。`quality-review`／`quality-response`はOwner裁定まで含む正式caseである。「changeを完成させる」という目的が明確な場面で、実装→別系統AIによる独立レビュー→修正を数回自動で回し、完成させる軽量な経路がない。

## What Changes

- 新Skill `spec-review-loop` を `quality-loop/skills/spec-review-loop/` に追加する。OpenSpec change IDを受け取り、`tasks.md`のタスク・検証文と`specs/**/spec.md`のScenarioから受入基準を抽出し、安定IDと要件指紋で固定する。
- 1 roundは「実装担当（現在のセッション）が実装報告付きのround commitを作る → 別系統のAI Reviewer（既定: Codex CLI、選択: Cursor CLI（`agent`）／Claude CLI）が読取り専用で、そのcommitを独立レビューする → 決定論的CLIが結果の構造を検証してGateを判定する」で構成する。
- 停止条件を固定する。全基準と必須checkがPASS、round上限（既定3）、Findingの停滞のいずれかで止め、PASS以外は人の判断、`quality-review`の`review-standalone`、`blind-qa-cycle`への引継ぎを案内する。
- 終了時、明示確認のうえでround commit群を1つのcommitへsquashする。squash前のcommitはローカルのバックアップrefに保存し、squash後のtreeがsquash前の最終treeと一致することを検証する。リモートへ公開済みのround commitがある場合はsquashしない（force-pushが必要になるため）。
- レビュー成果物（基準、実装報告、レビュー結果、要約）は`openspec/changes/<id>/review/`に残し、`openspec archive`でchangeと一緒に保存されるようにする。

## Capabilities

### New Capabilities
- `spec-review-loop`: OpenSpec changeを受入基準とする、round commit・別系統AI Reviewer・自動停止・終了時squashによる軽量な独立レビューループ。

### Modified Capabilities

なし。`quality-loop-skill-deployment`の管理対象Skillへの追加（4→5）は、本Skillの動作確認後に別changeで行う。

## Impact

- 追加: `quality-loop/skills/spec-review-loop/`（SKILL.md、references、stdlibのみのPython runtime、`bin/spec-review-loop-cli`、evals）。
- 実行時の書込み: 対象リポジトリの`openspec/changes/<id>/review/`、round commit、ローカルref `refs/spec-review/<change>/<timestamp>`。
- 外部ツール: Codex CLI（既定）、Cursor CLI（`agent`）、Claude CLI。実行時に存在とバージョンを確認し、未導入なら停止する。
- 対象外: `quality-qa`、`blind-qa-cycle`、`quality-review`、`quality-response`の本文・runtime・既存記録の変更、main/masterへのmerge、force-push、`openspec archive`の自動実行、外部Skillディレクトリへの配備。
