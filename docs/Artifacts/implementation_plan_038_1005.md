# QA-001旧対象の裁定記録と不要branch・worktree整理計画

created: 2026-10-05 21:21 (JST)
update: 2026-10-05 21:34 (JST)
author: Codex (GPT-6)

## 目的

Owner判断「後続実装で対応済み・旧対象は廃止」を記録し、後続実装で対応済みのQA-F01・QA-F02と未実施pytestを理由に旧Reviewed SHA `7d8880b2558cfabcc517b95b10b87b5ccebae03a`へ戻って修正しないことを明確にする。QA-001のFAILレビューを監査履歴として保存したうえで、不要なQA用worktreeとbranchを整理する。

## 現状

- 現在のcheckoutは`master`、HEADは`33cbcafeb412ac006c57b66aa59522de933beafb`でclean。
- `codex/qa-skill-integration`は`ad6ca1e`を指し、そのcommitは現在の`master`に含まれる。
- `/Users/myamaguchi/.codex/worktrees/qa-skill-integration-cloud-qa`はlocal branch `codex/qa-skill-integration-cloud-qa`の`928ef88132bb8fb3634fd4b2ed9cd4f03a11265f`をcheckout中。未追跡の公開状態JSONが1件あり、SHA-256は`39fa606a04bb2e43a6b37c05b497a03e2e784a85c9b0c29105b750ed9e3dcf0a`。
- remote `origin/codex/qa-skill-integration-cloud-qa`は`2492819df6042b5256cfe234986101e804e5d185`を指し、QA-001独立レビューを含む。QA-001レビュー本文は現`master`にない。
- remote `origin/codex/unify-qa-skill-workflow`は`c981707`を指し、作業完了済みの現`master`に含まれる。
- 現`master`には受入基準の完全一致検査、提出後snapshotと再QA対象commitの照合、拒否回帰テストがあり、実装側175 tests passedとCycle 4独立QA PASSを記録している。

## 実施範囲

1. QA-001独立レビューcommitから`docs/Artifacts/qa_review_001_1004.md`を現`master`へ保存する。レビュー本文のFAIL、QA-F01/F02、必須pytest未実施の記述は改変しない。
2. cloud QA branchにだけあるQA-001依頼本文を`docs/Archives/qa_workflow/qa_invite_001_cloud_qa_1004.md`へ保存する。現`master`の同名依頼は上書きしない。
3. worktreeにだけあるrevision 4のQA-001公開状態JSONを`docs/Archives/qa_workflow/qa_state_001_cloud_published_1004.json`へ保存する。既存のrevision 1状態JSONは変更しない。
4. `docs/Artifacts/qa_adjudication_001_1005.md`を作り、Owner判断を記録する。旧QA-001は当時のFAIL記録として保持し、現行実装で同等の欠陥に対応済み・旧Reviewed対象は廃止・旧対象への追加修正は不要と記載する。
5. 保存した各ファイルのSHA-256を元データと照合し、必要箇所をOpenSpec strict validationと`git diff --check`で確認する。
6. worktreeから対象を外し、次の不要branchを削除する。
   - local `codex/qa-skill-integration`（masterに統合済み）
   - local `codex/qa-skill-integration-cloud-qa`
   - remote `origin/codex/qa-skill-integration-cloud-qa`（レビューと依頼・状態を保存した後）
   - remote `origin/codex/unify-qa-skill-workflow`（masterに統合済み）
7. 最後に`master`のclean状態、branch一覧、worktree一覧、remote branch削除結果を確認する。

## 対象外

- `master`の製品コード、仕様、QA-001の原レビュー本文の修正
- QA-001の判定をPASSへ変更、または当時の独立レビュー結果を削除すること
- `origin/master`へのpush、PR作成、main/master以外への統合
- 本計画で列挙していないbranchやworktreeの削除

## リスクと対策

- QA-001レビューと公開状態は現在のmasterにない固有記録である。削除前に別名の履歴資料として保存し、元hashとの一致を確認する。
- QA-001 target commitは現masterの祖先ではない。旧対象branchを削除した後に旧対象の完全なtreeを再現できなくなる可能性はあるが、Owner判断により旧対象は廃止する。レビュー本文にはReviewed SHAを保持する。
- remote branch削除はGitHubへの外部書込みである。明示承認後にだけ実施し、削除対象を上記2 refsに限定する。

## 承認状態

2026-10-05 21:34 (JST)、Ownerから「実装して」と明示承認を受領した。QA-001レビュー・依頼・公開状態とOwner判断記録を現`master`へ保存し、hash・JSON・OpenSpecの検証を完了した。branch/worktree削除を実行中。
