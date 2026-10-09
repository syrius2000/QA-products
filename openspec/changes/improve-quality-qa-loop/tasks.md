# Tasks

## 1. 軽微な変更の判定（純粋関数）

- [x] 1.1 判定規則の失敗テストを先に書く（対象パス外、新規パス、完了条件の変更、行数上限超過、すべて満たす場合）。`pytest` で失敗することを確認する
- [x] 1.2 判定関数を実装し、1.1のテストが通ることを確認する
- [x] 1.3 判定結果（軽微か、停止理由）が記録に残ることを、テストで確認する（判定結果オブジェクトへの記録まで。状態への保存は 5.2・7.2 で確認する）

## 2. 承認文の検査

- [x] 2.1 承認文が利用者の発言と一致しない場合に受理しないテストを先に書き、失敗を確認する
- [x] 2.2 既存の `approve` に、利用者発言ログ（UserPromptSubmit hookが記録する `.git/qa-user-prompts.jsonl`）による照合を接続する。既存の承認テストは発言を再現して更新し、発言がない場合の拒否を確認する。hookは `.claude/settings.local.json` に登録済み

## 3. 修正commitの範囲

- [x] 3.1 承認文に「修正後のcommitまで」がない場合にcommitしないテストを先に書き、失敗を確認する
- [x] 3.2 承認済みパスだけをステージしてcommitする処理を実装する。`git add -A` を使わないことをテストで確認し、3.1が通ることを確認する（未承認の変更・未追跡ファイル・他者のステージ済み変更がコミットされないことで確認）

## 4. 公開前の検査と祖先確認

- [x] 4.1 機密情報・個人パス検出時にpushしないテストと、祖先関係が成り立たない場合に再QAを依頼しないテストを先に書き、失敗を確認する
- [x] 4.2 既存の `publish` の検査と `gitops.ancestor` を呼び出す処理を実装し、4.1のテストが通ることを確認する

## 5. 段階の記録と再開

- [x] 5.1 commit後に失敗した場合、再実行でcommitを繰り返さず再開するテストを先に書き、失敗を確認する
- [x] 5.2 段階（commit、submit、requa-request、finalize、publish）の完了状態を状態へ記録し、最初の未完了段階から再開する処理を実装し、5.1のテストが通ることを確認する
- [x] 5.3 `status` が完了段階、失敗段階、再開方法を返すテストを書き、実装して通ることを確認する

## 6. 同一指摘の反復と上限

- [x] 6.1 同じFinding IDが連続2サイクル未解決で停止するテストと、3サイクル上限で停止するテストを先に書き、失敗を確認する
- [x] 6.2 Finding IDの履歴とサイクル数から停止を判定する処理を実装し、6.1のテストが通ることを確認する

## 7. loop操作の統合

- [x] 7.1 承認前に修正を行わず計画を示して停止するテストと、承認後に修正・提出・公開・再QA依頼まで進むテストを先に書き、失敗を確認する（オーケストレーター `qa_workflow/loop.py` の段階で確認。実際の `Workflow` 操作はモックで置き換えている）
- [x] 7.2 `Workflow.loop` を追加し、1〜6の判定と段階（commit、submit、requa-request、finalize、publish）を接続、`cli.py` に `loop` を追加する。統合テスト `tests/test_loop_integration.py` で、承認前の停止、正常系（再QA依頼の公開まで）、公開指示なしの停止を確認する（注: 承認範囲外の判定は「対象パス外」のみ接続。軽微判定の行数上限は 9.2 で決定後に接続する）
- [x] 7.3 loopが修正担当自身の判定を記録しないことを、テストで確認する（判定段階が無いこと、判定結果を持たないことをテスト）

## 8. 文書の同期

- [x] 8.1 `quality-loop/skills/quality-qa/SKILL.md` に `loop` の操作を追加し、承認の例と停止条件を記載する
- [x] 8.2 `references/repair.md` と `references/results.md` の手順を、`loop` の実際の挙動と一致させる。文書とCLIのずれがないことを、対象操作の一覧で目視確認する
- [x] 8.3 `references/publish.md` に公開前検査と祖先確認の位置づけを追記する
- [x] 8.4 同梱runtime（`quality-loop/skills/quality-qa/runtime/qa_workflow/`）を正本と一致させる。外部配置先への同期は行わない（`tests/test_sync_productivity_skills.py` で確認）

## 9. リプレイ検証と行数上限の決定

- [x] 9.1 リプレイ検証（案B）: 既存 `unify-blind-qa-cycle` は旧4ファイル形式のため、統合テストの失敗レビュー（`unified-qa-review-v1`）をリプレイの入力とした。`tests/test_loop_integration.py` で、判定→承認→commit→提出→再QA依頼→公開までを確認。旧cycleの実データでの再生は行っていない（残余リスク）
- [x] 9.2 行数上限を50行に決定し、`qa_workflow/minor_change.py` の `MINOR_LINE_LIMIT` として記録。`Workflow.loop` の軽微判定に接続済み（行数超過・承認範囲外の停止を統合テストで確認）
- [x] 9.3 進行中の `unify-blind-qa-cycle` の手順とファイルが変更されていないことを、`git diff` で確認する

## 10. 全体確認

- [x] 10.1 全テスト（219件）が通る。標準ライブラリの `trace` で計測（pytest-cov は未使用）: 新規モジュール（loop_guard・loop_stages・minor_change・prompt_log・publish_guard・repair_commit）100%、loop 82%、workflow 88%（全体 92%）。計測は複数行シグネチャを未実行と数えるため、やや保守的
- [x] 10.2 `openspec validate improve-quality-qa-loop --strict` が通ることを確認する
