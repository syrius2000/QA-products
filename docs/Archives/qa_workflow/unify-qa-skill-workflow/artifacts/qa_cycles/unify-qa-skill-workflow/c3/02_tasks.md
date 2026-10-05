# QA-003 Cycle 3 実施側タスク

created: 2026-10-05 15:55 (JST)
update: 2026-10-05 15:55 (JST)
author: Codex (GPT-6)

Gate: **FAIL**。修復対象1件、Task 1件。製品・仕様の実装修正はこの依頼の範囲外であり、実施承認後に進める。

## T-C3-01 — 最終走査の停止境界と拒否後の回復を揃える

- closes: **QA-C3-F01**
- repair_surface: **code**
- 対象: 正本/配布workflow.py、契約test、unified-qa-workflow/spec.md、publish.md。
- 作業: 対象SHA確定前/後で公開停止境界を明確化し、承認した契約にruntime・OpenSpec・公開手順を合わせる。最終走査拒否時も作成済み対象commitと最終依頼hashを整合した非公開状態として保持するか、採用する停止契約に沿った安全な回復経路を設ける。
- 完了条件: 最終化で危険内容/走査失敗が発生しても招待commitとremote更新はなく、対象外index不変。HEAD/依頼/stateの状態が仕様どおりで、原因解消後に既存対象commitを再利用して再試行できる。
- 検証: 未確定対象でfinalize後secret/個人パスを注入するfixture、拒否後のstate/hash照合と回復再試行fixtureを追加し、正本/配布同期、pytest全suite、OpenSpec strictを固定SHAで再検証する。

spec.md:119とpublish.md:21の「対象commit前停止／commit開始禁止」を、実際の対象SHA確定と最終依頼生成の順序に照らして合意する。Reviewerはこの文書で要件変更やOwner裁定を行わない。対象外index/既存差分を戻すためのreset、stashや既存QA記録の編集を回復手段にしない。

QA-F01/QA-F02は今回の再確認では解消所見であり、旧記録・製品のFinding状態は変更していない。詳細は[レビュー](01_review.md)、構造化対応は[機械記録](03_machine.json)を参照する。
