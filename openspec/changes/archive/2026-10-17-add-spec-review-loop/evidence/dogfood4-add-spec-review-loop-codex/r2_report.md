# r2 実装報告（実装担当: Claude Code / claude-opus-5-5）

## Finding対応
- F-001（T-5.1）: 前roundの未解決Findingはfindingsで再判定されている場合だけ受理し、proposalsだけで返された場合は構造不適合（「提案としてだけ返されています」）にした。また、前roundの未解決Findingは基準IDが空でも提案へ格下げしない（gate.py `demote_proposals(keep_ids=…)`、`structural_errors`、review_round.py）。テスト: `test_previous_finding_returned_only_as_proposal_is_rejected`、`test_previous_finding_without_criteria_is_kept_for_rejudgement`。
- F-002（T-3.3）: squash失敗・tree不一致の際は、finish前の状態（最終round commit＋未commitのreview成果物、finish前のstate.json、summary.mdなし）へ戻し、不要になったバックアップrefを削除する（finish.py `_rollback`）。finishは再実行できる。テスト: `test_finish_restores_on_tree_mismatch`（復元後に再実行してsquashできることまで確認）、`test_finish_restores_when_squash_commit_fails`。

## 検証
- `python3 -m pytest -q quality-loop/skills/spec-review-loop/tests`: 109 passed。
- `openspec validate --strict add-spec-review-loop`: 成功。
