# Design

## Context

`quality-review`と`quality-response`は自己完結した配布単位として整備済みで、`quality-qa`も独立runtimeとCLIを同梱する。配布先は`~/.agents/skills/`で、3対象は現在すべて不存在。`blind-qa-cycle`は既存の別Skillとして保持する。QA-0008の`accepted-with-residual-risk`と旧`deployment_allowed:false`は過去の裁定として保持し、今回のOwner指示を新しい配置承認として記録する。

## Goals / Non-Goals

**Goals:**
- 3つのSkillを完全なディレクトリコピーとしてグローバル配置する。
- 配置前後のファイル一覧・SHA-256と、対象外パスが不変であることを記録する。
- 一時領域でCLIを検査し、rollback操作で配置前状態へ戻ることを確認する。

**Non-Goals:**
- `npx skills`による複数Agent向けinstaller設定、Codex agent-specific pathへの配置、またはsymlink化。
- `blind-qa-cycle`、既存Skill、Productivity-Skill、その他のSkillの更新・削除。
- QA-0008の過去のFinding、残余リスク、Owner裁定を書き換えること。
- commit、push、production配備。

## Decisions

1. **指定済みの個人共通パスへ手動コピーする。** `npx skills`はローカルpath導入とcopy modeに対応するが、Agent別の配置先を選ぶinstallerである。リポジトリが規定する`~/.agents/skills/`への厳密なコピーを保つため`cp -a`を用い、symlinkを作らない。
2. **上書きを禁止する。** 配置直前に3対象が引き続き不存在であることを検査する。1件でも存在したら停止する。既存の`blind-qa-cycle`は対象外としてSHA-256を前後比較する。
3. **一時領域でcopy・検査・rollbackを試す。** source/stageの相対path、file type、mode、サイズ、SHA-256を照合し、各CLIの`--help`を起動する。その後stageだけを撤去し、stageが不存在になったことを確認する。
4. **実配置を最後のcopy operationにする。** 直前にmanifestと配置先を再確認し、3ディレクトリを新規作成する。配置後にmanifestとCLIを再検査する。失敗時は本Changeで作成した3対象だけを削除し、配置前の不存在状態へ戻す。

## Risks / Trade-offs

- **QA-0008の履歴に配備不可裁定が残る** → 過去記録は変更せず、今回のOwner明示指示と対象範囲を新Changeのauthorization evidenceへ保存する。受入済みCoreと残余リスクを混同しない。
- **ローカルSkill sourceの更新追跡がない** → 配置版とtree SHA-256を記録し、以後の更新は新しい対象限定手順で行う。
- **Agentによるskill discoveryの更新時差** → ファイル配置とCLI起動を確認し、利用可能性は新しい会話／agent refresh後に確認する。

## Migration Plan

1. OpenSpec Change、authorization evidence、source manifestを作成する。
2. 配置先の不存在と既存`blind-qa-cycle`のbaselineを記録し、3 Skillを一時領域へcopyする。
3. 必要ファイル、CLI、hash、path境界を検証する。
4. 一時領域に限ってrollbackを実行し、baselineが復元されることを確認する。
5. 配置先を再確認し、明示承認済み3パスへcopyする。
6. 配置後manifestとCLIを検証し、失敗があれば3対象だけrollbackする。
