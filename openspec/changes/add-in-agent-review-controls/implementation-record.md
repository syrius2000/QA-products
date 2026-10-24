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
- T-6.3（macOS実機のCodex CLIでの通し実行）は未実施。実施まで完了扱いにしない。
