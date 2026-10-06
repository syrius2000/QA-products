# 実装前調査記録

## 1. 配置とGit状態

確認日: 2026-10-07

| 項目 | 観測 |
|---|---|
| repository branch | `master` |
| 開始時status | `master...origin/master`。追跡対象の既存変更なし。Plan 038とOpenSpec Changeは未追跡成果物。 |
| 正本 | `quality-loop/skills/blind-qa-cycle/`。Git追跡対象。 |
| 旧ローカル配置 | `.agents/skills/blind-qa-cycle/`。`.gitignore:14`の`/.agents/`によりGit管理外。Git追跡・通常statusからユーザー編集の不存在は証明できない。 |
| 観測された内容差分 | `SKILL.md`、`references/cloud_output_contract.md`、`references/focus_provenance_plans.md`、`references/git_wip_flow.md`、`references/machine_schema.md`の5ファイル。 |
| 配置移行境界 | Plan 039で専用計画化。事前ファイル別hash/backup、dry-run差分、rollback、明示承認が揃うまで`.agents/`は変更しない。 |

## 2. 現行契約と統合仕様の対応

| 領域 | 現行契約・根拠 | 今回の扱い |
|---|---|---|
| 基準点 | `checkpoint`は既存の非default topic branchのstaged-only WIPをBaselineとして記録する。Unstaged/untrackedや対象外stageがあれば停止。 | 維持。実装前`prepare`に加え、実装後はcheckpointまたは今回の明示cloud操作で新branchを作る際のbranch-start SHAを固定Baselineとして許可する。|
| Reviewed対象 | cloud flowはBaselineとReviewedの完全SHAを使い、別tipへ代替しない。指定SHA欠落はHOLD。 | 維持・強調。開始方式と完全SHAを招待へ含める。 |
| Local/Cloud | Localはpushせず本文をhandoff。Cloudはtopic-only pushと相対path handoff。main/masterは禁止。 | 同じQA/output契約を使い、Audience・remote visibility・handoff/Git帰着だけを分岐させる。 |
| 依頼・Reviewer資料 | 現行正本はAC原文/順序/fingerprintと参照Skill/contract hashを固定し、CloudはReviewed SHA上で照合する。 | 維持。正本本文、出力契約、machine schemaを同期する。 |
| Reviewer成果物 | `00_invite.md`、`01_review.md`、`02_tasks.md`、`03_machine.json`、`STATUS.md`。対応が必要なFindingとtaskの対応を要求。 | Reviewerの既存4ファイル契約を保つ。既存cycleを編集しない。 |
| 修正・再QA | 実装側はFinding単位に修正し、再QAは新cycleで前回ReviewedをBaselineとし、前cycleを凍結する。 | 維持してライフサイクル順に整理する。 |
| 終結 | Cloudレビュー成果物のcommit/pushは明示Audience/modeの範囲。Owner ACCEPT/ARCHIVEやmain mergeは禁止。 | 残余リスク・最終Gate・SHAと終結を分け、Owner判断とmergeを別工程にする。 |
| Human Understanding Note | 現行契約には存在しない。 | Reviewer成果物ではなく、人が終結時に書く`04_human_understanding.md`として追加。QA Gateとは分離し、AIによる代筆・採点をしない。 |
| QA Skillの役割境界 | `quality-qa`は通常QA、`quality-review`/`quality-response`はformal caseのReviewer/Implementer操作。各Skillの正本・CLI契約は個別。 | 既存Skill・case正本を変更せず、blind cycleから用途に応じて案内する。 |

この記録は読み取り調査に基づく。`.agents/`のバックアップ・書換え・shim配置および配置後検証はまだ実施していない。

## 3. Spec Scenario机上確認

2026-10-07にspecの全Scenarioを実装文書へ照合した。これは手順・契約の机上確認であり、実行テストや独立QAのEvidenceではない。

| Scenario | 期待結果 | 契約・実装箇所 | 状態 |
|---|---|---|---|
| 監査ブランチ上の独立QAを開始する | blind cycleで開始方式、topic branch、固定SHAを記録する | `quality-loop/skills/blind-qa-cycle/SKILL.md` Modes / prepare / invite | 対応 |
| 通常QAまたは正式caseの依頼を受ける | 既存Skillへ案内し、成果物やcase正本を移さない | `SKILL.md` 適用範囲と他QA Skillとの使い分け | 対応 |
| 実装前にQA計画をYip commitへ固定する | cleanなtopic branchで計画だけをcommitし、そのSHAをBaselineにする | `SKILL.md` Mode: prepare; `references/git_wip_flow.md` prepare | 対応 |
| 計画commit後に実装とレビューを行う | planの同cycleを使い、plan commitをBaselineとしてdiffから計画自体を除く | `SKILL.md` Mode: cloud / invite; `references/machine_schema.md` | 対応 |
| 実装後にQAを開始する | checkpointをBaselineにし、post-changeとして選択理由を記録する | `SKILL.md` Mode: cloud / local / invite; `references/git_wip_flow.md` | 対応 |
| 完了済み変更から新しいQA branchを作る | 切替前HEADがbranchの開始commitであり、Reviewedより前にcommitがないことを確認してBaselineへ固定する | `SKILL.md` Mode: cloud; `references/git_wip_flow.md` cloud; spec branch-start Scenario | 対応 |
| 指定SHAが取得できない | HEAD等へ差替えずHOLDとprovenance Findingを記録する | `SKILL.md` Mode: review; `references/audience_channels.md` | 対応 |
| Local reviewerへ渡す | 固定SHA・相対DIR・同一出力契約を使いpushしない | `references/audience_channels.md` local; `SKILL.md` Mode: local | 対応 |
| Cloud reviewerへ渡す | 対象と招待の可用性を確認し、取得不能ならHOLDまたはingestにする | `references/audience_channels.md` cloud; `SKILL.md` Mode: review / cloud | 対応 |
| 実装担当が同一対象をレビューする | 独立レビューとして受理せず別担当を求める | `SKILL.md` 適用範囲と他QA Skillとの使い分け; Mode: review | 対応 |
| 指摘と修正依頼を返す | Evidence付きFindingとFinding別taskをcycle DIRに保存する | `references/cloud_output_contract.md` 01/02/03成果物契約 | 対応 |
| 必須checkを実行できない | 未実施理由を記録し、PASSにしない | `references/cloud_output_contract.md` 適用範囲 / 受入基準 | 対応 |
| 過去cycleが存在する | 新cycleを作り、旧成果物を変更しない | `SKILL.md` Output directory / Re-QA; `references/git_wip_flow.md` | 対応 |
| 実装側がFindingへ対応する | 選択したFindingだけを修正し、Yip response commitと新cycle inviteへ結ぶ。Reviewer成果物は不変 | `SKILL.md` Mode: respond; `references/git_wip_flow.md` respond / Re-QA | 対応 |
| 修正後に再QAする | 新cycleで前回ReviewedをBaselineに再確認する | `SKILL.md` Re-QA; `references/git_wip_flow.md` cloud re-qa | 対応 |
| 前回の指摘が再QA結果から欠落する | Findingを未解決/未検証として残す | `SKILL.md` Re-QA、Reviewer contract | 対応 |
| サイクル終結時にNoteを作る | cycle情報を正本から取得してNote作成を促す | `SKILL.md` Mode: note | 対応 |
| 人が理解内容を記入する | 6問を提示し、本人回答を逐語で保存する | `SKILL.md` Mode: note / 04 template | 対応 |
| Noteが既に存在する | 上書きせず既存pathを返す | `SKILL.md` Mode: note step 3 | 対応 |
| Noteが未記入または理解が不十分である | 空欄・未理解を許しGateやOwner受入へ混ぜない | `SKILL.md` Mode: note steps 5-7 | 対応 |
| 監査サイクルを終結する | Finding状態、残余リスク、Gate、SHA、Note pathを記録する | `SKILL.md` 監査cycleの終結 | 対応 |
| 既定ブランチへ統合する | merge/deployをOwnerの別判断として案内し、自動実行しない | `SKILL.md` サイクル全体の流れ / 監査cycleの終結 | 対応 |
| 他のQA Skillが必要な依頼 | 対象Skillを案内し、正本データを複製・移動しない | `SKILL.md` 適用範囲と他QA Skillとの使い分け | 対応 |

`.agents/skills/blind-qa-cycle/`の互換shimと旧本文解消は別途Plan 039の承認待ちで、上表の契約統合とは別の未完了配置作業として残る。

## 4. 静的確認と変更範囲

- `openspec validate --strict unify-blind-qa-cycle`: 成功。
- `quality-loop/skills/blind-qa-cycle/SKILL.md`および同Skillの参照Markdownから抽出した16件の相対リンク: 欠落0件。
- `git diff --check`: 成功。
- 追跡対象の変更パスは正本Skill本文と4つの参照Markdownのみ。`quality-qa`、`quality-review`、`quality-response`、既存QA cycle記録、製品コードに変更はない。
- `docs/Artifacts/`には作業前からのPlan 038に加えてPlan 039の計画記録がある。OpenSpec Changeと計画書は未追跡Artifactで、Git差分の対象製品コードではない。
- `.agents/skills/blind-qa-cycle/`は未変更。Plan 039の明示承認待ち。

これらはOpenSpec構造・リンク・変更範囲の静的確認であり、動作テストや独立QAを実施した結果ではない。
