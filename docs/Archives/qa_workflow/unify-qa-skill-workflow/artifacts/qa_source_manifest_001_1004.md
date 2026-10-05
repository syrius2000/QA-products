# QAループ実装の持込元マニフェスト

created: 2026-10-04 17:03 (JST)
update: 2026-10-04 17:03 (JST)
author: Codex (GPT-6)

## 元checkoutの開始状態

- branch: `master`
- HEAD: `ad6ca1ee196bd75bed026858c2de9586ca49c85c`
- `git status --short`件数: 167
- status SHA-256: `6a2e3f9909d14626bb7ff74eacd008a18f019d2aac53ea80d725db9c632fa5c7`
- 元checkoutの差分・削除・未追跡ファイルは編集せず、必要対象のみ隔離worktreeへコピーした。

## コピー対象の内容識別

| 相対パス | SHA-256 |
|---|---|
| `.agents/skills/blind-qa-cycle/SKILL.md` | `dfad89b76a8e773334ee92679793220a39f75b5b82d49da37cf3facf6cebe2d1` |
| `.agents/skills/blind-qa-cycle/references/audience_channels.md` | `3ec0ab9144a36f3278e370af59ae3700058bd1b2cfc379377175c21852b7ee43` |
| `.agents/skills/blind-qa-cycle/references/cloud_output_contract.md` | `b225a7aa3a8c5ff5bd704a43739f475ad24a00013ac37e471166263c69b5e30e` |
| `.agents/skills/blind-qa-cycle/references/focus_math_definitions.md` | `f99f8959434089a0c73002a4a354e2c18594fd9ab348b96bca6b7da475d0c905` |
| `.agents/skills/blind-qa-cycle/references/focus_openspec_coherence.md` | `df929ddb903b76d9410620302e9f5b2d8309cec9b63e89cb6ca2e1a9356fe0af` |
| `.agents/skills/blind-qa-cycle/references/focus_path_sanitization.md` | `ee95b7a09af3d8596aef16a51f763b2275dec08ff682e2c64307465a1c897304` |
| `.agents/skills/blind-qa-cycle/references/focus_provenance_plans.md` | `947d708eeb9e724bf17ad7f8b5dc594a50533b28cf688a4b83cca96f04f414ed` |
| `.agents/skills/blind-qa-cycle/references/git_wip_flow.md` | `bd8143358c3359468eacac2ab7f583b1cb0057fedac7d6644f218f1a0eb048f0` |
| `.agents/skills/blind-qa-cycle/references/machine_schema.md` | `033692c891d7476206e59ac77849678b3368da75d0b425cec87ac8cd6cb716ac` |
| `.agents/skills/quality-qa/CHANGELOG.md` | `8c8aa2f654acad188b26a1d2aa4e1227a78e3843da825c1e6d9ffbe5fcfaba6e` |
| `.agents/skills/quality-qa/SKILL.md` | `dc5d651e4d189dd02d321ab09abdf163c863aef018e67850687672110097cf8d` |
| `.agents/skills/quality-qa/VERSION` | `e9dd8507f4bf0c6f42458e41aea833ad0bd3f6127272335eee9bf4d58541ed67` |
| `.agents/skills/quality-qa/bin/quality-qa-cli` | `e19b778f66f944236cfcf6dfe4f191693582357dfeeb975fe7913cb7c6c7a5df` |
| `.agents/skills/quality-qa/evals/evals.json` | `9897b437e55cd7aca29fc4cdce487061a6b631dab406779903b4a670c50d6d44` |
| `.agents/skills/quality-qa/references/prepare.md` | `e357c84764b4cb1a045bc1a511eb55285e9743f445c8d7b66a5c57b0518ebd61` |
| `.agents/skills/quality-qa/references/publish.md` | `2d5bdb221a1fb33efebed198d274a58f5796c32c9be9deee70f44fa452fa9e77` |
| `.agents/skills/quality-qa/references/repair.md` | `4216159d99816242bc56590caa2d6bf27bf28cb8e90f740d381c52f803e5e2ba` |
| `.agents/skills/quality-qa/references/results.md` | `9affbc02839b741605392280357a0e546d7cb687caba0fe3556c4e923536eb8f` |
| `.agents/skills/quality-qa/runtime/qa_workflow/__init__.py` | `d34c722ded7fb33593e3c861d54ffe14ca4e3146fce414a65f68d0aaea436ca5` |
| `.agents/skills/quality-qa/runtime/qa_workflow/cli.py` | `7c62fff2c69ff7e1b72957d2e9a18d5cf42fde8114e06d863e46013f2510e5d2` |
| `.agents/skills/quality-qa/runtime/qa_workflow/github.py` | `6acff302c31a33900b452b647c96886fa7045b8770e251cdf35b068ad0902c89` |
| `.agents/skills/quality-qa/runtime/qa_workflow/gitops.py` | `54409fb45046a4a2e947c641757287891eb989c01fc3ebc72bb8c7caf7c6d68b` |
| `.agents/skills/quality-qa/runtime/qa_workflow/legacy.py` | `7d75ddb5528aafaa139a29841a3b6067df33dfafe2f2684849a446570ebb6f04` |
| `.agents/skills/quality-qa/runtime/qa_workflow/review.py` | `20147efd78f216fd5a9eab61ace3fd55a25ec63830854c9f1c445d70ba653c68` |
| `.agents/skills/quality-qa/runtime/qa_workflow/store.py` | `8fc2f51f5b4afbea17a9187e8dc1778f25c2786e758792714f916baf644f0746` |
| `.agents/skills/quality-qa/runtime/qa_workflow/workflow.py` | `9b3104511a876ff8b11e656377cb07912c0382c14b6f4f498e96afa96e352527` |
| `.agents/skills/quality-qa/templates/qa_review.md` | `86d4301d374d2814f6d537af65da838f5f1358440d2cc0691e1038de5ece434e` |
| `AGENTS.md` | `674c5a1eaa3b0786e5edffb50f776b1a368066a8013cb7167b036c037dc79f84` |
| `docs/Artifacts/implementation_plan_029_1004.md` | `fd5fe8e693d141c9d42df06691a136e5eedb4dff650792ad50e088a3ba71c5b7` |
| `docs/Artifacts/implementation_plan_030_1004.md` | `86e658b2d06c15abc690ada38d9bd57c91fb7a0c788b6078014faec111a3c472` |
| `docs/Artifacts/implementation_plan_031_1004.md` | `b9f64e710b960bd487ec161cf19ae4ae75554bc46f66920c84877f4913c2995c` |
| `openspec/changes/unify-qa-skill-workflow/.openspec.yaml` | `ad734da2ba5f4c5a6979a8bbb6bad4db20fb21ec275ceca5f24842fbdfaf5bef` |
| `openspec/changes/unify-qa-skill-workflow/design.md` | `1ce7a7fe07cb6c34f885a049f4dde4395cbc220a1255272f5e71591b0fc524d5` |
| `openspec/changes/unify-qa-skill-workflow/proposal.md` | `e4769a85009e0019734aebbad384862737a82ed997f850e58db5acbf8c527798` |
| `openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md` | `70da9ed822eb774a3b3613f7f60bd36d8cf8512374a146577cf226afd1f312a9` |
| `openspec/changes/unify-qa-skill-workflow/tasks.md` | `dcffab510f54b9ae7ed9ea8dd40a02722bd4cf6b24f5453a4d2d685f66f18910` |
