# QAループ統合Artifactsのアーカイブ記録

created: 2026-10-05 22:30 (JST)
update: 2026-10-05 23:37 (JST)
author: Codex (GPT-6)

## 対象期間と結論

対象期間: 2026-10-04 〜 2026-10-05

`docs/Artifacts`にあったPlan 040以外の37ファイルと、先行して移動済みのPlan 034・037をArchiveへ集約した。合計39件を`docs/Archives/qa_workflow/unify-qa-skill-workflow/`以下へ保存し、`docs/Artifacts/`には現行の整理計画[Plan 040](../Artifacts/implementation_plan_040_1005.md)のみを残した。

移動は削除を伴わない。元の相対階層とファイル名を維持し、QA証跡、未承認計画、draft/prepared/invalid状態、FAIL/HOLD結果もそのまま履歴保存した。QA状態JSON内に書かれた当時の`docs/Artifacts/...`パスはprovenanceとして保持しており、現在の保存場所は本書の対応表で追跡できる。

## 確定した判断と理由

- Quality Loop v1.4.0 Coreは2026-10-05にOwnerが正式受入済み。根拠と範囲は[Owner裁定記録](qa_workflow/unify-qa-skill-workflow/artifacts/owner_adjudication_001_1005.md)に保持した。
- QA-001のReviewed SHA `7d8880b2558cfabcc517b95b10b87b5ccebae03a`に対するFAIL、QA-F01/F02、必須pytest未実施の記録は当時の結果として保持した。後続実装で旧対象は廃止され、Ownerは旧対象の追加修正を不要と判断した。
- QA-003 Cycle 1はFAIL、Cycle 2はHOLD、Cycle 3はFAIL（QA-C3-F01 OPEN）、Cycle 4はPASS。後続結果で前サイクルの履歴を書き換えていない。
- Plan 029〜032等の改訂・未承認計画は履歴として保存した。Archiveへの移動は承認や実装を意味しない。
- Cycle 3のFAILとCycle 4のPASS、各QA JSONの状態、レビュー本文、招待本文は内容選別・判定変更なしで保存した。

## 主要成果と検証の限界

実装報告とOpenSpec記録には、QA-F01/F02対応、Plan 036後の174 tests passed、Cycle 3後のQA-C3-F01修正、Cycle 4のPASS等が記載されている。これらは当時の実装者検証または独立QAの証拠であり、本アーカイブ作業で再実行した結果ではない。

- 移動ファイル: 37件。加えて、前段で移動済みのPlan 034・037を含めたArchive対応表は39件。
- 移動直後に各ファイルのSHA-256を照合した。QA JSONと固定QA原文のhashは移動直後に一致した。
- リンク修復のため、移動後に相対リンクを更新した文書はPlan 037、Plan 039、実装報告001/002、Owner記録、runtime inventoryである。外部Markdown参照もArchive後のパスに合わせた。管理下原本はGit履歴から復元可能で、未追跡だったPlan 039とOwner記録はArchiveに保持した。
- QA invite、独立review本文、Cycle 3/4 machine JSON、QA state JSONは内容とSHA-256が不変。
- 移動先Markdownのリンク検査は成功した。`git diff --check`も成功。製品テストは行っていない。
- リポジトリ全体のMarkdown検査では、今回の移動と無関係な既存リンク切れ17件がリポジトリ全体に残る。今回追加・更新したリンクは解決する。

## 未解決事項と引継ぎ

- v1.4.0 Coreの外部Skill配置・production deploymentは未実施。専用計画、backup、dry-run、rollback確認と別途明示承認が必要。
- commit・pushは本整理では行っていない。
- 今後のArtifactsには、現行・承認待ちの計画や次に必要な文書だけを置く。完了後は本書と同じ方法でArchiveへ整理する。
- 整理計画と実施記録は[Plan 040](../Artifacts/implementation_plan_040_1005.md)を参照する。

## 元文書と復元情報

全39件の元パス、Archive先、Archive側SHA-256を記録する。`docs/Artifacts/`以下の階層はArchive内の`artifacts/`以下に維持した。Plan 034・037は既存の`plans/`にある。QA state JSONに記録された旧パスは、当時の記録値としてそのままにしてある。

| 元文書 | Archive先 | Archive側SHA-256 | 復元情報 |
|---|---|---|---|
| `docs/Artifacts/implementation_plan_023_0906.md` | [implementation_plan_023_0906.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_023_0906.md) | `0e648f0744e319d97a353fa32a2e42d2040234d41c8b080c3293e12166a5ff37` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_029_1004.md` | [implementation_plan_029_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_029_1004.md) | `fd5fe8e693d141c9d42df06691a136e5eedb4dff650792ad50e088a3ba71c5b7` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_030_1004.md` | [implementation_plan_030_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_030_1004.md) | `86e658b2d06c15abc690ada38d9bd57c91fb7a0c788b6078014faec111a3c472` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_031_1004.md` | [implementation_plan_031_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_031_1004.md) | `ab44327627ab626446948ae36159114669750dbe13f46571dda0bb0a615034b8` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_032_1004.md` | [implementation_plan_032_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_032_1004.md) | `0f8a20b6f66eaf162181554b7d2cc093b30c3ff3b59f6198db79aac02548eff1` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_033_1004.md` | [implementation_plan_033_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_033_1004.md) | `395411ea42f29e8295d1c1739a6e8481d659df7b1cdd0320f18aa5add8c6a0b9` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_034_1005.md` | [implementation_plan_034_1005.md](qa_workflow/unify-qa-skill-workflow/plans/implementation_plan_034_1005.md) | `8e2c0f750ed80c02a234e11f57e38c79611cb96edcf86362caf927ef13c2f1c9` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_035_1005.md` | [implementation_plan_035_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_035_1005.md) | `614e2e5f79365dde8c120a15b218fb3b3918da50ffc4725ffe768ec3f3bc267a` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_036_1005.md` | [implementation_plan_036_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_036_1005.md) | `1d69b9dd87aecb90235f894f3bd2a7fdd4104640f29d918c49a340d0f988f9c0` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_037_1005.md` | [implementation_plan_037_1005.md](qa_workflow/unify-qa-skill-workflow/plans/implementation_plan_037_1005.md) | `27365da8f84910cfa8d30146eafede0fb5b63ba73ab26ad7d320edcf516fe7cf` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_038_1005.md` | [implementation_plan_038_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_038_1005.md) | `6b31f4de6a8858dc3035eab587a936f86881c2f6e673c6c2cd4dc4c53b23038c` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_plan_039_1005.md` | [implementation_plan_039_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_plan_039_1005.md) | `cd3a471558f62303800a4c4b1d35453156b35798e31307cde3fc1e2ee2ac10bc` | 整理前は未追跡。Archive側の原本を元パスへ戻せる |
| `docs/Artifacts/implementation_report_001_1004.md` | [implementation_report_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_report_001_1004.md) | `9219dc00b2a6c0e15c886bab577b5ff434212dd0b6d497ebf6714a405c5e91c0` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/implementation_report_002_1005.md` | [implementation_report_002_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/implementation_report_002_1005.md) | `4c9f9bf4a3670f79c321ac1254b4b2bc3f2923a8cf1f38f11ca490240bf59e2b` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/owner_adjudication_001_1005.md` | [owner_adjudication_001_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/owner_adjudication_001_1005.md) | `d0900f6a5f469cf76d11255856f789b7b0ef7972b85ed2f1964c792cb981a174` | 整理前は未追跡。Archive側の原本を元パスへ戻せる |
| `docs/Artifacts/qa_adjudication_001_1005.md` | [qa_adjudication_001_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_adjudication_001_1005.md) | `936dfc44f767ed7d9d7ffde227dc3445aded63b8372625291c26d4f9ab3a462a` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/00_invite.md` | [00_invite.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/00_invite.md) | `0043edf3f2396586de2afaa230d73801701948928e2cb9d99db41a2af393c153` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/01_review.md` | [01_review.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/01_review.md) | `0641c33eb8ccc636095c082a670b8c46177e0d8cf406e7a01dd542b4e0c14017` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/02_tasks.md` | [02_tasks.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/02_tasks.md) | `93c31586ae72fb9c0a4902f6ef295cea959d132ce2eab93ecb6b3b3d1f88e30b` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/03_machine.json` | [03_machine.json](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/03_machine.json) | `a5b12ca37f98f757b95716cc06b26bcbc8a478c15bcd0530ad4941b110c93301` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c3/STATUS.md` | [STATUS.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/STATUS.md) | `4f8e9e45f8a9e1843b81eaf3bdf52a6b778d415d23bf985774a9d34a43f69bd5` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/00_invite.md` | [00_invite.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/00_invite.md) | `0c92deef0ac7338d6b9942e238a15558c0ace110130c0eed584d94e90bd0fa20` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/01_review.md` | [01_review.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/01_review.md) | `d034b29d80c8b3673ddab66a56ebb9072119d579590b8d390e1a5655db867d49` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/02_tasks.md` | [02_tasks.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/02_tasks.md) | `34263f63d57c6b0e814a8bd23dfe1ad4c8ad077eb55059e31902b9a427195b98` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/03_machine.json` | [03_machine.json](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/03_machine.json) | `dadac58e230d141aa9f6f845fafd1b4c782453e3cff418fb7ee91f9d01d960ec` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_cycles/unify-qa-skill-workflow/c4/STATUS.md` | [STATUS.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/STATUS.md) | `c26de83abdc9496cd1301470918ec39ecca1cf389ef0ae1c6504da1800d1c431` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_implementation_baseline_001_1004.md` | [qa_implementation_baseline_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_implementation_baseline_001_1004.md) | `d4348be5b52589dedcf1e72b2ea730312f56a84a903e5d6d2de40abe70a5f56c` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_invite_001_1004.md` | [qa_invite_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_invite_001_1004.md) | `b915f0a5bb8e3a3ca97c841f4a83c46dc98918049a98aa19420728c460b189db` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_invite_002_1004.md` | [qa_invite_002_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_invite_002_1004.md) | `f54e68e0e22d5a95c29f0b82534059ae9f0d5ab0ce137ab9f2817e4732b3cace` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_invite_003_1004.md` | [qa_invite_003_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_invite_003_1004.md) | `1bb6438abc4025d4d213e4c099c228fff05b4193e0354b25fa00ffe60951b51e` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_review_001_1004.md` | [qa_review_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_001_1004.md) | `d655a822e157b7a9e773dee4d2505201a15a2bbf67f641bb77453e449497c865` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_review_003_1004.md` | [qa_review_003_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_003_1004.md) | `bdc999f1cd5c3e5127ebf97d8658b83e26b8011df15df5913ead6d82460a0f52` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_review_003_cycle2_local_1005.md` | [qa_review_003_cycle2_local_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_003_cycle2_local_1005.md) | `76fc9bb1c73bef926186a3eda46ff361aefba9a54f1d3606bd5c8ac05982399b` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_review_evaluation_001_1005.md` | [qa_review_evaluation_001_1005.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_evaluation_001_1005.md) | `cbe141ff97b79b1b2f4f7d62ffa7edc295eb1290870e64f2d23557f637a3271c` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_runtime_inventory_001_1004.md` | [qa_runtime_inventory_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_runtime_inventory_001_1004.md) | `adbd238e06e820644e6452a49a74734f4bb661e022a43d555b269944dcc1e52b` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_source_manifest_001_1004.md` | [qa_source_manifest_001_1004.md](qa_workflow/unify-qa-skill-workflow/artifacts/qa_source_manifest_001_1004.md) | `d7eee6cfc7591c57912f7d3bb75935c13ccad3e07639dce8be3e934af0facd50` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_state_001_1004.json` | [qa_state_001_1004.json](qa_workflow/unify-qa-skill-workflow/artifacts/qa_state_001_1004.json) | `b5bdb4d9c842c9c5cf21f01786c7575a62f4631f48fbd04c2cd0242a05e61449` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_state_002_1004.json` | [qa_state_002_1004.json](qa_workflow/unify-qa-skill-workflow/artifacts/qa_state_002_1004.json) | `437ee4f679ab8711bfaba8855c96c993630d4234cf60b49e715fdec2e7a98bda` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |
| `docs/Artifacts/qa_state_003_1004.json` | [qa_state_003_1004.json](qa_workflow/unify-qa-skill-workflow/artifacts/qa_state_003_1004.json) | `61ebe4709bb964841675c930f0a30ed62e8e75ff5d6882293cc7d58db22398f2` | 原本をArchive内に保存。管理下原本はGit履歴から復元可能 |

## Archive索引

本書は[Archives README](README.md)に索引登録した。Artifactsには作業計画Plan 040だけを残している。
