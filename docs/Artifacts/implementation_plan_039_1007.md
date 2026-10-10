# blind-qa-cycleローカルshim配置計画

> **更新（2026-10-11）**: 利用者の決定により、shim化ではなく削除を実施した。削除前のバックアップ（9ファイル、SHA-256照合済み）: （リポジトリの外、QA-products-qa-records-backup-20261010/agents-blind-qa-cycle-20261011020730）。対象は`.agents/skills/blind-qa-cycle/`のみ。以下の手順のうち、shim配置とdry-runの承認は、この決定により実施していない。


created: 2026-10-07 00:56 (JST)
update: 2026-10-07 00:56 (JST)
author: Codex (GPT-6)

## 目的

`unify-blind-qa-cycle` Changeで整備する正本`quality-loop/skills/blind-qa-cycle/`へ、このcheckoutの`.agents/skills/blind-qa-cycle/`から安全に誘導できるよう、ローカル配置の互換shim化を別工程で行う。本計画はこのcheckout内の当該Skillだけを対象にし、グローバル配置、他リポジトリ、QA製品コード、既存QA cycle記録を対象にしない。

## 現状確認

2026-10-07の読み取り調査で、作業開始時のGitブランチは`master`、追跡対象の変更はなかった。OpenSpec Change成果物およびPlan 038は未追跡Artifactとして存在する。

- 正本候補: `quality-loop/skills/blind-qa-cycle/`。Git追跡対象。
- ローカルSkill配置: `.agents/skills/blind-qa-cycle/`。`.gitignore:14`の`/.agents/`によりGit管理外。
- ローカル配置は現行正本と同一ではなく、`SKILL.md`、`references/cloud_output_contract.md`、`references/focus_provenance_plans.md`、`references/git_wip_flow.md`、`references/machine_schema.md`の5ファイルで差が観測された。
- 変更前状態の完全なbackup、内容hash、ローカル利用者による意図的変更の有無は未確認。ignore対象で通常の`git status`に現れないため、Git差分だけでは利用者変更なしと判定できない。

## 実施対象と境界

対象はこのcheckoutの`.agents/skills/blind-qa-cycle/`配下のみ。

実施候補は旧Skill本文の実行指示を残さず、`quality-loop/skills/blind-qa-cycle/SKILL.md`を唯一の正本として案内する短い互換shimへ置換すること。参照ファイルを同ディレクトリに残す場合、旧内容の独立契約として使わせず、正本への案内と配置説明に限定する。最終配置方式は乾式差分を提示した時点で計画との一致を再確認する。

変更しないもの:

- `~/.agents/skills/`等のグローバルSkill配置
- 他のrepositoryにある同名Skill
- `quality-loop/skills/`の正本（これはPlan 038の承認範囲で別途更新する対象）
- `quality-qa`、`quality-review`、`quality-response`
- QA cycleの既存データ、main/master、remote

## 手順

1. **事前状態記録**: 実施直前にbranch、HEAD、Git status、対象ファイル一覧、各ファイルSHA-256、size、mtimeを読み取り、dry-run reportへ保存する。既存ファイルをユーザー変更と区別できない状態のため、内容を外部backup先へ完全コピーし、復元対象とhash manifestを作る。backup先・manifestのパスは書き込み前に表示する。
2. **事前停止条件**: 事前状態がこの計画の対象・方式と異なる、対象に予期しないファイルがある、backupの完全性が検証できない、または正本が確定していない場合は変更しない。ユーザーへ差分と理由を報告して計画を更新する。
3. **dry-run**: 実際には書き込まず、旧Skillからshimへ変わるファイルごとの削除・置換・追加、正本への相対参照、Codexからの読み取り可否を示す。全差分をユーザーが確認できる形式で提示する。dry-run実行後に実体を編集しない。
4. **実行前照合と承認**: dry-run結果、backup場所とmanifest、書換対象一覧、rollback手順が本計画と一致することを確認し、このローカル配置変更への明示承認を得る。Plan 038またはOpenSpec applyの一般承認を、この配置承認の代替にしない。
5. **shim配置**: 承認済みの対象ファイルだけを書き換える。`git add`、commit、push、他Skill配置、他repo編集は行わない。正本が扱われる対象branch上のSkillとして到達可能な相対案内を記載する。
6. **配置後検証**: 対象ファイルがdry-runどおりであること、shimから正本へ到達できること、旧版の競合実行指示が残らないこと、対象外ファイル・QA記録・Git branch/index/worktreeが変わらないことを照合し、検証結果を記録する。
7. **rollback**: 検証失敗またはユーザー要求があった場合、事前hash manifestと照合し、当該配置ラウンドが変更した対象だけをbackupから復元する。復元先の内容が想定と異なる場合は上書きせず停止し、差分を提示する。復元後に全ファイルhashと配置一覧をbackup manifestへ照合する。

## 受入条件

- 実施前の全対象ファイルがbackupされ、manifestで完全性を検証できる。
- dry-runに対象ごとの変更内容、相対リンク先、rollback手順が示され、明示承認が記録される。
- 旧配置が正本を一意に案内し、旧本文や旧参照契約を重複した実行正本として残さない。
- 実施対象はこのcheckoutの`.agents/skills/blind-qa-cycle/`だけで、Git追跡対象、製品コード、QA cycle、他Skill、他repo、remoteは変更されない。
- 配置後検証と、backup manifestからの対象限定rollback手順が成功する。

## 未実施事項と承認ゲート

本書は計画のみである。backup作成、dry-runの作成、shim配置、rollback実行、Git操作は未実施であり、いずれも本書の承認後に対象を再確認して行う。承認前にPlan 038の一般承認だけで`.agents/`へ書き込まない。
