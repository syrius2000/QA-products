# 独立QAレビュー

- Repository: `syrius2000/QA-products`
- Branch: `codex/blind-qa-cycle-remote-qa`
- Start mode: `post-change`
- Preparation plan: なし（事後開始）
- Baseline: `1d696f917ce03a1a6072fdafcb8c05c7259de54d`
- Reviewed: `5112d59abf3a38850723b0599cc08f96385c06b5`
- Cycle: `1`
- Audience: `cloud`
- Remote visibility: `pushed`
- Focus packs: `path-sanitization`
- Requirements fingerprint: `d08e1457ec6e25b00f18e0fd2b7ad0c3fa956b784dd78ec734da395ccf9d2f1c`
- Gate: `FAIL`

## 結論

- Blocking 1: `QA-FLOW-M01`。新branch開始時の`branch_start` Baselineを主要cloud手順とOpenSpecは許可する一方、共有`Mode: invite`と補助referenceの一部がpost-changeをcheckpoint必須としており、AC-002のライフサイクル契約が内部矛盾している。
- Blocking 2: 必須check `openspec validate --strict unify-blind-qa-cycle` は独立Reviewer環境で `NOT_RUN`。Reviewer runtimeに`openspec`実行ファイルがなく、依頼でinstall/依存追加が禁止されているため起動していない。実装記録の成功主張は独立再実行の代替にしない。
- path-sanitization: Baseline..Reviewedの13変更ファイルを検査し、実パスとしての`/Users/example/...`、`/home/...`、Markdown `file:///`、Windows drive path、UNC pathは検出しなかった。Git author metadataはscope外。
- Plan 039 / `.agents`: OpenSpec task 2.3は未完了で、配置未完了・承認待ちが明示されている。Git差分には`.agents`がないが、ignoredなローカル実体そのものはReviewed commitからは独立検証不能。

## 参照Skill確認

| Path | Expected SHA-256 | Observed SHA-256 | Read |
|---|---|---|---|
| `quality-loop/skills/blind-qa-cycle/SKILL.md` | `186dc5d68efed35f365a19fda33ece05d5b2014aff77ae54ee5a86fe1f9d8feb` | `186dc5d68efed35f365a19fda33ece05d5b2014aff77ae54ee5a86fe1f9d8feb` | true |
| `quality-loop/skills/quality-qa/SKILL.md` | `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261` | `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261` | true |
| `quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md` | `98b82a70ef5976c149a18bda279970a3f2523214426f490667a7725c786d20f2` | `98b82a70ef5976c149a18bda279970a3f2523214426f490667a7725c786d20f2` | true |

3件ともReviewed SHAから取得して一致したため、provenance不一致によるHOLDはない。

## 必須check

- Check: `openspec validate --strict unify-blind-qa-cycle`
- Required: true
- Runtime: reviewer container
- argv: `["openspec","validate","--strict","unify-blind-qa-cycle"]`
- cwd: Reviewed treeでの実行が必要
- Status: `NOT_RUN`
- Exit status: `N/A`（process未起動）
- Result: `openspec` executableがReviewer runtimeに存在しない。依頼でinstall・依存追加が禁止されているため導入しなかった。通常`git clone`も当該runtimeの外向きDNS制約で利用できず、固定SHA資料・diff・remote DAGはGitHub repository APIから検証した。
- Prior implementation evidence: `openspec/changes/unify-blind-qa-cycle/implementation-record.md:66`には成功記録があるが、実装者側記録なので独立実行の代替とはしない。
- Consequence: 必須check未実施のため、このFindingが修復されても再QAでcheckが成功するまでGate=PASSにはできない。

## 受入基準

- AC-001: Reviewerは実装担当から独立し、招待で固定されたBaseline..Reviewedの差分と全受入基準を確認する。 | 判定: `PASS` | Evidence: Reviewer process: fixed Baseline..Reviewed was independently fetched/compared; merge-base=Baseline, ahead_by=1, 13 changed files; all 9 ACs are assessed here. Reviewer did not author Reviewed.
- AC-002: 実装前は計画をYip commitへ固定し、実装後の新branch開始時は切替前HEAD、または既存checkpointをBaselineとし、branch・Baseline・Reviewedの完全SHAをinviteに記録する。 | 判定: `FAIL` | Evidence: quality-loop/skills/blind-qa-cycle/SKILL.md:123-126 permits eligible branch_start, but SKILL.md:207 still requires a valid checkpoint for post-change; references/audience_channels.md:3,11 and references/git_wip_flow.md:19,97 also describe checkpoint-only post-change, conflicting with spec.md:35-37.
- AC-003: LocalとCloudは同じAC・Finding・Gate契約を使い、Reviewerは指定SHA上のReviewer資料hashを照合し、指定された4成果物だけを作成する。 | 判定: `PASS` | Evidence: openspec/changes/unify-blind-qa-cycle/design.md:61-65 and quality-loop/skills/blind-qa-cycle/SKILL.md:275-303; all three pinned reviewer-material SHA-256 values matched Reviewed exactly. Artifact commit is constructed from exactly 01_review.md, 02_tasks.md, 03_machine.json, STATUS.md.
- AC-004: Cloud QAではReviewed commitとinvite commitだけをtopic branchへpushし、main/masterへのmergeやforce-pushを行わない。Local reviewはpushしない。 | 判定: `PASS` | Evidence: Remote DAG before reviewer artifact commit: master=1d696f9..., Reviewed 5112d59... is its direct child, invite 33523ef... is the direct child of Reviewed; compare Reviewed..invite contains only c1/00_invite.md. quality-loop/skills/blind-qa-cycle/SKILL.md:127-136 and :156-160 preserve topic-only cloud push / local no-push.
- AC-005: Implementerは利用者が指定したFindingだけに対応するYip response commitを作り、前cycleを変更せず、前回ReviewedをBaselineとする新cycleでReviewerに再確認を求める。 | 判定: `PASS` | Evidence: quality-loop/skills/blind-qa-cycle/SKILL.md:325-330 and references/git_wip_flow.md:63-71.
- AC-006: Note modeは一致を確認したcycle情報と最終Gateを参照し、6問への人の回答を逐語保存する。既存Noteを上書きせず、NoteでGate・Finding状態・Owner判断を変更しない。 | 判定: `PASS` | Evidence: quality-loop/skills/blind-qa-cycle/SKILL.md:336-342 and :344-378.
- AC-007: Cycle終結時にFinding状態、残余リスク、最終Gate、SHA、Note pathを記録し、Owner判断・merge・配備から分離する。 | 判定: `PASS` | Evidence: quality-loop/skills/blind-qa-cycle/SKILL.md:380-389.
- AC-008: quality-qa、quality-review、quality-responseの用途、データ、CLI契約を変更せず、blind-qa-cycleから用途に応じて案内する。 | 判定: `PASS` | Evidence: quality-loop/skills/blind-qa-cycle/SKILL.md:19-25 routes by purpose; Baseline..Reviewed changed-path list contains no quality-loop/skills/quality-qa/, quality-review/, or quality-response/ files.
- AC-009: ignoredな.agents配置はPlan 039の承認前に変更せず、配置未完了を明示する。 | 判定: `UNVERIFIED` | Evidence: openspec/changes/unify-blind-qa-cycle/tasks.md:12 leaves task 2.3 open; implementation-record.md:12-14,30,62,71 states .agents is ignored, unchanged, and approval-pending. Baseline..Reviewed contains no .agents path. However the actual ignored checkout contents are outside Git and cannot be independently reconstructed from Reviewed, so physical local non-modification is not fully verifiable.

## Findings

### QA-FLOW-M01 — branch_startとcheckpoint必須記述が矛盾

- Severity: `Medium`
- Status: `OPEN`
- Requirement: AC-002
- Evidence:
  - `quality-loop/skills/blind-qa-cycle/SKILL.md:123-126` — 同一の明示cloud操作で新branchを作る場合、切替前HEADを`branch_start` Baselineとして許可する。
  - `quality-loop/skills/blind-qa-cycle/SKILL.md:207` — `Mode: invite`はpost-changeで「valid checkpoint Baseline」を要求し、branch_start例外を記載していない。
  - `quality-loop/skills/blind-qa-cycle/references/audience_channels.md:3,11` — 実装済みpost-changeをcheckpoint経路としてのみ説明する。
  - `quality-loop/skills/blind-qa-cycle/references/git_wip_flow.md:19,97` — post-changeはcheckpointを使い、無ければ停止する旨を一般則として記載する一方、同文書`:42`ではbranch_start例外を許可している。
  - `openspec/changes/unify-blind-qa-cycle/specs/blind-qa-cycle/spec.md:35-37` — 明示cloud新branchのbranch-start Scenarioを要求している。
- Expected: `cloud`から入ったpost-changeでは、cloud step 3で適格性を確認済みの`branch_start` Baselineを共有invite処理と全referenceが一貫して受け入れる。checkpoint必須はbranch_start例外に該当しない経路へ限定する。
- Impact: 同一Skill内の入口によって合法なpost-change cycleを受理したり拒否したりし得る。今回のc1自身が`branch_start`で生成されているため、契約の自己整合性と再現性を損なう。
- Action: `Mode: invite` step 5、`audience_channels.md`、`git_wip_flow.md`の一般記述を、`cloud`で事前に検証済みのeligible branch-startを明示的に許可する表現へ統一する。branch-startの限定条件（同一明示cloud操作、切替前HEAD固定、branch開始commit、Reviewed前に別commitなし）は緩和しない。
- repair_surface: `docs`

## Re-QA

- 推奨Baseline: `5112d59abf3a38850723b0599cc08f96385c06b5`
- 再確認対象: `QA-FLOW-M01`
- 必須: 修復後のReviewed tree上で `openspec validate --strict unify-blind-qa-cycle` を独立Reviewerが実行し、exit code 0を確認する。
