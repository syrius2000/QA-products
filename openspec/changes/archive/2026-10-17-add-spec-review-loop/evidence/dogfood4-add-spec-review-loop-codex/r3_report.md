# r3 実装報告（実装担当: Claude Code / claude-opus-5-5）

## Finding対応
- F-003（T-3.3）: finishで書込みを始めた後の全工程（summary.md・state.jsonの書込み、git add、summary commit、clean確認、バックアップref作成、squash、tree一致確認）を1つのtryに入れ、どこで失敗してもfinish前の状態（最終round commit＋未commitのreview成果物、finish前のstate.json、summary.mdなし、バックアップrefなし）へ戻す（finish.py `finish`・`_rollback`）。summary commitが作られる前の失敗では、HEADを動かさずindexとstateだけを戻す。テスト: `test_finish_restores_when_summary_commit_fails`（pre-commit hookで拒否→復元→hook除去後に再実行してsquash成功）、既存の`test_finish_restores_on_tree_mismatch`・`test_finish_restores_when_squash_commit_fails`。

## 検証
- `python3 -m pytest -q quality-loop/skills/spec-review-loop/tests`: 110 passed。
- `openspec validate --strict add-spec-review-loop`: 成功。
