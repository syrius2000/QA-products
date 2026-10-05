# 独立QAレビュー依頼：QA-003 Cycle 4 QA-C3-F01修正確認

created: 2026-10-05 18:07 (JST)
update: 2026-10-05 18:07 (JST)
author: Codex (GPT-6)

- **Repository:** `syrius2000/qa-products`
- **Branch:** `codex/unify-qa-skill-workflow`
- **Baseline commit:** `c9817075bb314644e7defe9ff0e989dc53dfbd26`
- **Reviewed commit:** `154e2ae875d7485fa9fafab60769f79bbfb45ec1`
- **Baseline subject:** `Yip: record QA-003 Cycle 3 handoff`
- **Reviewed subject:** `Yip: fix QA-C3-F01 final scan state persistence`
- **Diff:** `git diff c9817075bb314644e7defe9ff0e989dc53dfbd26 154e2ae875d7485fa9fafab60769f79bbfb45ec1`
- **Focus packs:** `path-sanitization`, `openspec-coherence`
- **Output dir:** `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/`
- **Cycle:** `4`
- **Audience:** `local`
- **Remote visibility:** `local-only`
- **Changed paths:**
  - `M openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md`
  - `M openspec/changes/unify-qa-skill-workflow/tasks.md`
  - `M quality-loop/qa_workflow/workflow.py`
  - `M quality-loop/skills/quality-qa/references/publish.md`
  - `M quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py`
  - `M quality-loop/tests/test_qa_workflow_contract.py`
- **Diff summary:** 6 files changed, 215 insertions(+), 30 deletions(-)
- **Requester notes:** Cycle 3はGate FAIL。QA-F01/F02はCycle 3で解消確認済み。新規Finding QA-C3-F01（Medium / OPEN）は、最終依頼走査拒否後に対象commitだけが作成済みなのにReviewed SHAと依頼hashがstateへ保存されず、再試行が不整合になる点。Cycle 3の原レビューとそれ以前の記録は変更しない。実装担当の説明、本依頼の受入主張、既存テストの期待値を正しさの根拠にせず、Baseline..Reviewedの実差分から独立に判定する。

## 対象SHA上のReviewer資材

Reviewed SHAから取得したraw bytes SHA-256:

- `quality-loop/skills/quality-qa/SKILL.md`: `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261`
- `quality-loop/skills/quality-qa/references/reviewer_contract.md`: `0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42`

Baselineでも同じhashである。SHAと上記資材hashを独立に確認する。不一致またはcommitがローカルに存在しない場合はHOLDとする。

## 目的

固定されたReviewed SHAにおいて、最終公開走査の拒否がcase state、Reviewed SHA、最終依頼hash、対象commit、ユーザーindex、招待commit、remoteの境界を一貫して保つか確認する。Cycle 3でOPENとなったQA-C3-F01の解消可否を独立判定する。

## 受入基準

- **AC-001 / 拒否後provenance:** 対象SHAを持つ製品限定commit後、最終走査より前にReviewed SHA、製品snapshot hash、最終依頼hash、Reviewer資材hash、check契約hashがstateへ保存される。secret様代入・個人絶対パス・走査snapshot不一致で拒否された後、state内hashと実ファイルおよび対象commitが一致し、拒否stage・分類・時刻・回復案内が残る。
- **AC-002 / 停止境界:** 最終走査拒否で作られ得るのは製品snapshotのみのローカル対象commit。招待commitとremote更新は発生せず、元indexは保持される。拒否文面や値そのものをstate・error・status応答に漏らさず検出分類だけを記録する。
- **AC-003 / 再試行と置換依頼:** 同じ拒否済みstateのpublish再実行は保存済み理由と次操作を返し、汎用hash不一致へ変化しない。原因を除いた新しいQA依頼/stateが記録済み`--reviewed <SHA>`を再利用でき、前caseのstate・invite・拒否履歴を変更しない。
- **AC-004 / 成功・既存経路:** 最終走査成功時は既存のF01 hash binding、招待commit内blob照合、remote到達可能性の順序を壊さない。通常再試行および対象commit直後の回復経路にも回帰がない。
- **AC-005 / 契約同期:** 正本runtimeと配布runtime、OpenSpec requirement、公開手順、回帰testsが同じ停止境界を表す。OpenSpec strict validationがvalid。
- **AC-006 / 検証:** Reviewed SHA上で `quality-loop` 全suiteを独立実行し、実際のPython/pytest版、argv、cwd、env、timeout、exit、duration、stdout/stderr SHA-256を記録する。実行不可・ERROR/NOT_RUNはPASSにしない。

## 重点監査観点

### path-sanitization

- Reviewed treeに実在する個人名、OS絶対パス、`file:///`リンク、Windows drive path、UNC pathを確認する。
- 検査規則を示すliteralおよび合成fixtureの値は実在情報と区別し、それ自体をFindingにしない。
- レビュー対象コードのエラー/state/status出力が検出したsecret本文を再掲しないか確認する。

### openspec-coherence

- OpenSpec scenario、正本runtime、配布runtime、公開手順、testsの順序・拒否状態・回復契約が一致するか確認する。
- Plan 037の範囲と固定差分、テスト結果の対応を確認する。実行していない検証を成功扱いしない。

### QA-C3-F01再確認

- 最終依頼が対象SHAを含む形にfinalizeされ、実際に走査するbyte hashがstateへ先行保存される境界を追う。
- secret、個人パス、snapshot不一致の拒否処理で、対象SHA、依頼hash、材料hash、検出分類、stage、時刻、次操作が永続化されるか確認する。
- 拒否時に招待commit/pushがなく、対象commitが存在する場合のtree scope、remote tip、ユーザーindexの不変性を確認する。
- 同じ依頼の再試行を試し、拒否履歴が曖昧なhashエラーにならず、既存caseを変えないか確認する。新しいcaseが同じReviewed SHAを明示して再利用できるか確認する。
- 成功系、対象commit後の中断回復、F01/F02の従来契約への回帰を確認する。

## 必須check

Reviewed SHAのcheckoutで、許可済み環境のみを使って次を実行する。無許可の依存導入、ネットワーク、認証情報アクセスは行わない。

- `python3 --version`
- `pytest --version`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q`、cwd `quality-loop/`、timeout `300s`
- 正本runtimeと`quality-loop/skills/quality-qa/runtime/`の該当workflowが一致するかをraw bytesで照合
- `openspec validate unify-qa-skill-workflow --strict --json`

各checkのargv、cwd、env、timeout、version、exit code、duration、stdout/stderr SHA-256を記録する。

## Gate判定

- SHAsまたはReviewer資材hashが確認不能・不一致なら **HOLD**。
- provenance有効で受入基準または必須checkが失敗すれば **FAIL**。
- 既知FAILがなく必須checkがERROR/NOT_RUNなら **INCONCLUSIVE**。
- 全受入基準・必須checkがPASSし、重大なOPEN Findingがない場合のみ **PASS**。

## Reviewer contract

- `git rev-parse`でBaselineとReviewedの両方を確認する。レビューは指定2 SHA間の実差分に対して行い、別SHAへ置換しない。実装者とは別担当として判定し、同じチャットの実装説明・本依頼の主張・前回テストを根拠の代用にしない。
- Reviewer資材のraw bytes hashを指定値と照合してから契約を読む。必要なcommit、hash、出力契約が取得できなければHOLD。
- Cycle 3のQA-C3-F01、QA-F01、QA-F02をそれぞれ `解消` / `未解消` / `未検証` / `撤回提案` のいずれかで明示し、Reviewed SHA上の具体的根拠を記す。
- レビュー成果物はOutput dir内の次の4ファイルだけとする。00_invite.md、既存c1〜c3記録、製品コード、仕様、stateを変更しない。
  - `01_review.md`: 日本語の結論、AC照合、根拠付きFindings、検証Evidence、前回Finding再確認、次のbaseline。
  - `02_tasks.md`: 修復が必要な各Findingに具体的taskを対応。PASS所見だけならtaskなし。
  - `03_machine.json`: `blind-qa-cycle-v1`。必須keyは`schema`, `topic`, `cycle`, `baseline`, `reviewed`, `audience`, `remote_visibility`, `gate`, `focus_packs`, `findings`, `tasks`。Gateは`PASS|HOLD|FAIL|INCONCLUSIVE`、severityは`High|Medium|Low|PASS`、statusは`OPEN|CLOSED`、repair_surfaceは`docs|code|spec|plan`。
  - `STATUS.md`: Gate語1語のみ。JSONのgateと一致させる。
- Findingは差分または一次情報で確認した不一致に限る。各Findingに一意ID、severity、status、`path:line`、期待動作、`repair_surface`を記し、対応taskは`closes`で結ぶ。OwnerのACCEPT/ARCHIVE判断をしない。
- Audience=`local`、Remote visibility=`local-only`。出力はこのclone内へ保存し、pushしない。QA artifact以外へ書き込まない。

## 出力形式

`01_review.md`にはRepository、Branch、Baseline、Reviewed、Cycle、Audience、Remote visibility、Focus packs、Gateを記載し、「結論」「受入基準照合」「必須check evidence」「前回Finding再確認」「Findings」「Re-QA」節を含める。Findingがない場合は根拠と検査範囲を記し、架空Findingを作らない。

`02_tasks.md`は次の形式とする。

```markdown
# 修復タスク

- [ ] T-01 (closes: QA-AREA-M01) severity=Medium; path=`path/to/file`; action=<具体的な修正内容>; done_when=<観察可能な完了条件>; verify=<確認手順と期待結果>
```

PASS所見だけなら「タスクなし」と記載する。`03_machine.json`と`STATUS.md`は上記Reviewer contractのschemaとenumを守る。

## Reviewer最終返信

5項目以内でGate、Output dir、Blocking件数、Task件数、次の行動を報告する。PASS以外をPASS相当と表現しない。
