# 独立QAレビュー依頼：QA-003 Cycle 3 F01/F02再確認

- **Repository:** `syrius2000/qa-products`
- **Branch:** `codex/unify-qa-skill-workflow`
- **Baseline commit:** `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb`
- **Reviewed commit:** `47b6a58f3323d4fcd455d768314f2e4c97b88dfd`
- **Baseline subject:** `docs: add cross-device development handoff memo`
- **Reviewed subject:** `Yip: fix QA-003 Cycle 2 findings`
- **Diff:** `git diff 17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb 47b6a58f3323d4fcd455d768314f2e4c97b88dfd`
- **Focus pack:** `path-sanitization`, `openspec-coherence`
- **Output dir:** `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/`
- **Cycle:** `3`
- **Audience:** `local`
- **Remote visibility:** `local-only`
- **Changed paths:**
  - `A docs/Artifacts/implementation_plan_036_1005.md`
  - `M openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md`
  - `M quality-loop/qa_workflow/workflow.py`
  - `M quality-loop/skills/quality-qa/references/publish.md`
  - `M quality-loop/skills/quality-qa/references/reviewer_contract.md`
  - `M quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py`
  - `M quality-loop/tests/test_qa_workflow_contract.py`
- **Diff summary:** 7 files changed, 267 insertions(+), 19 deletions(-)
- **Requester notes:** QA-003 Cycle 2のHOLDおよびQA-F01/F02が未解決。前回レビュー本文は `docs/Artifacts/qa_review_003_cycle2_local_1005.md`。Cycle 2記録は変更せず、この依頼では修正後の固定SHAを独立評価してください。Cycle 2で問題となったReviewer契約hashは、前回依頼記載値ではなく、ここに記したReviewed SHA内のraw bytes hashと照合してください。

## 対象SHA上のReviewer資材とprovenance

指定commitから取得した各ファイルのraw bytes SHA-256:

- `quality-loop/skills/quality-qa/SKILL.md` — `57bb58973476cb503c35ea2981c55908c245d8c6e34972385e4c987740bdc261`
- `quality-loop/skills/quality-qa/references/reviewer_contract.md` — `0a0cf6793197fedd16bd365b8d1b8280a790d77c83c8f3b7d1eda0338c6dec42`

Baseline上のReviewer契約hashは `84f11def7f338acbf91362bbd8ad62834cd195383830a8684ec7ec7f4d3bf8cc` です。BaselineとReviewedの契約が異なるため、レビュー契約としてReviewed SHA上のファイルを用い、依頼中のhashとraw bytesを独立に照合してください。hash不一致、対象SHA取得不能、必要資材不在の場合はHOLDです。

## 目的

QA-003 Cycle 2でOPENだったQA-F01（公開走査が最終依頼本文に結び付かない）およびQA-F02（再QA時に承認文だけで必須check契約を弱められる）への修正が、対象SHA上で受入可能かを独立確認する。修正担当者の説明や本依頼の主張を根拠とせず、Baseline..Reviewedの実差分、関連runtime・spec・testを確認してください。

## 受入基準

- **AC-001 / QA-F01:** 対象SHA確定後に生成された最終依頼本文と製品対象が走査され、最終依頼SHAが公開状態へ記録される。走査後の変更は招待commit前に拒否され、commit内blob hashと走査hashの一致をpush前に検証する。正常系・改変拒否・機密/個人パス拒否で、拒否時にremoteへ公開されないこと。
- **AC-002 / QA-F02:** 既存必須checkの削除、ID変更、`required=false`、argv/cwd/env/timeout/期待終了コード等の変更を承認文があっても拒否する。許される契約変更では旧新hashを明示承認へ結び付け、記録に旧新契約hashと構造化差分を保存する。
- **AC-003 / 同期・仕様:** 正本runtimeと配布runtime、OpenSpec要件、公開手順、Reviewer契約が実装挙動と一致し、対象SHA上のReviewer資材hashが依頼記載値と一致する。
- **AC-004 / 回帰:** 対象SHAでF01/F02の正常系・拒否系を含む `quality-loop` の必須suiteが実行可能である。実行できない項目は結果と理由を残し、PASSにしない。

## 重点監査観点

### path-sanitization

- 対象tree内に実在する個人の絶対パス、個人情報、`file:///`リンクが追加されていないこと。
- 禁止パターンを検出するためのliteralやテストfixtureは、実在情報と区別する。
- Windows drive path、UNC pathが差分にあれば同様に確認する。

### openspec-coherence

- OpenSpec requirement/scenario、基盤runtime、配布runtime、公開手順、Reviewer契約、回帰testの間に契約矛盾がないこと。
- 計画で宣言した変更と実差分・検証範囲が対応していること。実行していない検証を成功扱いしない。

### QA-F01：最終依頼と公開走査の結合

- `publish`で対象SHA確定に伴い依頼文が再生成される順序を追い、実際に公開する最終バイト列を走査しているか確認する。
- 保存されたscan Evidenceが製品snapshot、依頼hash、check contract hashと整合するか確認する。
- commit直前に依頼が変わるfixtureが、invite commitおよびremote push前に停止するか確認する。拒否時に既存ユーザーindexを破壊しないかも確認する。
- invite commit内blob hashがscan hashと一致し、成功状態に同じcommit識別が保存されるか確認する。
- 走査がcommit後またはpush後になっていないか、再試行時に別本文のhashを使い回さないか確認する。

### QA-F02：必須check契約の不変性と変更承認

- 必須checkの削除、ID置換、任意化、argv/cwd/env/timeout/expected exit/Python minimumの変更を、承認文あり・なし双方で確認する。
- 旧新hashを含まない承認、誤った新hash、他契約のhashによる承認が拒否されるか確認する。
- 許容される変更では、実際のcheck契約と記録hash、構造化added/removed/changed差分が一致するか確認する。
- 入力checkの構造不正や重複IDにより辞書化・比較が例外または契約迂回にならないか確認する。

## 必須check

依頼側の実装者検証記録では以下と報告されているが、ReviewerはReviewed SHAで独立に確認し、報告を根拠の代用にしないでください。

- `python3 --version`
- `pytest tests -q`、cwd `quality-loop/`、env `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=.`
- runtime同期検査
- `openspec validate unify-qa-skill-workflow --strict --json`

利用可能な環境とリポジトリ規則の範囲で実行してください。無許可の依存導入、ネットワーク、認証情報の利用は禁止です。checkごとにargv、cwd、env、timeout、Python/pytest版、exit code、duration、stdout/stderr SHA-256を記録してください。必須検証のERROR/NOT_RUNはPASS不可です。

## Gate判定

- Provenance（SHA、依頼、参照資材hash）が不一致または確認不能なら **HOLD**。
- Provenanceが有効で、受入基準または必須checkのFAILがあれば **FAIL**。
- 既知FAILがなく必須checkがERROR/NOT_RUNなら **INCONCLUSIVE**。
- 全受入基準と必須checkがPASSし、重大なOPEN Findingがない場合のみ **PASS**。

## Reviewer contract

- 実装担当とは別のReviewerとして、Baseline `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb` とReviewed `47b6a58f3323d4fcd455d768314f2e4c97b88dfd` の全差分を確認する。両SHAがこのcloneに存在することを確認し、別SHAへ置き換えない。
- レビュー成果物は以下4ファイルだけをOutput dirに作成する。製品コード、OpenSpec、依頼本文、既存QA状態は変更しない。
  - `01_review.md` — 日本語結論、AC照合、根拠付きFinding、必須check evidence、前回QA-F01/F02再確認、残余事項。
  - `02_tasks.md` — 修復が必要なFindingごとの具体的タスク。PASS所見だけなら「タスクなし」。
  - `03_machine.json` — `blind-qa-cycle-v1`。必須key: `schema`, `topic`, `cycle`, `baseline`, `reviewed`, `audience`, `remote_visibility`, `gate`, `focus_packs`, `findings`, `tasks`。Gateは`PASS|HOLD|FAIL|INCONCLUSIVE`、severityは`High|Medium|Low|PASS`、statusは`OPEN|CLOSED`、repair_surfaceは`docs|code|spec|plan`。
  - `STATUS.md` — Gate語1語のみ。JSONのgateと一致させる。
- Findingは差分または一次情報で確認した不一致だけとし、各Findingに一意ID、severity、status、`path:line`、期待動作、`repair_surface`を記す。対応Findingにはtaskの`closes`を結ぶ。実装修正やOwnerのACCEPT/ARCHIVE判断は行わない。
- 再QAではQA-F01とQA-F02を各々 `解消` / `未解消` / `未検証` / `撤回提案` のいずれかで明示し、Reviewed SHA上の根拠を示す。
- Output dir以外へ書き込まない。Audience=`local`のためpushしない。依頼本文をGitHub Cloudへ貼り付けない。

## Reviewerの最終返信

5項目以内でGate、Output dir、Blocking件数、Task件数、次の行動を報告してください。PASS以外をPASS相当と表現しないでください。
