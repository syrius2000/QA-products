# Implementation record

## 検証の出力（コンテナ、Python 3.13.16）

| コマンド | 結果 |
|---|---|
| `python3 -m pytest -q quality-loop/skills/spec-review-loop/tests` | 127 passed（既存112件＋追加15件。`test_controls.py`） |
| `python3 -m pytest -q tests`（リポジトリ直下） | 3 passed |
| `openspec validate --strict add-in-agent-review-controls` | Change 'add-in-agent-review-controls' is valid |
| `python3 scripts/check_markdown_links.py`（change・Skill・README） | Markdown相対リンク検査OK |
| 差分の範囲 | `quality-qa`・`blind-qa-cycle`・`quality-review`・`quality-response`の変更なし |

## 補足

- 既存テスト1件（`test_gate.py`の再試行上限の例外メッセージ）は、仕様の変更（1 round・1 Reviewerあたり2回、別Reviewerへの切替を許可）に合わせて期待メッセージだけを「再試行の上限」へ変更した。
- killpgによる子孫プロセスの停止は、killpgをproc.kill()に置き換えると`test_timeout_kills_descendant_processes`が失敗することで検出力を確認した。
- claude／cursorアダプタは`--output-format json`のため、Reviewer終了までstdoutが出ない。実行中のログには`[srl] start`とstderrだけが出る。codexはstderrの進行が逐次出る。
- evals/evals.jsonへ、実行中の確認・人の指示・pause・Reviewer切替の4例を追加した（dogfood r1のF-001）。
- 実Claude CLIをReviewerにしたdogfoodで、`status`が実行中のPID・経過時間・ログを返すことを確認した。
- T-6.3（macOS実機のCodex CLIでの通し実行）は、この時点では未実施だった（2026-10-25に実施。下の「T-6.3 macOS実機検証」を参照）。

## PR #9 レビュー対応（並行操作）

- P1-1 ロック競合: O_EXCL＋PID書込みを、flock（OSロック）へ置き換えた。作成直後の空ファイルを古いロックと誤認しない（`test_lock_held_but_still_empty_is_not_treated_as_stale`）。
- P1-2 停止後の指示: 停止・終了後の`instruct`を拒否。未消化の指示があるfinishは`--accept-residual`での明示を要求（`test_instruct_after_stop_is_refused_and_finish_rejects_unconsumed`、`test_finish_requires_judgment_when_instruction_is_unconsumed`）。
- P2-3 state.json競合: `state_lock`（flock）で直列化し、JSONは一時ファイル＋`os.replace`で保存。5並行reviewで起動は1回だけ（`test_only_one_of_concurrent_reviews_runs`）、8並行instructが全件残る（`test_concurrent_instructs_are_all_recorded`）。
- テスト: 133件通過（前回127件＋並行系6件）。

## PR #9 再レビュー対応（検査と確定の原子性）

- P2-1: `review`はロック取得後にstateを再読込して判定をやり直す（`test_review_rechecks_state_after_acquiring_lock`）。修正前のコードでは失敗し、同じroundを2回レビューすることを確認した。
- P2-2: `finish`の検査から`finished`の確定までを状態ロックの下で行う（`test_finish_check_and_commit_are_atomic_against_instruct`）。修正前のコードでは、検査後に割り込んだ`instruct`が受け付けられ、終了に混入することを確認した。
- 追加: `commit-round`も状態ロックの下で検査・書込みを行い、実行中のreviewがあれば拒否する（`test_commit_round_is_refused_while_review_holds_the_lock`。これは修正前も別の検査で拒否できたため、回帰防止のテスト）。

## T-6.3 macOS実機検証（2026-10-25）

- macOS 27.0.1 (26A434)上の実際の`codex-cli 0.164.0`をReviewerにして、`add-in-agent-review-controls`を`check/t63-codex`の使い捨てbranchで実行した。round SHAは`9725a356fee5fb13b3c05c930704a0975eb37ecb`。
- `doctor`はCodex Reviewer利用可を返し、`start --reviewer codex --pause round`は受入基準12件・Scenario 16件で成功した。
- review中のstatusでPID・経過時間・ログ末尾を確認し、ログが25,359 bytesから219,864 bytes、完了時262,766 bytesへ増加した。同時実行のreviewは終了コード2で拒否された。
- r1の`r1_review.md`にReviewer `codex`、version `codex-cli 0.164.0`、model `gpt-6-luna`を記録した。コマンド出力は[実機検証記録](../../../CODEX_VERIFICATION.md)に掲載。
- したがってT-6.3の明示された実機実行要件は満たした。一方、spec-review-loopのr1/r2 GateはINCONCLUSIVE。r2 Reviewerは、実機結果を要約しただけでround内にコマンド出力がないことをF-001とした。出力を記録した後の独立再レビューは未実施のため、GateをPASSと扱わない。
- GateがPASS以外のため、`finish`は実行していない。使い捨てbranch/worktreeは手順に従い破棄し、元の`feat/in-agent-review-controls`、PR #9、未追跡Artifactには触れていない。

## PR #9 第4回レビュー対応（プロンプト記録・FD・finish dry-run）

- 再試行・Reviewer切替の2回目で`r<N>_prompt.md`を先に上書きし、記録（SHA-256）の更新が後になっていた。実行中の`status`が改ざんHOLDと誤表示し、実行中に異常終了すると以降が恒久的にHOLDになった。`record_prompt`で、ファイルと記録を同じ状態ロックの下で更新し、`status`・`review`・`finish`（dry-run）の検査も同ロックの下で行うようにした。プロンプトはattemptごとの別ファイルにも残し、過去のattemptの書換えも検知する。`write_text`は一時ファイル＋`os.replace`にした。
- `Popen`が失敗したときにログのFDが閉じられなかった点を修正した。
- `finish`のdry-runがPID記入前のロックを検知できなかった点を、OSロックによる判定へ揃えた。
- テスト: 141件通過（136件＋5件）。追加した5件は、修正前のコードで全て失敗することを確認した。
- 対応しない指摘: 「基準ドリフトで早期returnしたattemptの旧SHAが残る」は、その場合プロンプトを書き換えないため、記録とファイルは一致する（問題なし）。`commit-round`が一時的にreviewロックを取る瞬間の`review`の拒否は、安全側の失敗として既知（CODEX_VERIFICATION.md §8）。`Session`の責務集中、`effort`検証の重複、引数群の引き回しは、動作に影響しない構造上の指摘であり、本changeでは行わない（別changeで扱う）。


## PR #9 第5回レビュー対応（親CLI異常終了後のReviewer・attempt番号）

- 親CLIを強制終了すると、ロックは解放されるが子のReviewerは別セッションで動き続けた。その間に次の`review`が開始でき、同じログへ同時に書き込めた。`set_reviewer_pid`で子のPIDをロックに記録し、親CLIが死んでも子が生きている間は`acquire_lock`・`assert_no_review_running`（`finish`を含む）が拒否するようにした。`status`は実行中として表示する。
- 子のPIDが残っているとき、`release_lock`はロックの内容を消さない。
- attempt番号を「完了したattempt数＋1」から、「記録済みattemptと保存済みプロンプトの最大番号＋1」へ変えた。異常終了で記録されなかったattemptの番号を再利用して、前のプロンプトとハッシュを上書きしないため。
- Linuxでは、終了済みで回収されていないゾンビを実行中とみなさない（`/proc/<pid>/stat`）。macOSでは確認できないため、ゾンビの扱いは既存の`os.kill`判定のままである。
- PIDの再利用による誤判定は残る。PIDだけでは同一プロセスを完全に識別できないため、この点は既知の制約として扱う（別途、開始時刻による照合を検討）。
- テスト: 143件すべて通過（既存141件＋新規2件）。追加した回帰テストのうち2件（親CLI停止後の二重review拒否、attempt番号の再利用防止）は、修正前のコードで失敗することを確認した。前回の`or True`による誤った待機条件は、子プロセスの終了を待つ条件に直した。
