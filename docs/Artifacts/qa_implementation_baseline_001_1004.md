# QAループ実装開始ベースライン

created: 2026-10-04 18:06 (JST)
update: 2026-10-04 18:06 (JST)
author: Codex (GPT-6)

## 開始時点

- 作業場所: 専用の隔離worktree
- HEAD: `ad6ca1ee196bd75bed026858c2de9586ca49c85c`
- branch: `detached HEAD`
- status entry: 47件（`git status --porcelain=v1 --untracked-files=all`）
- staged diff SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- tracked worktree diff SHA-256: `8f0c4dad2aacb0d9cb7fce7b81e299eeec65dec0097d46fe458c7b124227eb82`
- 本作業開始前から存在する変更・未追跡ファイルを保持し、reset、clean、stash、restore、commit、pushを行わない。
- QA-F02既存回帰のbaseline: `quality-loop/tests` 126件中125成功・1失敗。失敗はテストfixtureが提出契約の`product_paths`を欠いているため。

## 開始時点のパスと識別値

| 状態 | 相対パス | SHA-256／存在状態 |
|---|---|---|
| ` M` | `AGENTS.md` | `4cc8a965c04cc3a5564de1d7de33377164c320451e1a4b91ccfde52aa61ac61a` |
| `??` | `docs/Artifacts/implementation_plan_029_1004.md` | `fd5fe8e693d141c9d42df06691a136e5eedb4dff650792ad50e088a3ba71c5b7` |
| `??` | `docs/Artifacts/implementation_plan_030_1004.md` | `86e658b2d06c15abc690ada38d9bd57c91fb7a0c788b6078014faec111a3c472` |
| `??` | `docs/Artifacts/implementation_plan_031_1004.md` | `ab44327627ab626446948ae36159114669750dbe13f46571dda0bb0a615034b8` |
| `??` | `docs/Artifacts/implementation_plan_032_1004.md` | `0f8a20b6f66eaf162181554b7d2cc093b30c3ff3b59f6198db79aac02548eff1` |
| `??` | `docs/Artifacts/qa_source_manifest_001_1004.md` | `d7eee6cfc7591c57912f7d3bb75935c13ccad3e07639dce8be3e934af0facd50` |
| `??` | `openspec/changes/unify-qa-skill-workflow/.openspec.yaml` | `ad734da2ba5f4c5a6979a8bbb6bad4db20fb21ec275ceca5f24842fbdfaf5bef` |
| `??` | `openspec/changes/unify-qa-skill-workflow/design.md` | `76bd51c13671a323b40c97dc2076626f58866399de410ece1fa9c2cc15fd6572` |
| `??` | `openspec/changes/unify-qa-skill-workflow/proposal.md` | `6562014df9e1427f13121c074e8bed19d35e87421be676d2cf8af256092a3078` |
| `??` | `openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md` | `70da9ed822eb774a3b3613f7f60bd36d8cf8512374a146577cf226afd1f312a9` |
| `??` | `openspec/changes/unify-qa-skill-workflow/tasks.md` | `1163b383a3c05b0e31fdf4c2b82f67bcb27a6d746503ee71343f80e18fb4e4d7` |
| `??` | `quality-loop/qa_workflow/__init__.py` | `d34c722ded7fb33593e3c861d54ffe14ca4e3146fce414a65f68d0aaea436ca5` |
| `??` | `quality-loop/qa_workflow/cli.py` | `7c62fff2c69ff7e1b72957d2e9a18d5cf42fde8114e06d863e46013f2510e5d2` |
| `??` | `quality-loop/qa_workflow/github.py` | `6acff302c31a33900b452b647c96886fa7045b8770e251cdf35b068ad0902c89` |
| `??` | `quality-loop/qa_workflow/gitops.py` | `54409fb45046a4a2e947c641757287891eb989c01fc3ebc72bb8c7caf7c6d68b` |
| `??` | `quality-loop/qa_workflow/legacy.py` | `7d75ddb5528aafaa139a29841a3b6067df33dfafe2f2684849a446570ebb6f04` |
| `??` | `quality-loop/qa_workflow/review.py` | `fc227bea059aa7371e9a0d3d402c25ad6765409013454ddfab02b5b57e6d5166` |
| `??` | `quality-loop/qa_workflow/store.py` | `8fc2f51f5b4afbea17a9187e8dc1778f25c2786e758792714f916baf644f0746` |
| `??` | `quality-loop/qa_workflow/workflow.py` | `9767d246d87944e31916469c00c6f7ab24fb2eaf03d59fd3e5e12721c2b17b79` |
| `??` | `quality-loop/skills/blind-qa-cycle/SKILL.md` | `47514c6794c2f1cf8d85f72bac01ea870874035fd453a86b0050a512d0ab7724` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/audience_channels.md` | `3ec0ab9144a36f3278e370af59ae3700058bd1b2cfc379377175c21852b7ee43` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md` | `735d29ac787ee7b32461d65c121ce2d3718def94ef3f2a6888086e4021b8e5ec` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/focus_math_definitions.md` | `f99f8959434089a0c73002a4a354e2c18594fd9ab348b96bca6b7da475d0c905` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/focus_openspec_coherence.md` | `df929ddb903b76d9410620302e9f5b2d8309cec9b63e89cb6ca2e1a9356fe0af` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/focus_path_sanitization.md` | `ee95b7a09af3d8596aef16a51f763b2275dec08ff682e2c64307465a1c897304` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/focus_provenance_plans.md` | `947d708eeb9e724bf17ad7f8b5dc594a50533b28cf688a4b83cca96f04f414ed` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/git_wip_flow.md` | `bd8143358c3359468eacac2ab7f583b1cb0057fedac7d6644f218f1a0eb048f0` |
| `??` | `quality-loop/skills/blind-qa-cycle/references/machine_schema.md` | `664684e8f991380a5273d6b4f99990e6e38f8a625f8952eb367865ad94b484f2` |
| `??` | `quality-loop/skills/quality-qa/CHANGELOG.md` | `8c8aa2f654acad188b26a1d2aa4e1227a78e3843da825c1e6d9ffbe5fcfaba6e` |
| `??` | `quality-loop/skills/quality-qa/SKILL.md` | `648ad2268e2b7cc19ff68e20aa90c389c314080a3dd1bbd4b14209483bcc3873` |
| `??` | `quality-loop/skills/quality-qa/VERSION` | `e9dd8507f4bf0c6f42458e41aea833ad0bd3f6127272335eee9bf4d58541ed67` |
| `??` | `quality-loop/skills/quality-qa/bin/quality-qa-cli` | `e19b778f66f944236cfcf6dfe4f191693582357dfeeb975fe7913cb7c6c7a5df` |
| `??` | `quality-loop/skills/quality-qa/evals/evals.json` | `9897b437e55cd7aca29fc4cdce487061a6b631dab406779903b4a670c50d6d44` |
| `??` | `quality-loop/skills/quality-qa/references/prepare.md` | `e357c84764b4cb1a045bc1a511eb55285e9743f445c8d7b66a5c57b0518ebd61` |
| `??` | `quality-loop/skills/quality-qa/references/publish.md` | `2d5bdb221a1fb33efebed198d274a58f5796c32c9be9deee70f44fa452fa9e77` |
| `??` | `quality-loop/skills/quality-qa/references/repair.md` | `4216159d99816242bc56590caa2d6bf27bf28cb8e90f740d381c52f803e5e2ba` |
| `??` | `quality-loop/skills/quality-qa/references/results.md` | `9affbc02839b741605392280357a0e546d7cb687caba0fe3556c4e923536eb8f` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/__init__.py` | `d34c722ded7fb33593e3c861d54ffe14ca4e3146fce414a65f68d0aaea436ca5` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/cli.py` | `7c62fff2c69ff7e1b72957d2e9a18d5cf42fde8114e06d863e46013f2510e5d2` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/github.py` | `6acff302c31a33900b452b647c96886fa7045b8770e251cdf35b068ad0902c89` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/gitops.py` | `54409fb45046a4a2e947c641757287891eb989c01fc3ebc72bb8c7caf7c6d68b` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/legacy.py` | `7d75ddb5528aafaa139a29841a3b6067df33dfafe2f2684849a446570ebb6f04` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/review.py` | `20147efd78f216fd5a9eab61ace3fd55a25ec63830854c9f1c445d70ba653c68` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/store.py` | `8fc2f51f5b4afbea17a9187e8dc1778f25c2786e758792714f916baf644f0746` |
| `??` | `quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py` | `9b3104511a876ff8b11e656377cb07912c0382c14b6f4f498e96afa96e352527` |
| `??` | `quality-loop/skills/quality-qa/templates/qa_review.md` | `cec07269e23cf407999a6bdfb238426d451084c349590f77b18a5c2908f954f8` |
| `??` | `quality-loop/tests/test_qa_workflow_contract.py` | `c284dc6e2c7df6f91e84484991394324c146c23f65bb2a421f229d2dc214ae56` |
