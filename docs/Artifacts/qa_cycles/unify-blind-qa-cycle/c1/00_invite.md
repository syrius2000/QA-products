# 独立QAレビュー依頼: blind-qa-cycle統合ライフサイクル

- **Repository:** `syrius2000/QA-products`
- **Branch:** `codex/blind-qa-cycle-remote-qa`
- **Start mode:** `post-change`
- **Preparation plan:** なし（事後開始）
- **Baseline commit:** `1d696f917ce03a1a6072fdafcb8c05c7259de54d`
- **Reviewed commit:** `5112d59abf3a38850723b0599cc08f96385c06b5`
- **Baseline rationale:** `branch_start`。新topic branch作成直前の`master` HEADを固定した。新branchはこのSHAから始まり、Reviewedより前に別commitはない。
- **Baseline subject:** `docs: archive completed QA artifacts and OpenSpec changes`
- **Reviewed subject:** `Yip: WIP QA review unify-blind-qa-cycle`
- **Requirements fingerprint:** `d08e1457ec6e25b00f18e0fd2b7ad0c3fa956b784dd78ec734da395ccf9d2f1c`
- **Output dir:** `docs/Artifacts/qa_cycles/unify-blind-qa-cycle/c1/`
- **Cycle:** `1`
- **Audience:** `cloud`
- **Remote visibility:** `pushed`
- **Diff:** `git diff 1d696f917ce03a1a6072fdafcb8c05c7259de54d 5112d59abf3a38850723b0599cc08f96385c06b5`
- **Focus packs:** `path-sanitization`
- **Fingerprint algorithm:** AC行を`AC-NNN: <criterion>`形式で番号順に並べ、LFで結合し末尾にLFを付けたUTF-8バイト列のSHA-256。

## 受入基準（全文・順序固定）

- **AC-001:** Reviewerは実装担当から独立し、招待で固定されたBaseline..Reviewedの差分と全受入基準を確認する。
- **AC-002:** 実装前は計画をYip commitへ固定し、実装後の新branch開始時は切替前HEAD、または既存checkpointをBaselineとし、branch・Baseline・Reviewedの完全SHAをinviteに記録する。
- **AC-003:** LocalとCloudは同じAC・Finding・Gate契約を使い、Reviewerは指定SHA上のReviewer資料hashを照合し、指定された4成果物だけを作成する。
- **AC-004:** Cloud QAではReviewed commitとinvite commitだけをtopic branchへpushし、main/masterへのmergeやforce-pushを行わない。Local reviewはpushしない。
- **AC-005:** Implementerは利用者が指定したFindingだけに対応するYip response commitを作り、前cycleを変更せず、前回ReviewedをBaselineとする新cycleでReviewerに再確認を求める。
- **AC-006:** Note modeは一致を確認したcycle情報と最終Gateを参照し、6問への人の回答を逐語保存する。既存Noteを上書きせず、NoteでGate・Finding状態・Owner判断を変更しない。
- **AC-007:** Cycle終結時にFinding状態、残余リスク、最終Gate、SHA、Note pathを記録し、Owner判断・merge・配備から分離する。
- **AC-008:** quality-qa、quality-review、quality-responseの用途、データ、CLI契約を変更せず、blind-qa-cycleから用途に応じて案内する。
- **AC-009:** ignoredな.agents配置はPlan 039の承認前に変更せず、配置未完了を明示する。

## 参照Reviewer資料（Reviewed SHAから読むこと）

- `quality-loop/skills/blind-qa-cycle/SKILL.md`
  - 期待SHA-256: `186dc5d68efed35f365a19fda33ece05d5b2014aff77ae54ee5a86fe1f9d8feb`
- `quality-loop/skills/quality-qa/SKILL.md`
  - 期待SHA-256: `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261`
- `quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md`
  - 期待SHA-256: `98b82a70ef5976c149a18bda279970a3f2523214426f490667a7725c786d20f2`
- 指定SHAで資料を取得できない、またはhash不一致なら製品レビューを止め、Gate=`HOLD`とHigh provenance Findingを記録する。別branchやHEADの資料で代用しない。

## 変更パスと差分概要

```text
A docs/Artifacts/implementation_plan_038_1006.md
A docs/Artifacts/implementation_plan_039_1007.md
A openspec/changes/unify-blind-qa-cycle/.openspec.yaml
A openspec/changes/unify-blind-qa-cycle/design.md
A openspec/changes/unify-blind-qa-cycle/implementation-record.md
A openspec/changes/unify-blind-qa-cycle/proposal.md
A openspec/changes/unify-blind-qa-cycle/specs/blind-qa-cycle/spec.md
A openspec/changes/unify-blind-qa-cycle/tasks.md
M quality-loop/skills/blind-qa-cycle/SKILL.md
M quality-loop/skills/blind-qa-cycle/references/audience_channels.md
M quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md
M quality-loop/skills/blind-qa-cycle/references/git_wip_flow.md
M quality-loop/skills/blind-qa-cycle/references/machine_schema.md
```

差分概要: 13 files changed, 663 insertions(+), 40 deletions(-)

## Requester notes

- この依頼は上記Baseline..Reviewedだけを対象にする。実装者の説明を根拠にせず、Reviewer自身がdiff、Spec、契約、hash、Evidenceを確認する。
- Plan 039はこのcheckoutのignoredな`.agents/skills/blind-qa-cycle/`を調査したローカル配置計画であり、このbranchではそのignored配置を変更していない。OpenSpec task 2.3は未完了のまま明示されている。未完了と承認境界を確認し、統合完了を過大評価しないこと。
- Plan 039およびPlan 038は今回のreview diffに含まれるArtifactである。今回のQA依頼は配置変更の承認ではない。
- 必須確認: `openspec validate --strict unify-blind-qa-cycle`をReviewed tree上で実行し、exit statusと結果を記録する。未実行・失敗ならPASSにしない。
- Product testは指定しない。必須確認以外の任意checkは実行可否・理由を記録する。Install、依存追加、credentialアクセス、許可されていないnetworkアクセスは行わない。

## Focus pack: path-sanitization

- Reviewed treeの変更内容に実在する個人名、OS絶対パス（`/Users/...`等）、Markdownの`file:///`リンク、Windows drive path、UNC pathが混入していないか確認する。
- 検査ルール・例示内の禁止パターン文字列は、実パスとして使われていない限りFindingにしない。
- scopeはReviewed commit treeの内容。Git author metadataや過去履歴の書換えは対象外。

## Reviewer contract

- Reviewerは実装担当と独立していること。同じ会話・実装担当からの自己レビューは受理しない。
- 対象は固定SHA間の`git diff <Baseline> <Reviewed>`。別SHA、HEAD、main/masterで代用しない。
- Review結果は必ず日本語で、指定Output dirに次の4ファイルのみ作成する: `01_review.md`、`02_tasks.md`、`03_machine.json`、`STATUS.md`。招待、計画、製品ファイル、他cycleを編集しない。
- 全ACを全文・同じ順序で転記し、判定をPASS/FAIL/UNVERIFIEDとEvidenceで説明する。
- Findingは実差分から確認した不一致に限る。各FindingにはID、Severity、OPEN/CLOSED、Evidence（path:line）、期待動作、影響、修正案、repair_surfaceを記す。修正対象となるFindingごとにtaskを作り、Finding ID、対象path、action、観察可能なdone_when、verifyと期待結果を記す。High Findingは必ずtaskを持つ。
- 必須checkがFAILならGate=FAIL。必須checkが未実施、実行不能、errorならPASS不可。SHA/hash/範囲不一致はHOLD。GateはPASS/HOLD/FAIL/INCONCLUSIVEから選ぶ。
- Reviewerは製品コードを修正せず、ACCEPT/ARCHIVE、Owner判断、merge、deployを行わない。

### `01_review.md` template

```markdown
# 独立QAレビュー

- Repository: `syrius2000/QA-products`
- Branch: `codex/blind-qa-cycle-remote-qa`
- Baseline: `1d696f917ce03a1a6072fdafcb8c05c7259de54d`
- Reviewed: `5112d59abf3a38850723b0599cc08f96385c06b5`
- Cycle: `1`
- Audience: `cloud`
- Remote visibility: `pushed`
- Focus packs: `path-sanitization`
- Requirements fingerprint: `d08e1457ec6e25b00f18e0fd2b7ad0c3fa956b784dd78ec734da395ccf9d2f1c`
- Gate: `PASS | HOLD | FAIL | INCONCLUSIVE`

## 結論

## 参照Skill確認
<!-- 各資料の期待hash、観測hash、読取状態 -->

## 受入基準
<!-- AC-001から全基準を全文・同じ順序で転記し、判定とEvidenceを付ける -->

## Findings
<!-- 不一致のみ。ID/Severity/Status/Evidence(path:line)/Expected/Impact/Action/repair_surface -->

## Re-QA
- 推奨Baseline: `5112d59abf3a38850723b0599cc08f96385c06b5`
- 再確認対象: <Finding IDs>
```

### `02_tasks.md` template

```markdown
# 修復タスク

- [ ] T-01 (closes: QA-AREA-H01) severity=High; path=`path/to/file`; action=<具体的修正>; done_when=<観察可能な完了条件>; verify=<確認手順と期待結果>
```

対応不要のFindingがある場合はtaskを省略し、その理由をreviewに記録する。1 taskへ独立修正をまとめない。

### `03_machine.json` required shape

```json
{
  "schema": "blind-qa-cycle-v1",
  "topic": "unify-blind-qa-cycle",
  "cycle": 1,
  "start_mode": "post-change",
  "baseline": "1d696f917ce03a1a6072fdafcb8c05c7259de54d",
  "reviewed": "5112d59abf3a38850723b0599cc08f96385c06b5",
  "audience": "cloud",
  "remote_visibility": "pushed",
  "requirements_fingerprint": "d08e1457ec6e25b00f18e0fd2b7ad0c3fa956b784dd78ec734da395ccf9d2f1c",
  "gate": "HOLD",
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "text": "<inviteのAC全文>",
      "result": "UNVERIFIED",
      "evidence": "<path:lineまたは未実施理由>"
    }
  ],
  "reviewer_materials": [
    {
      "path": "quality-loop/skills/blind-qa-cycle/SKILL.md",
      "expected_sha256": "186dc5d68efed35f365a19fda33ece05d5b2014aff77ae54ee5a86fe1f9d8feb",
      "observed_sha256": "<Reviewed SHAから計算した値>",
      "read": true
    }
  ],
  "focus_packs": ["path-sanitization"],
  "findings": [],
  "tasks": []
}
```

- machine JSONには9件すべての受入基準、全参照Reviewer資料のhash、全Finding/task対応を入れる。3つの資料がすべてreviewer_materialsに必要。
- `STATUS.md`はGateを示す単一語（`PASS`、`HOLD`、`FAIL`、`INCONCLUSIVE`）だけとし、machine JSONのgateと一致させる。

### 提出とGit帰着

- 提出前に4ファイルの存在、JSON構文、Gate一致、ACとfingerprint、Finding/task対応を照合する。
- Audience=cloud。現在branchがmain/masterでなく、worktreeがReviewer成果物4ファイル以外cleanの場合に限り、4ファイルのみをstageしてcommitする: `Yip: QA review unify-blind-qa-cycle c1`、trailer `Blind-QA-Review-Artifacts: unify-blind-qa-cycle`。続けてtopic-only `git push -u origin HEAD`。製品・招待・Plan 039ファイルはstageしない。
- push不能ならrepo永続化を主張せず、4本文を返して`ingest-needed`を明記する。
- 最終返信はGate、Output dir、Blocking/Task count、Artifacts SHAまたは`ingest-needed`を5項目以内に報告する。
