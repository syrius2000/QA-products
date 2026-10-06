---
name: blind-qa-cycle
description: >
  Explicit-only independent blind QA lifecycle for local peer agents or
  GitHub/cloud agents. Supports prepare, checkpoint, cloud (Reviewed+invite+topic push+path),
  cloud re-qa, local, invite, respond, review (cloud may commit+push QA artifacts only),
  ingest (requester writes back review artifacts), and human note. Artifacts under
  docs/Artifacts/qa_cycles/<topic>/c<N>/. Use ONLY when explicitly invoked.
  Never auto-run after commits or OpenSpec apply. Does not Owner-decide, fix
  product code, or merge to main. Topic-only push only for cloud/cloud re-qa/
  cloud review artifacts/ingest.
disable-model-invocation: true
---

# blind-qa-cycle — Independent Blind QA Cycle

このSkillは、Yip commitと固定SHAを使い、監査ブランチ上で独立QAを開始から終結まで明示的に進める。

## 適用範囲と他QA Skillとの使い分け

- 監査ブランチ上の独立レビュー、固定SHA、Reviewer成果物DIR、Yip commitでのFinding対応・再QAには、この `blind-qa-cycle` を明示起動する。
- 通常のQA依頼・結果確認・承認後のローカル修正・再QAには `quality-qa` を使う。同Skillの単一Markdown成果物を本Skillの4成果物契約へ移さない。
- 正式Quality Loop caseのReviewer工程には `quality-review`、Implementer応答には `quality-response` を使う。case正本・CLI状態を本Skillへ取り込んだり変更したりしない。
- Reviewerは実装担当とは独立した別担当でなければならない。実装した同じチャットで `review` を実行しない。
- Reviewerは固定SHAの依頼指示とReviewer指定資料を読み、実行check契約があれば環境・リポジトリ規則の許す範囲で実行する。実行環境が使えない場合はPASSにせず、理由と未検証を残す。

## Modes

| User intent | Mode |
| :--- | :--- |
| `/blind-qa-cycle prepare` | 実装前に受入基準を`00_plan.md`へ記録し、計画commitを後続レビューのBaselineにする |
| `/blind-qa-cycle checkpoint` | 事前計画なしの実装前WIPを固定するBaseline commit (`Blind-QA-Checkpoint`) |
| `/blind-qa-cycle cloud` | 実装後にReviewed Yip → 招待確定 → invite commit → **topic-only push** → **path handoff** |
| `/blind-qa-cycle cloud re-qa` | Re-QA: Baseline = previous cycle Reviewed; skip new checkpoint requirement |
| `/blind-qa-cycle local` | `invite` with Audience=`local` (no push; full invite body; do not paste to Cloud) |
| `/blind-qa-cycle invite`, 「QAメタデータ」 | `invite` (ask Audience if omitted) |
| `/blind-qa-cycle review`, 依頼ブロック／`00_invite.md`／相対パス | `review`（cloud は **QA 成果物のみ** commit+topic push 可） |
| `/blind-qa-cycle ingest` | 依頼側: Cloud から受け取った4ファイルを Output dir へ書き、artifact commit+topic push |
| `/blind-qa-cycle respond <cycle>` | Implementerが指定Findingへ対応し、Yip response commitを次cycleへ渡す |
| `/blind-qa-cycle note` | QA cycleに紐づく人間記入のHuman Understanding Noteを作成する |
| Ambiguous | Ask once; default **`invite`** |

## サイクル全体の流れ

**実装前準備ができる場合（推奨）**

```text
cleanなtopic branch → prepare (00_plan.mdをYip commit / Baseline確定)
                   → 実装側が開発
                   → cloud または local (Reviewed Yip / 招待確定)
                   → 独立Reviewer → respond (Finding別Yip commit) → 再QA
                   → note → 監査cycle終結
```

**実装が先に完了している場合**は、既存のcheckpointまたは前cycleのReviewedをBaselineとして、staged-onlyのReviewed Yip commitから開始する。招待には事後開始とBaseline選定理由を記録する。

QA終結はOwner受入や`main`/`master`へのmergeを意味しない。merge・配備・外部Skill配置は別の判断・承認工程とする。

## Audience (local vs cloud)

Same skill, same Output dir contract. Channel differs only in **remote visibility** and handoff form.

| Audience | Who runs `review` | SHA requirement | Default handoff |
| :--- | :--- | :--- | :--- |
| `local` | Other local agent / other chat on same clone | SHAs must exist **locally**. Unpushed OK. | Full invite body. **Do not paste to GitHub Cloud.** |
| `cloud` | GitHub / remote Cloud Agent | Baseline **and** Reviewed (and invite commit when path handoff) must be ancestors of `origin/<branch>` after fetch when possible. | **Relative path** to `00_invite.md` (preferred). Full body only if push failed. |

- If audience omitted (plain `invite`): ask once. Do not guess.
- `/blind-qa-cycle cloud` / `local` / `cloud re-qa` fix Audience without asking.
- Record in invite: `Audience` and `Remote visibility: local-only | pushed`.
- **Never paste a `local-only` invite to GitHub Cloud.**

Details: [`references/audience_channels.md`](references/audience_channels.md)

## Yip commitと作業領域の共通保護

Read [`references/git_wip_flow.md`](references/git_wip_flow.md) for the full commit and recovery rules.

```text
existing topic branch
  → /blind-qa-cycle prepare    # optional: pre-implementation criteria + plan Baseline
  → implement per plan (skill idle)
  → /blind-qa-cycle cloud      # Reviewed Yip → finalized invite → push → path

Without pre-implementation preparation:
existing topic branch
  → /blind-qa-cycle checkpoint   # clean Baseline local commit (staged pre-change WIP)
  → implement per plan (skill idle); stage only the review set
  → /blind-qa-cycle cloud        # Reviewed Yip → invite → invite commit → topic push → path
```

An explicit `prepare`, `checkpoint` or `cloud` invocation authorizes only the mode's named Yip commits; `cloud` also authorizes the invite-only follow-up commit and topic-only push. Inspect and report exact paths before any commit. Stop on unrelated staged/unstaged/untracked paths. Never use `git add -A` or stage product files on the user's behalf. Each generated QA artifact commit stages only its named artifact path.

## Mode: prepare

Create the QA plan and freeze acceptance criteria **before implementation**. This mode creates only a preparation artifact and its Yip commit; it does not implement product code, finalize a review invite, fetch, push, or start a review.

1. Require an explicit topic, repository root, and a non-`main`/`master` branch. Confirm the worktree, index, and untracked set are clean before creating the cycle.
2. Ask for or derive from the request the purpose, in-scope paths, all acceptance criteria, and required checks. Assign stable `AC-001`… IDs and preserve the exact criterion text.
3. Select the next cycle `docs/Artifacts/qa_cycles/<topic>/c<N>/`; never reuse an existing cycle folder.
4. Write `00_plan.md` with repository, branch, preparation HEAD, cycle, scope, purpose, criteria, required checks, and the statement that review has not started. Do not invent the plan commit's own SHA inside the file.
5. Show the generated path and exact staged diff. Stage only `00_plan.md` and commit `Yip: QA plan <topic> c<N>` with trailer `Blind-QA-Plan: <topic>`. The resulting plan commit SHA is the Baseline for implementation and later review.
6. If the checkout changes during preparation, if unexpected files appear, or if the one-file staged set cannot be guaranteed, stop before commit and preserve all existing work.
7. Return the Baseline SHA and cycle path. Do not claim that QA was performed. The implementation-side `cloud` or `local` flow later creates the final `00_invite.md` from this frozen plan and the Reviewed SHA.

## Mode: checkpoint

Create a **clean Baseline** local commit on the existing topic branch before the next implementation increment when no `prepare` plan exists. Do **not** rename this mode to `setup`.

1. Require a topic other than `main` / `master`, resolve the topic slug, and verify the current branch and repository root.
2. Require at least one staged change and zero unstaged or untracked changes. Otherwise stop with exact status and stage/clean-up guidance; do not stage or discard anything.
3. Show the staged path list and staged diff summary. On this explicit mode invocation, commit only the existing index with subject `Yip: WIP QA checkpoint <topic>` and trailer `Blind-QA-Checkpoint: <topic>`.
4. Record the resulting full SHA in the confirmation. The commit trailer is the branch-local lookup key used by `/blind-qa-cycle cloud`.
5. Do not write QA cycle artifacts, fetch, push, or start a review in checkpoint mode.

## Mode: cloud (shortcut)

Purpose: one command after implementation for **topic-branch cloud QA handoff** — Reviewed commit, invite artifact, invite commit, topic push, path handoff. No main merge.

1. Set Mode=`invite`, Audience=`cloud` (do not ask).
2. `branch=$(git branch --show-current)`.
   - If `branch` is `main` or `master`: **fail-fast STOP**. Do not create Reviewed/invite commits and do not push. Tell the user to switch to a non-`main`/`master` topic branch first. Confirmation does **not** override this guard.
3. Resolve topic and inspect cycle plans. If exactly one unused `Blind-QA-Plan: <topic>` commit for the prepared cycle is an ancestor of HEAD, use that plan commit as **Baseline** and reuse its cycle directory. If a candidate is ambiguous, already has a final invite, or is not an ancestor, stop and ask the user to resolve the cycle; do not silently switch baselines. With no prepared plan, use the newest matching `Blind-QA-Checkpoint: <topic>` in current branch first-parent history and mark `start_mode=post-change`. If no checkpoint exists, a branch created in this same explicit `/blind-qa-cycle cloud` operation may use the exact pre-branch HEAD as Baseline only if that SHA was captured before switching branches, is the branch's starting commit, and no branch commit was made before the reviewed commit. Record the source branch and `branch_start` rationale in the invite. Otherwise stop and direct the user to `/blind-qa-cycle checkpoint`. Never infer Baseline from an unrelated tip or QA cycle.
4. **Reviewed WIP commit:** If the index has staged changes and the worktree has no unstaged or untracked changes, report the staged paths and create one post-change commit with subject `Yip: WIP QA review <topic>` and trailer `Blind-QA-Reviewed: <topic>`. If a matching reviewed commit is already at `HEAD` (rerun after partial success), reuse it. If neither condition holds, stop without committing.
5. Set Reviewed to that commit and verify Baseline and Reviewed SHAs locally. Collect subjects, `git diff --name-status`, and `git diff --stat` for the invite (orientation only; review inspects the real diff).
6. For a prepared cycle, read its tracked `00_plan.md` and carry forward the exact purpose, scope, acceptance criteria, and required checks; set `start_mode=prepared` and record plan path + commit SHA. Otherwise choose the next unused cycle folder `docs/Artifacts/qa_cycles/<topic>/c<N>/` and record `start_mode=post-change` plus the checkpoint or branch-start rationale. Write `00_invite.md` only after Reviewed is fixed, so invite and plan materials are not in Baseline..Reviewed.
7. **Invite follow-up commit:** Stage only the new `00_invite.md` (and directory placeholders if needed). Commit with subject `Yip: QA invite <topic> c<N>` and trailer `Blind-QA-Invite: <topic>`. Do not amend Reviewed. Record Invite commit SHA separately from Reviewed.
8. Prefer `git fetch origin` (warn if fetch fails; use existing `origin/<branch>` refs).
9. **Topic-only push (authorized by this explicit `/blind-qa-cycle cloud` invocation):**
   - Run `git push -u origin HEAD` for the **current topic branch only**.
   - **Never** merge to `main` / `master`. **Never** force-push unless the user gave a separate explicit force-push order in the same turn.
10. **Preflight after push (or against existing origin):**
    - `git merge-base --is-ancestor <baseline> origin/<branch>`
    - `git merge-base --is-ancestor <reviewed> origin/<branch>`
    - Prefer also: invite commit is ancestor of `origin/<branch>` when path handoff is used.
11. **On push or preflight FAIL:** Keep local Reviewed and invite commits. Do **not** claim path handoff works. Show topic-only push help and emit **full invite body** as fallback paste. Stop. Do not merge to main.
12. **On SUCCESS:** Set `Remote visibility: pushed`, optional `Tracking: origin/<branch>@<tip-sha>`. Emit Cloud handoff as **one relative path line** (preferred):

    ```text
    docs/Artifacts/qa_cycles/<topic>/c<N>/00_invite.md
    ```

    Optionally show Reviewed / Invite / Baseline SHAs in ≤5 bullets. Do not dump the full invite body unless fallback. Do not `gh pr comment` unless explicitly asked.

## Mode: cloud re-qa

Required when closing findings from a frozen cycle (`HOLD` / `FAIL`).

1. Audience=`cloud`. Inputs: topic, previous cycle path (default: latest `cN` under topic), Finding IDs to close (from previous `02_tasks.md` / review), Reviewed tip (usually current HEAD after repair Yip commit).
2. `branch=$(git branch --show-current)`. If `branch` is `main` or `master`: **fail-fast STOP** (same guard as `cloud` step 2). No Reviewed/invite commit and no push.
3. **Baseline default** = previous cycle's **Reviewed** SHA (not a new checkpoint). Do **not** require `Blind-QA-Checkpoint` for this mode.
4. If repair is not yet committed: same staged-clean rules as `cloud` step 4 to create Reviewed; else reuse HEAD if it is the repair tip.
5. Create **`c{N+1}`**; never mutate frozen `cN`.
6. Continue with invite file → invite commit → topic-only push → path handoff (same as `cloud` steps 6–12).

## Mode: local (shortcut)

1. Set Audience=`local`, `Remote visibility: local-only`.
2. If exactly one unused prepared plan exists on the current branch, reuse its Baseline and cycle directory; otherwise require the matching checkpoint for a post-change cycle. Run standard invite without origin ancestor check or push.
3. Emit **full invite body** with explicit **Do not paste to GitHub Cloud.**

## Output directory (canonical)

```text
docs/Artifacts/qa_cycles/<topic>/c<N>/
  00_plan.md (prepared cycles only; implementation-side input, not Reviewer output)
  00_invite.md
  01_review.md
  02_tasks.md
  03_machine.json
  STATUS.md
  04_human_understanding.md (optional; human-authored, not Reviewer output)
```

- `<topic>`: OpenSpec change name, else short kebab-case slug
- Re-QA always creates **`c{N+1}`**; freeze prior cycle
- Artifact置き場の規則: [`AGENTS.md`](../../../AGENTS.md)
- JSON keys: [`references/machine_schema.md`](references/machine_schema.md)

## Focus packs

Load only packs named in the invite:

- [`references/focus_math_definitions.md`](references/focus_math_definitions.md)
- [`references/focus_path_sanitization.md`](references/focus_path_sanitization.md)
- [`references/focus_openspec_coherence.md`](references/focus_openspec_coherence.md)
- [`references/focus_provenance_plans.md`](references/focus_provenance_plans.md)

## Reviewer Skillと依頼基準の固定

- 新しい依頼を作る実装側は、Reviewed SHAにある次の3ファイルを読み取り、各ファイルのSHA-256を取得してinviteへ記録する。Cloud Reviewerは必ず同じReviewed SHAから読み、記録hashと照合する。
  - `quality-loop/skills/quality-qa/SKILL.md`
  - `quality-loop/skills/blind-qa-cycle/SKILL.md`
  - `quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md`
- 対象commitにファイルがない、取得できない、またはhashが合わない場合は、推測で補わずGate=`HOLD`、Highのprovenance findingと修復taskを4成果物へ記録する。別のbranchやHEADにある同名ファイルで代用しない。
- inviteには目的・受入基準の全件を`AC-001`から順番に、原文のまま列挙する。`01_review.md`と`03_machine.json`にも同じID・原文・件数・順序を保持し、基準ごとの判定とEvidenceを記録する。欠落・重複・追加・順序変更・原文変更は提出前に修正する。
- Cloud Reviewerは実装担当AIの説明を根拠にせず、固定差分と基準を自ら確認する。指摘はFindingごとに対象版のpath:line、期待動作、影響、対応案を記録し、対応が必要な各Findingを`02_tasks.md`のtaskへ結び付ける。High Findingは必ずtaskを持つ。

## Mode: invite

Used by `cloud` / `local` / plain invite. Plain invite does **not** create WIP commits or push unless entered via `cloud`.

1. Resolve **full** SHAs: `git rev-parse <baseline>` / `git rev-parse <reviewed>`. Fail if unresolved locally.
2. Resolve **Audience** (`local` | `cloud`). Ask once if missing (unless entered via shortcut).
3. For bare `invite` with Audience=`cloud` **without** going through Mode cloud's commit/push pipeline: run remote visibility gate only; on FAIL print push help and do not claim path handoff; on SUCCESS may emit path if `00_invite.md` is already on `origin/<branch>`, else full body.
4. For `audience=local`: set `Remote visibility: local-only`. Skip origin ancestor check (optional warn if unpushed).
5. Choose `topic` and start mode. Reuse the matching prepared plan's cycle directory and preserve its exact criteria when one unambiguous unused plan exists; otherwise use the next unused cycle and require a valid checkpoint Baseline for `post-change`. Re-QA uses the previous cycle's Reviewed SHA and a new cycle. Never overwrite an existing invite or frozen cycle.
6. Collect **Requester notes** (or `(none)`). Do not rewrite focus pack bodies.
7. Select focus pack id(s).
8. Read [`references/cloud_output_contract.md`](references/cloud_output_contract.md). For cloud path handoff, the reviewer loads `00_invite.md` from git; still keep the invite file self-contained (inline focus criteria and output templates inside `00_invite.md`).
9. Write `00_invite.md` with required fields below. **Handoff:**
   - cloud + pushed + invite on origin → emit **relative path only**
   - otherwise → emit one fenced full markdown block

```markdown
# 独立 QA レビュー依頼: <title>

- **Repository:** `syrius2000/agentic-evidence-analysis`
- **Branch:** `<branch>`
- **Start mode:** `prepared` | `post-change` | `re-qa`
- **Preparation plan:** `<repo-relative path and full commit SHA, prepared only>`
- **Baseline rationale:** `<plan commit / checkpoint commit / explicit new-branch start SHA / previous cycle Reviewed>`
- **Baseline commit:** `<full-sha>`
- **Reviewed commit:** `<full-sha>`
- **Requirements fingerprint:** `<sha256>`
- **Acceptance criteria:** `AC-001: <全文>` ...
- **Reviewer Skill:** `quality-loop/skills/blind-qa-cycle/SKILL.md` / SHA-256 `<hash>`
- **QA Skill:** `quality-loop/skills/quality-qa/SKILL.md` / SHA-256 `<hash>`
- **Output contract:** `quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md` / SHA-256 `<hash>`
- **Reviewed subject:** `<git log -1 --format=%s reviewed>`
- **Diff:** `git diff <baseline> <reviewed>`
- **Focus pack:** `<pack-ids>`
- **Output dir:** `docs/Artifacts/qa_cycles/<topic>/c<N>/`
- **Cycle:** `<N>`
- **Audience:** `local` | `cloud`
- **Remote visibility:** `local-only` | `pushed`
- **Baseline subject:** `<git log -1 --format=%s baseline>`
- **Changed paths:** `<git diff --name-status baseline reviewed>`
- **Diff summary:** `<git diff --stat baseline reviewed>`
- **Requester notes:**
  - <bullets or "(none)">

## 重点監査観点

<from selected focus pack references>

## Reviewer contract

- Write ONLY under Output dir: `01_review.md`, `02_tasks.md`, `03_machine.json`, `STATUS.md`. Do **not** modify `00_invite.md` or any product/code paths outside that Output dir.
- Create all four files in the specified Output dir in the QA checkout. Follow the exact templates and completeness checks in [`references/cloud_output_contract.md`](references/cloud_output_contract.md).
- Create the Output dir if it is absent; never overwrite a frozen prior cycle.
- Findings only in `01_review.md` (no long Aligned formula dumps); write the report in Japanese, preserving code identifiers in English.
- Every actionable finding must have a task; every High finding must have one. Each task identifies the finding ID, path, concrete completion condition, and verification/expected result.
- Chat final reply ≤5 bullets (Gate / Output dir / Blocking count / Task count / Next action / Artifacts git SHA or ingest-needed).
- **Do not** edit product code, change Baseline/Reviewed SHAs, merge to main, force-push, or Owner-decide (no ACCEPT/ARCHIVE).
- **Git 帰着（Audience=`cloud`）:** After the four files are complete, stage **only** those four paths under Output dir, commit `Yip: QA review <topic> c<N>` with trailer `Blind-QA-Review-Artifacts: <topic>`, then **topic-only** `git push -u origin HEAD`. This artifact push is authorized by explicit `/blind-qa-cycle review` with Audience=`cloud`.
- If the cloud environment **cannot** push or cannot write to a clone of the topic branch: do **not** claim repo persistence; return the four file bodies for requester `/blind-qa-cycle ingest`.
- If Baseline or Reviewed SHA is missing in this clone: do NOT review another tip; Gate HOLD with High provenance finding; still write the four artifacts (and attempt artifact commit/push or return bodies per above).
```

Required fields (fail invite if any missing): Repository, Branch, Start mode, both full SHAs, both commit subjects, requirements fingerprint, every acceptance criterion with stable ID and exact text, all three Reviewer Skill/contract paths and SHA-256 values, Diff, Focus pack, **Output dir**, Cycle, **Audience**, **Remote visibility**, changed paths, diff summary, Requester notes, Reviewer contract, complete inline output requirements and templates. Prepared cycles also require the plan path and full plan commit SHA; post-change cycles require a checkpoint or eligible branch-start Baseline rationale; re-qa cycles require the previous cycle path and Finding IDs.

1. Do not auto-run `gh pr comment` unless the user explicitly asks; then confirm before posting. Refuse posting when `Remote visibility: local-only`.
2. **Push policy:**
   - `/blind-qa-cycle cloud` / `cloud re-qa`: topic-only push of Reviewed+invite commits.
   - `/blind-qa-cycle review` with Audience=`cloud`: topic-only push of **QA artifact commit only** (four files under Output dir).
   - `/blind-qa-cycle ingest`: topic-only push of the same artifact commit after writing files locally.
   - `checkpoint` / `local` / plain `invite`: must not push.
   - Never merge to `main`. Force-push requires a separate explicit user order.

## Mode: review

1. Require invite metadata (message, `00_invite.md`, or a repo-relative path to `00_invite.md`). Missing SHA, Output dir, or Audience → stop.
2. Confirm you are not the implementer of the reviewed commit in this chat; if you are, refuse `review`.
3. Before reviewing code, read the three pinned Reviewer Skill/contract files from the exact Reviewed SHA and compare their SHA-256 values with `00_invite.md`. If any source cannot be read or the hash differs, write all four artifacts with Gate `HOLD`, a High provenance finding, and a task to supply the matching source; stop product review. Do not use the current branch tip as a substitute.
4. **SHA availability (before any code or math review):**
   - `git rev-parse <baseline>` and `git rev-parse <reviewed>` must succeed in **this** clone.
   - If either fails (typical cloud + unpushed Reviewed):
     - Do **not** substitute `HEAD` / another commit for the missing SHA.
     - Write the four artifacts under Output dir with Gate **`HOLD`**.
     - One High finding e.g. `QA-PROV-H01` (repair_surface: `plan`): specified SHA not present; independent review of requested tip impossible.
     - Task with `closes:` requiring push (cloud) or corrected invite.
     - Still attempt artifact git 帰着 (step 10) or return bodies for ingest.
     - Chat ≤5 bullets. Stop after 帰着 attempt.
5. Inspect only `git diff <baseline> <reviewed>` (blind: treat implementer narrative / prior flat QA PASS as **claim**, not proof). Use changed-path and stat summaries only to navigate; verify findings against the actual diff and source files.
6. Write `01_review.md` (Japanese body; code ids in English):
   - Header: repo, branch, baseline, reviewed, cycle, audience, remote visibility, focus, **Gate**
   - §結論: Blocking items only, one line each
   - §受入基準: every `AC-NNN` ID and exact criterion text from the invite, plus PASS/FAIL/UNVERIFIED and evidence
   - §参照Skill確認: each pinned file path, expected/observed SHA-256, read status
   - §Findings: mismatches only. ID `QA-<AREA>-<H|M|L|P><nn>`, Severity, Status, Evidence `path:line`, Expected, `repair_surface` (`docs`|`code`|`spec`|`plan`)
   - §Re-QA: next baseline default = this reviewed SHA
   - **Forbidden:** long Aligned formula catalogs; broken TeX; Owner ACCEPT/ARCHIVE
7. Write `02_tasks.md`:
   - Follow [`references/cloud_output_contract.md`](references/cloud_output_contract.md).
   - All actionable findings map to a task; High → task required; PASS notes → no task.
8. Write `03_machine.json` per [`references/machine_schema.md`](references/machine_schema.md) (include `audience`, `remote_visibility`, exact `acceptance_criteria`, and `reviewer_materials`).
9. Write `STATUS.md` with single token Gate: `PASS` | `HOLD` | `FAIL` | `INCONCLUSIVE`.
10. **Do not** edit product code or `00_invite.md`.
11. **Artifact git 帰着:**
    - Before any artifact commit or push: `branch=$(git branch --show-current)`. If `branch` is `main` or `master`: **fail-fast STOP** (same guard as `cloud`). Do not commit artifacts and do not push. Confirmation does **not** override.
    - **Audience=`cloud`:** Stage only `01_review.md`, `02_tasks.md`, `03_machine.json`, `STATUS.md` under Output dir (worktree otherwise clean aside from those). Commit `Yip: QA review <topic> c<N>` with trailer `Blind-QA-Review-Artifacts: <topic>`. Run topic-only `git push -u origin HEAD`. Report Artifacts commit SHA. On push failure: keep local commit if created; return four file bodies; tell requester to run `/blind-qa-cycle ingest`.
    - **Audience=`local`:** Writing into the shared clone is enough; do not push unless the user separately asks.
11. Chat final reply ≤5 bullets including Gate, Output dir, Blocking/Task counts, and Artifacts SHA **or** `ingest-needed`.

## Mode: ingest

Use when Cloud review returned four file bodies (or a patch) but could not push to origin.

1. Require Output dir path and the four file contents (or paths the user staged). Audience effectively `cloud` handoff cleanup.
2. `branch=$(git branch --show-current)`. If `branch` is `main` or `master`: **fail-fast STOP** (same guard as `cloud` / cloud `review`). Do not write-commit-push on main.
3. Write/overwrite only `01_review.md`, `02_tasks.md`, `03_machine.json`, `STATUS.md` under that Output dir. Never modify `00_invite.md` or product code.
4. Require worktree clean except those four paths. Commit `Yip: QA review <topic> c<N>` with `Blind-QA-Review-Artifacts: <topic>` if not already committed.
5. Topic-only `git push -u origin HEAD`. Never merge to main / force-push.
6. Confirm with Artifacts commit SHA and relative Output dir. Stop.

## Re-QA (`c{N+1}`)

Prefer `/blind-qa-cycle cloud re-qa`. Required inputs: new Reviewed SHA (or staged repair), previous cycle path, Finding IDs to close, Audience=`cloud` for cloud path. Baseline default = previous cycle's Reviewed. Create new folder; do not mutate frozen `cN`. Checkpoint is **not** required for Re-QA when Baseline is taken from the previous cycle Reviewed SHA.

## Mode: respond — Finding対応

このmodeは、`blind-qa-cycle`のReviewerが返したFinding/taskを実装担当が処理するための入口です。正式Quality Loop caseの`quality-response`とは別フローで、case正本や他cycleのQA成果物には触れません。

1. Require one frozen cycle path. Read its `00_invite.md`, `01_review.md`, `02_tasks.md`, `03_machine.json`, and `STATUS.md`. Cross-check topic/cycle, finding IDs, task-to-finding mapping, and Gate. If inputs disagree or a task ID is absent, stop and report the mismatch.
2. Ask which task IDs/Finding IDs the user authorizes this implementation round to address. Work only within those selected tasks and the existing project approval boundary. Do not alter the frozen invite, review, tasks, machine data, or STATUS.
3. Before implementation, show the selected Finding/task IDs, affected paths, and intended change boundary. If the repository requires a separate implementation plan/approval, follow it before editing. Do not treat `respond` as blanket approval for unlisted findings or unrelated cleanup.
4. Implement the authorized corrections. Before commit, require a non-`main`/`master` topic branch, a clean status except for the selected response paths, and a staged-only index containing exactly the response paths. Never stage, stash, restore, reset, or discard user changes. If the preconditions fail, stop and report the exact paths.
5. Create one Yip response commit from that existing index: subject `Yip: QA response <topic> c<N>`; trailers `Blind-QA-Response: <topic>` and `Blind-QA-Findings: <comma-separated Finding IDs>`. Report full commit SHA, paths, Finding IDs, and any task not addressed. The response commit does not close Findings.
6. Re-submit through `/blind-qa-cycle cloud re-qa` or a local invite with the previous cycle path and selected Finding IDs. The previous cycle's Reviewed SHA is Baseline; the new Reviewed SHA is the response commit (or a later explicitly selected repair commit). Create a new `c{N+1}` and keep the prior cycle immutable.

## Mode: note — Human Understanding Note

Use after the cycle's latest review result is available. This mode supports a human-authored reflection; it does not review code, change Findings, or determine acceptance.

1. Require the cycle directory (path or unique topic/cycle). Read `00_invite.md`, parse `03_machine.json`, and read `STATUS.md` as the reference source. Confirm topic/cycle and Baseline/Reviewed SHA match between invite and machine data; confirm machine `gate` matches the single Gate token in STATUS. Require Repository and Branch in the invite. If a required file/value is missing or inconsistent, do not create a Note; report the exact missing or conflicting fields.
2. Resolve the values from those files only. Do not infer from chat context, current HEAD, another cycle, or implementer explanation. Include the source path and reference SHA values in the Note header.
3. If `04_human_understanding.md` already exists, do not edit or replace it. Return its path and offer read-only viewing or a new QA cycle.
4. Ask whether the person wants to answer in chat or receive an empty template to edit. Show all six prompts and mention **目安: 約5分**.
5. When the person answers in chat, preserve their answer text verbatim under each matching question. Do not correct, summarize, infer, grade, or fill blanks. Keep empty responses blank or record the person's own `まだ理解していない` text.
6. Create only the new `04_human_understanding.md` under that cycle directory. Do not write to `00_invite.md`, the four Reviewer outputs, or any other path; do not commit or push in note mode.
7. The Note records human understanding only. Its presence/content does not change `STATUS.md`, JSON `gate`, Finding/task status, Owner adjudication, or merge/deployment state.

### `04_human_understanding.md` template

```markdown
# Human Understanding Note

- 記入者: 人（本人記入）
- 作成日時: <JST日時または本人記入>
- Cycle: <topic>/c<N>
- Repository: <00_invite.mdから取得>
- Branch: <00_invite.mdから取得>
- Baseline SHA: <00_invite.mdから取得>
- Reviewed SHA: <00_invite.mdから取得>
- 最終QA Gate: <STATUS.mdと03_machine.jsonから取得>
- 出典: <invite/review/machine/statusの相対パス>

目安: 約5分。自分の言葉で記入する。空欄や未理解を残してよい。

1. 今回変わったsystem boundary:
   <本人の回答>

2. 守るべきinvariant:
   <本人の回答>

3. 今回一番危険だったfailure mode:
   <本人の回答>

4. それを防ぐmechanism:
   <本人の回答>

5. AIなしで説明できる今回の設計:
   <本人の回答>

6. まだ理解していない点:
   <本人の回答、または空欄>
```

## 監査cycleの終結

Reviewerまたは実装担当は、終結前に最新cycleで次を対応づけて確認する。

- cycle ID、Repository/branch、Baseline/Reviewed SHAと最終Gate
- 各Findingの最新状態（再QA済み／未解決／未検証）と対応するtask
- 未解決Finding、必須check未実施、その他の残余リスク
- Human Understanding Noteの保存先（未作成の場合は未作成と明記）

上記を終結応答に記録し、QA監査cycleがtopic branch上で終了したことを示す。HOLD/FAILや残余リスクがある場合も状態を偽らず記録したうえでcycleを閉じられる。Noteの未作成・空欄はQA Gateを変更しない。終結はOwner受入、`main`/`master`へのmerge、外部Skill配置、配備を実行・承認するものではなく、必要ならOwner判断へ明示的に引き継ぐ。

## Out of scope

Implementation/repair of product code, merge to main, Owner sign-off, Artifacts flat-file migration, always-on `gh` posting, renaming `checkpoint` to `setup`, silent push outside explicit `cloud` / `cloud re-qa` / cloud `review` artifact push / `ingest`.
