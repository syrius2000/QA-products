# r2 実装報告（実装担当: Claude Code / claude-opus-5-5）

## Finding対応
- F-001（T-3.3、S-7.3）: `finish`でsquash commitが失敗した場合も含め、バックアップへ`git reset --hard`で完全に復元するようにした（finish.py:96〜102、gitops.py `restore`）。前提条件で作業ツリーclean・バックアップと同一treeを確認済みのため、捨てるのはsquash処理中の差分だけ。回帰テスト: `test_finish_restores_when_squash_commit_fails`、`test_finish_restores_on_tree_mismatch`（作業ツリーの改変も戻ることを確認）。
- F-002（T-5.1、S-4.3）: Reviewer出力のスキーマ検証を`demote_proposals`より前に行い、不適合はINCONCLUSIVE・attempt加算・再試行1回として記録する（review_round.py:105〜108）。回帰テスト: `test_malformed_reviewer_output_is_inconclusive_not_internal_error`（`findings:[null]`、`criterion_ids:null`、`criteria:"x"`）。
- F-004（T-5.3）: `summary.md`に最終roundの全基準ID・必須checkの判定表を追加した（report.py）。回帰テスト: `test_review_and_summary_markdown_contain_required_items`で全基準IDの表行を確認。
- F-006（T-6.1、S-7.4）: PASS以外の`finish`で`Spec-Review-Residual-Findings: <ID…>`trailerを追加した（finish.py:66〜69）。回帰テスト: `test_non_pass_finish_records_residual_findings_in_trailer`。
- F-005（T-7.2）: 一時リポジトリでの実機実行の証跡（criteria、各roundのレビューJSON／Markdown、summary.md、squash commitメッセージ）を`evidence/sandbox-add-slugify-codex/`に追加し、本changeでの通し実行（このループのr1結果）をimplementation-record.mdに記録した。このループのr1_review.json／mdもr2 commitに含まれる。
- F-003（T-4.1）: 未解消。agy（Gemini CLIの後継）アダプタを追加したが、この実行環境ではagyが応答を返さず、最終出力の取得まで確認できていない。Gemini CLIは未導入。利用者の判断待ち。

## 検証
- `python3 -m pytest -q quality-loop/skills/spec-review-loop/tests`: 95 passed。
- `openspec validate --strict add-spec-review-loop`: 成功。
