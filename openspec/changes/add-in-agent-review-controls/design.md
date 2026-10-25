## Context

既存の`reviewers.run`は`subprocess.run(capture_output=True)`で同期実行し、終了まで出力を保存しない。`state.json`は各roundに`attempts`・`gate`・`review`を持つが、保存後の改変を検知する情報はない。`review`が失敗したroundは同じReviewerを最大2回まで試せるだけで、別Reviewerへは切り替えられない。

## Decisions

### D1. 逐次ログとロック
- Reviewerを`Popen`で起動し、stdout／stderrを別スレッドで`review/r<N>_reviewer.log`へ逐次書き出す。timeoutでは`killpg`で子孫ごと止める。codexの最終出力は従来どおり`--output-last-message`、claude／cursorはstdoutのJSONから得る（stdoutはログと同時にメモリにも保持する）。
- ログは`review/.gitignore`（`*.log`、`.review.lock`）で追跡対象外にする。`.gitignore`は`start`が作り、既存のループでは初回のreview時に作る。
- `review`開始時に`review/.review.lock`へ`fcntl.flock`（排他・非ブロッキング）をかける。取得できなければ二重実行として拒否する。PID・開始時刻・round・toolは取得後に書き込み、終了時に内容を空にしてから解放する。OSのロックはプロセスが死ねば解放されるため、古いロックを判定して削除する処理は持たない（PR #9 P1-1: 作成直後の空ファイルを古いロックと誤認して奪う競合を排除）。`status`の表示用の情報は内容から読むが、排他の判断には使わない。

### D1b. state.jsonの排他（PR #9 P2-3）
- `state.json`の読取り→更新→保存は、`review/.state.lock`への`fcntl.flock`で直列化する（`instruct`・`commit-round`・`refreeze`・レビュー結果の保存・`finish`）。
- JSONの保存は一時ファイルへ書いてから`os.replace`で置き換え、読み手が書きかけを見ないようにする。
- 停止中・終了済みのループには`instruct`を受け付けない（PR #9 P1-2）。`finish`は、実装報告に反映されていない指示があれば拒否し、`--accept-residual`で利用者の判断を明示した場合だけ、その指示IDとともに`Spec-Review-Unconsumed-Instructions`／`Spec-Review-Unconsumed-Judgment`をtrailerに残す。

### D1c. 検査と確定の原子性（PR #9 再レビュー P2-1・P2-2）
- `review`は、レビューロックの取得後に`state.json`を状態ロックの下で再読込し、レビューできるかの判定をやり直す（取得前に読んだ古い状態のまま、別プロセスが完了したroundを再レビューしない）。再読込の前後ではReviewerを起動しない。
- `commit-round`と`finish`は、検査から`state.json`の確定までを状態ロックの下で行う。あわせてレビューロックを一時的に取って、実行中のreviewがないことを確認する（`instruct`は状態ロックの待ちに入り、確定後は「終了済み」として拒否される）。
- 状態ロックはReviewerの実行中は保持しない（実行中の`instruct`を受け付けるため）。ロックの取得順は、レビューロック→状態ロックに統一し、`commit-round`・`finish`は状態ロックを保持したままレビューロックを非ブロッキングで試すだけにして、デッドロックを避ける。

### D2. 人の指示（instruct）と一時停止（pause）
- `instruct <change> --message "<人の発言>"`は、`state.instructions`に`{id, at, text, after_round, consumed_round: null}`を追加する。`--message`が空なら拒否する。
- `commit-round`は、未消化の指示すべてについて、その原文が`r<N>_report.md`に含まれることを検証し、含まれなければcommitせず、欠けた指示を表示して拒否する。成功時に`consumed_round`を記録する。
- `start --pause round`は`state.pause='round'`を記録する。`review`が停止せず終わったとき`state.awaiting_user=true`にし、`commit-round`は`awaiting_user`の間は拒否する。`instruct`が`awaiting_user`を解除する。Gateが停止した場合（PASS・停滞・上限・HOLD）は`awaiting_user`を立てない。

### D3. 改ざん検知（HOLD）
- Reviewerへ渡したプロンプトを、attemptごとに`r<N>_prompt.attempt<k>.md`へ、最新のものを`r<N>_prompt.md`へ保存する。保存と記録（roundの`prompt_sha256`・`prompt_files`）は同じ状態ロックの下で行い、`status`も同ロックの下で検査するため、再試行・Reviewer切替の実行中に食い違いを改ざんと誤検知しない。roundには`review_sha256`（`r<N>_review.json`の内容）も記録する。
- `Session.integrity_problems()`が、記録済みのファイルのSHA-256を再計算して不一致を返す。`status`は問題があれば次の操作に`HOLD`と該当ファイルを示し、`commit-round`・`review`・`finish`は拒否する。`refreeze`は基準の再固定であり、この問題を解消しない。
- この検知は書換えの事後検出であり、書換えの防止ではない。

### D4. Reviewer切替
- 試行の上限を「1 round・1 Reviewerあたり2回」とする（既存の「1 roundあたり2回」を変更）。Reviewerが失敗して`review`が有効な結果を得られなかったroundは、同じReviewerで上限に達した後でも、未試行の別Reviewerを`review --reviewer`で指定すれば再実行できる。
- 切替後に成功した場合、roundの`reviewer`には実際に成功したReviewerが記録される。HOLD（基準ドリフト・provenance不一致）のroundは切替で解消しない。

## Risks / Trade-offs

- 逐次ログはReviewerの出力（コード断片を含みうる）をローカルのファイルに残す。追跡対象外にして、commit・squashへ入らないようにする。
- 切替を許すと、PASSを出すReviewerを探して回す運用が可能になる。ただし、各attemptのReviewerとエラーを記録し、Gateは有効な結果にだけ適用し、失敗したattemptの結果は判定に使わない。
- `instruct`の発言の真正性は検証できない（Non-goals参照）。
