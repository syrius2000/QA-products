## Why

`spec-review-loop`は、Reviewerを別プロセスで読取り専用に起動し、Gateを決定論的に判定する。しかしReviewerの実行中は何も見えず（同期実行で、終了まで出力がない）、実装担当のエージェントが「進行を眺め、必要なら人の指示を受けて次のroundへ反映する」ことができない。また、Reviewerの出力・プロンプトが保存後に書き換えられても検知できず、Reviewerが失敗した後に別のReviewerへ切り替える手段がない。

## What Changes

- Reviewerの実行中、出力を`review/r<N>_reviewer.log`へ逐次書き出し、`status`が実行中（PID・開始時刻・ログの末尾）を報告する。同じroundの二重実行は拒否する。
- 人の指示を`instruct`で原文のまま記録し、次の`r<N>_report.md`への原文転記がない`commit-round`を拒否する。`start --pause round`では、各review後に`instruct`で人の指示を記録するまで次のroundを始められない。
- 各roundのReviewerへ渡したプロンプトと`r<N>_review.json`のSHA-256を記録し、保存後の書換えを`status`・`commit-round`・`review`・`finish`が検知してHOLDにする。
- Reviewerが失敗（起動失敗・timeout・スキーマ不適合）したroundは、同じReviewerの再試行を1回まで、未試行の別Reviewerへの切替（`review --reviewer`）を許す。

## Non-goals

- 既存のGate判定、停止条件、squash、`refreeze`、Reviewerアダプタ（Codex／Cursor／Claude）、受入基準の抽出は変更しない。
- Findingの格下げ（`waive`）は導入しない。PASS以外で終えるときの判断は、既存の`finish --accept-residual`と引継ぎの選択肢で扱う。
- `instruct`に記録する発言が人のものであることを、CLIは検証できない。実装担当が利用者の実際の発言だけを渡すことをSkillの手順で定める（`refreeze --reason`と同じ前提）。

## Impact

- 変更するspec: `spec-review-loop`（ADDED 3件、MODIFIED 1件）。
- 変更するコード: `reviewers.py`（逐次ログ）、`review_round.py`、`session.py`、`cli.py`、`render.py`、`finish.py`、`SKILL.md`、`evals/evals.json`。
- 既存のstate.jsonとの互換: 追加項目はすべて任意で、無い場合は従来どおり動く。
- `quality-qa`、`blind-qa-cycle`、`quality-review`、`quality-response`は変更しない。
