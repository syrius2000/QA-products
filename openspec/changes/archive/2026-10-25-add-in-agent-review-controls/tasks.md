# Tasks

## 1. 実行中の進行確認（reviewers.py・review_round.py・session.py）

- [x] 1.1 `reviewers.run`を`Popen`＋逐次ログに変え、timeoutでは子孫プロセスごと止める。検証: 偽Reviewer（遅延・逐次出力）でログが実行中に増え、timeoutでも孤児プロセスが残らず、既存のReviewer系テストが通る。
- [x] 1.2 `review/.review.lock`（PID・開始時刻・round・tool）と`review/.gitignore`を実装し、二重実行を拒否し、古いロックを破棄する。`status`が実行中のPID・経過時間・ログ末尾を返す。検証: spec deltaの「Reviewerの実行中に進行を確認できる」の全Scenarioをテストで再現して期待結果になり、ログとロックがround commitとsquashに入らない。

## 2. 人の指示（session.py・cli.py）

- [x] 2.4 PR #9再レビュー対応: `review`のロック取得後の状態再検証、`commit-round`・`finish`の検査〜確定の原子化。検証: ロック取得直前に別のreviewが完了する場合に再レビューしないこと、finishの検査後に割り込む`instruct`が終了に混入しないことを、修正前のコードで失敗し修正後に通るテストで確認する（test_controls.py）。
- [x] 2.3 PR #9レビュー対応: ロックをflockへ変更、state.jsonの読取り→保存を排他化、停止後のinstructを拒否、未消化の指示を含むfinishを拒否。検証: 並行実行・並行instruct・停止後指示・未消化finishのテストが通る（test_controls.py）。

- [x] 2.1 `instruct`を実装し、`commit-round`が未消化の指示の原文を実装報告に要求して消化済みを記録する。検証: spec deltaの「人の指示を原文のまま次のroundへ引き継ぐ」のScenarioのうち、転記なし拒否・転記あり成功・空指示拒否をテストで再現する。
- [x] 2.2 `start --pause round`と`awaiting_user`を実装する。検証: 一時停止の拒否、`instruct`による解除、停止条件到達時に一時停止しないことをテストで確認する。

## 3. 改ざん検知（session.py・review_round.py・finish.py）

- [x] 3.1 プロンプトの保存（`r<N>_prompt.md`）とSHA-256、`r<N>_review.json`のSHA-256を記録し、`integrity_problems`で検知して`status`・`commit-round`・`review`・`finish`を拒否する。検証: spec deltaの「保存したプロンプトと結果の書換えを検知する」の全Scenarioをテストで再現して期待結果になり、記録のない旧形式のstateは問題なしとして扱われる。

## 4. Reviewer切替（review_round.py）

- [x] 4.1 試行の上限を「1 round・1 Reviewerあたり2回」に変更し、失敗したroundで未試行のReviewerへの切替を許す。検証: 失敗後の切替成功、試行済みReviewerの拒否、全attemptの記録をテストで確認する。

## 5. 表示とSkill

- [x] 5.1 `render.py`・`cli.py`に`instruct`と`status`の実行中・HOLD表示を追加し、`SKILL.md`と`evals/evals.json`を更新する（起動条件は変えない）。検証: 既存の`test_skill.py`が通り、手順に「実行中の確認」「人の指示の扱い」「切替」が記載されている。

## 6. 統合確認

- [x] 6.1 一時リポジトリで「実行中にstatus確認 → 指示 → round間pause → 2 roundでPASS → finish」を通しで実行する。検証: round commit 2件が1 commitにまとまり、tree一致、ログがcommitに入らない。
- [x] 6.2 既存の全テストと追加テストが通り、`openspec validate --strict add-in-agent-review-controls`が成功し、差分に`quality-qa`・`blind-qa-cycle`・`quality-review`・`quality-response`の変更が含まれない。検証: テストとvalidateの出力を実装記録に残す。
- [x] 6.3 macOS実機でCodex CLIを使い、実際のchange 1件で通しで実行する。検証: Reviewerのツール・モデル名が記録され、実行中にログが増える。2026-10-25に実施し、実機出力は[`CODEX_VERIFICATION.md`](../../../../CODEX_VERIFICATION.md)、結果は[`implementation-record.md`](implementation-record.md)に記録。spec-review-loopの独立GateはINCONCLUSIVEのため、PASSとは区別する。
