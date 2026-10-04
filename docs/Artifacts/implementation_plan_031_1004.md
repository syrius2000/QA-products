# 追跡可能なQA Skill統合と通常QA全工程の改善計画

created: 2026-10-04 16:56 (JST)
update: 2026-10-04 16:56 (JST)
author: Codex (GPT-6)

## 位置付け

本計画は、承認済みの[計画030](implementation_plan_030_1004.md)を、実装開始前のOpenSpec確認で判明した格納先・作業範囲の差に合わせて改訂する。計画030に基づくコード・Skill変更はまだ開始していない。本計画への再承認後は、計画030の代わりに本計画を実装境界として使用する。

## 改訂が必要な理由

- `unify-qa-skill-workflow`はOpenSpecの`spec-driven` Changeで、39タスクすべてが未完了と記録されている。計画030は全工程を掲げているが、39タスクの成果物・パッケージ化・旧形式互換を実装範囲として十分に固定していなかった。
- `.agents/skills/`はリポジトリの`.gitignore`で除外されている。そこだけを変更しても、Cloud Reviewerが対象commitからSkillを読めず、変更をレビュー・配布できない。
- 既存のリポジトリ内Skill配布は`quality-loop/skills/<skill>/`を追跡可能な自己完結パッケージとして使う。通常QA側にもCloudがcommitから読む正式パッケージが必要である。
- 現在の`AGENTS.md`の「新規topic branch」指示は、`blind-qa-cycle`の既存topic branch・checkpoint方式と矛盾する。CloudへのSkill読込、レビュー対象commit、依頼commit、QA成果物commitも区別する必要がある。
- 実際のOpenSpec開始時Git状態は`master` / `ad6ca1e`、既存差分166件（削除148、未追跡17、変更1。調査時点）で、OpenSpec初期タスクに記録された削除件数20と一致しない。開始記録を現状に合わせ、既存差分を保全する必要がある。

## 目的と完了像

通常QAの全工程（依頼準備、ローカル／クラウド公開、独立レビュー、結果取得・検査、修正計画、承認後提出、再QA、終了判断）について、正本Skill、追跡可能な配布パッケージ、runtime、OpenSpec契約、回帰テスト、evalを一致させる。Cloud Reviewerが固定対象commitからQA Skillと出力契約を実際に読め、全受入基準をレビュー成果物へ列挙・照合でき、提出後の未承認変更が次回QA対象に混入しない状態を目指す。

## 対象

- `AGENTS.md`の限定委任節を訂正し、通常QA／クラウドQA、ローカル成果物、Reviewed対象、依頼、Reviewer成果物それぞれの許可境界をSkill契約と一致させる。
- 正式な追跡元として`quality-loop/skills/quality-qa/`と`quality-loop/skills/blind-qa-cycle/`を作成または更新し、`SKILL.md`、runtime、CLI、references、templates、evalsをCloud clone内で自己完結させる。
- 既存ローカルSkill `.agents/skills/quality-qa/` と `.agents/skills/blind-qa-cycle/`を同一契約へ更新し、追跡元との内容一致を検査する。グローバルSkillや別repositoryへの配置は行わない。
- `quality-loop/tests/`にQA workflowの単体・統合・Git操作fixtureを追加し、`quality-loop/README.md`、機能仕様、必要な手動配置ガイド、`scripts/sync_productivity_skills.py`のSkill対象定義を新しい追跡パッケージと一致させる。外部コピー・同期実行はしない。
- `openspec/changes/unify-qa-skill-workflow/`のproposal/spec/design/tasksを現在の正本構成、現Git状態、QA-F01/F02、Skill読込、branchとcommit境界に合わせて更新し、39タスクすべてを完了条件に使う。
- 正式Quality Loopのcase正本、events、Owner裁定ロジックは変更せず、関連回帰テストだけ実行する。

## 実装契約

### 依頼と承認

- 通常QAの明示依頼は、読み取り専用調査、依頼準備、指定先へのQA成果物作成を許可する。曖昧な「QAして」だけからクラウド公開・commit・pushを推定しない。
- クラウドQAの明示依頼は、そのQA依頼で表示・固定した対象範囲についてのみ、Skillが明記するQA提出処理を許可する。製品Reviewed commit、QA依頼commit、QA成果物commitは、各々許可パス・SHA・起動条件を分離する。
- branch自動作成をQA公開の暗黙動作に含めない。既に選択された非main topic branchとSkill固有のcheckpoint/staged-only要件を使い、合わない場合は公開前に停止する。force-push、main/master公開・統合を行わない。
- 製品コード・仕様の修正、Findingの裁定、残余リスク受入、merge、外部配置には別の明示承認を要求する。

### 独立レビューとCloud Skill読込

- inviteに対象Reviewed SHA、baseline SHA、QA Skillの追跡可能な相対パス、Skillと出力契約のSHA-256、全受入基準、許可出力範囲を記録する。
- Reviewerに対象commit内の`quality-qa`／`blind-qa-cycle`の指定Skillと出力契約を読むよう指示する。必要ファイルの不在・hash不一致・取得不能ではGateをHOLD相当として理由を残す。
- invite本文を自己完結させ、ローカル／クラウドで共通のcriterion集合と4成果物契約を使う。実施AIの自己評価・期待Findingをレビュー結論の誘導に使わない。

### QA-F01／QA-F02と成果物

- 依頼基準を安定ID付き原文の順序付き集合として固定し、Markdownレビューとmachine記録に全件列挙する。取込時にID・原文・件数・順序・fingerprintを依頼正本と照合し、欠落・重複・追加・改変を拒否する。
- 修正提出時に計画承認済みパス、提出snapshot、Evidenceを保存する。再QAは提出されたsnapshotだけを対象にし、提出後に追加・変更された別製品ファイルを自動採用しない。範囲拡張や未提出変更は停止し、再承認または新規依頼へ戻す。
- 初回基準、目的、全受入基準、前回reviewed baseline、全未解決Findingと過去サイクルを保持し、凍結済みサイクルを上書きしない。
- 依頼・review・tasks・machine JSON・STATUSの整合、Finding/task対応、High必須task、Gate/STATUS一致、source SHA・Skill hashを機械検査し、問題があれば成功扱いにしない。

## 作業方法と保護境界

- 実装着手時にOpenSpec task 1を現状へ更新する。開始時状態を再取得し、既存166件と無視対象`.agents`の全対象ファイルをmanifest/hashで記録する。
- 現在のdirtyな`master`へ直接実装しない。隔離worktreeへ承認済みOpenSpec・計画・必要Skill正本だけを内容識別付きで持ち込み、元checkoutの削除・未追跡・既存差分には触れない。worktree開始点またはコピー可能なGit状態が特定できない場合は作業を止めて計画を再確認する。
- 編集ラウンドごとに開始・終了diffを取得し、既存差分と本作業分を分ける。依存追加は行わず、既存Python標準ライブラリ範囲を維持する。
- OpenSpecの39タスクを順に適用し、各タスクの実装・検証後にだけチェックを付ける。仕様追加や対象拡張が必要なら実装を止め、計画更新と再承認を得る。

## 検証

- OpenSpec適用前後で`openspec list/status/instructions apply`を取得し、最終的にstrict validationを通す。
- QA-F01 negative cases: 基準1件欠落、ID重複、原文改変、追加基準、順序変更、fingerprintのみ一致する不正本文を拒否する。
- QA-F02 negative cases: submit後の別製品パス編集、新規ファイル、rename、複数製品ファイルの部分提出、古いsnapshotを拒否し、提出済み範囲内の正常な再QAだけを通す。
- authorization/Git fixtures: 曖昧なQA、明示local/cloud、main/master、branch不一致、checkpoint欠落、unstaged/untracked、対象外staged paths、commit後失敗、remote先行・分岐、push失敗、QA成果物のみの再試行をbare remoteで確認する。GitHubへはpushしない。
- Cloud package tests: Skillと参照の相対link、実行可能CLI、同梱runtime、source/mirror SHA一致、inviteの4成果物・全criterion・Skill hash、欠落時HOLDを確認する。
- 依頼から終了までの統合fixture、legacy読取互換、quality-loop既存回帰、Skill eval、パッケージ同期dry-run、OpenSpec strict validationを実行する。実Cloud reviewとOwner裁定は未実施として分けて報告する。

## 対象外

- GitHubへのpush、PR作成・コメント、main/master統合、外部Skill配置、旧Skill削除、Productivity-Skill同期実行。
- 実クラウド独立QAの実施、正式Quality LoopのOwner裁定、既存case正本やeventsの変更。
- 現在の元checkoutにある既存削除・未追跡ファイルの整理・復元・上書き。

## 承認状態

本計画はユーザーから「実装して」と明示承認を受けた。承認対象は本書に記載した範囲に限る。実装は隔離worktree上で進行中であり、GitHub push、PR、外部Skill配置、旧Skill削除、実クラウドQA、Owner裁定は含まない。
