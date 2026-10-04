# QAループ統合計画024〜032の履歴

created: 2026-10-04 17:48 (JST)
update: 2026-10-04 17:48 (JST)
author: Codex (GPT-6)

## 対象期間と結論

対象期間: 2026-10-04 〜 2026-10-04

計画024〜032は、QA入口の統合、Cloud Reviewerの監査手順、全受入基準の照合、提出後snapshotの保護、QA依頼前のGit基準点づくりを同一のQAループとして検討・段階化した記録である。内容と未完了事項は現行の[統合計画033](../../Artifacts/implementation_plan_033_1004.md)へ引き継いだ。計画033を唯一の現行計画とし、本書と原計画は経緯・承認境界・復元用の履歴である。

## 更新された判断と主要成果

- 初期設計（024）では`quality-qa`を入口として、ローカル／Cloud QA、結果確認、修正計画、承認後修正、再QA、終了判断を統合する構想を定めた。初期OpenSpecは15要件、43シナリオ、39実装タスクを持つ。
- 仕様整備・ローカルSkill配置（025）は記録上完了した。これは実クラウドQA、独立QAの受入、Owner終了判断、master統合の完了を意味しない。
- QA-F01／F02の修正実装（026）は42/42タスク完了、通常QA 165成功・skip 1、追加workflow回帰37成功、OpenSpec strict検証成功と記録された。実Cloud QA、Python 3.10での実行、独立再QAは未実施。
- Cloud Reviewerに固定Skillを読ませ、監査記録と実施側タスクを返す変更（027）はOpenSpec 11/11、171テスト成功（任意JSON Schema検査skip 1を含む）と記録された。実Cloud QA、独立QA、Skill利用コピー配置、commit・push・mergeは未実施。
- 新topicへのpushとCloud QAを行う案（028）は未承認であり、実行されていない。現行のQA公開はAGENTS.mdにある限定委任、固定対象・受入基準・許可path・baseline/reviewed SHAの検査と停止条件に従う。
- QA定型実行の限定委任（029）は現行AGENTS.mdにあるQAループ節と関連する。元計画の当時の承認状態・実施見込みは原文を保存した。
- 全体改善案（030）は実装範囲を追跡可能なSkill配布パッケージと39タスクへ具体化した計画031に更新された。031は承認済みで、専用隔離worktreeに一部実装がある。作業開始時点のHEADは`ad6ca1e`と記録された。
- QA依頼前のPhase 0と、クラウドでPython等を使う場合の実行検証契約（032）は、計画031へ追加する未承認の改訂案だった。これらは計画033へ統合された。今回のアーカイブ承認は計画033の実装承認を含まない。

## 未解決事項・引継ぎ

- 計画033の実装範囲は未承認。隔離worktreeの現状・差分・未完了タスクを再確認し、計画033の承認後にだけ継続する。
- QA-F01／F02の独立再QA、Cloud Reviewerによる実際のSkill読込・監査、Python等の環境別実行、Ownerによる残余リスク・終了判断は未完了として扱う。
- GitHub push、PR、merge、外部Skill配置、deploymentは本履歴統合の対象外。計画028の未承認push案を実行済みと解釈しない。
- dirtyな元checkoutの既存差分、未追跡物、別の作業ツリー成果は変更・破棄していない。

## 元計画と復元情報

元の9文書はファイル名と記録内容を維持して`docs/Archives/qa_workflow/plans/`へ移動した。移動で切れる相対リンクだけ移動先から有効になるよう更新した。原文SHA-256は移動前の識別値、アーカイブSHA-256はリンク修復後の退避ファイルの識別値である。復元時はアーカイブSHAで退避内容を確認し、元の`docs/Artifacts/`へ戻す。元配置に戻す際、移動によるリンク差分を元の相対参照へ戻せば原文SHAと一致する。

| 元のパス | アーカイブ先 | 原文SHA-256 | アーカイブSHA-256 |
|---|---|---|---|
| `docs/Artifacts/implementation_plan_024_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_024_1004.md` | `27c427e942bee4e79555d52816fa3ebe493d576b919e6db42130e12499e77403` | `d76b2ac15f8dbd494d8589e5a1af9507e5a9117b696e9300931c7ced0dac981b` |
| `docs/Artifacts/implementation_plan_025_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_025_1004.md` | `6315d6d33b9a15ffb038a497f926cc11be738a8de0cecd79ff946d505cbc5e28` | `6315d6d33b9a15ffb038a497f926cc11be738a8de0cecd79ff946d505cbc5e28` |
| `docs/Artifacts/implementation_plan_026_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_026_1004.md` | `ec0e6e4efd39858eaefa60cbb3541fe28489885a48162df4436d5e7fcd09da43` | `ec0e6e4efd39858eaefa60cbb3541fe28489885a48162df4436d5e7fcd09da43` |
| `docs/Artifacts/implementation_plan_027_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_027_1004.md` | `40f512338c3d2062545fb51a3cf0400d133400432c96cf318753a85fbf96333f` | `40f512338c3d2062545fb51a3cf0400d133400432c96cf318753a85fbf96333f` |
| `docs/Artifacts/implementation_plan_028_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_028_1004.md` | `6e68fa9508d5184d5d6f019766382aaa24e178caa5abdc3e5f3aa8b1b4b8700d` | `6e68fa9508d5184d5d6f019766382aaa24e178caa5abdc3e5f3aa8b1b4b8700d` |
| `docs/Artifacts/implementation_plan_029_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_029_1004.md` | `fd5fe8e693d141c9d42df06691a136e5eedb4dff650792ad50e088a3ba71c5b7` | `fd5fe8e693d141c9d42df06691a136e5eedb4dff650792ad50e088a3ba71c5b7` |
| `docs/Artifacts/implementation_plan_030_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_030_1004.md` | `86e658b2d06c15abc690ada38d9bd57c91fb7a0c788b6078014faec111a3c472` | `86e658b2d06c15abc690ada38d9bd57c91fb7a0c788b6078014faec111a3c472` |
| `docs/Artifacts/implementation_plan_031_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_031_1004.md` | `b9f64e710b960bd487ec161cf19ae4ae75554bc46f66920c84877f4913c2995c` | `b9f64e710b960bd487ec161cf19ae4ae75554bc46f66920c84877f4913c2995c` |
| `docs/Artifacts/implementation_plan_032_1004.md` | `docs/Archives/qa_workflow/plans/implementation_plan_032_1004.md` | `0f8a20b6f66eaf162181554b7d2cc093b30c3ff3b59f6198db79aac02548eff1` | `0f8a20b6f66eaf162181554b7d2cc093b30c3ff3b59f6198db79aac02548eff1` |

現行計画は`docs/Artifacts/implementation_plan_033_1004.md`に保持する。アーカイブ移動はGit commit、push、外部公開を行っていない。
