---
name: spec-review-loop
description: >
  ユーザーが現在のメッセージで対象のOpenSpec changeを示し、spec-review-loopによるレビューループの実行を明示的に依頼した場合だけ使用する。正例: 「/spec-review-loop add-auth」「add-authをspec-review-loopで完成させて」「このchangeでレビューループを回して」。ループの仕組みの説明・相談、結果の共有だけ、一般的なコードレビュー、OpenSpec apply／verifyだけの依頼では使用しない。実装担当（このセッション）がround commitを作り、別系統のAI Reviewer（既定Codex CLI、選択Cursor CLI（agent）／Claude CLI）が読取り専用で独立レビューし、CLIがGateと停止を判定する。終了時は明示確認のうえでround commit群を検証付きで1 commitへsquashする。quality-qa、blind-qa-cycle、quality-review、quality-responseの成果物・case・状態は作成・変更しない。openspec archive、main／masterへのmerge、push、force-pushは行わない。
---

# spec-review-loop — OpenSpec changeを独立レビューで完成させる

OpenSpec changeの`tasks.md`のタスク・検証文と`specs/**/spec.md`のScenarioを受入基準として固定し、「実装 → round commit → 別系統AIの独立レビュー → Finding対応」を最大N round（既定3）自動で回す。CLIは決定論的な部分（基準抽出・指紋、commit、worktree、check実行、構造検証、Gate、停止、squash）だけを担い、実装・実装報告・Finding対応はこのSkillの手順に従って実装担当が行う。

CLIはこのSkillの`bin/spec-review-loop-cli`を使い、対象リポジトリを作業DIRとする（`--root <repo>`で指定可）。人向け表示は日本語、`--json`でJSON出力。終了コードは0成功、2契約拒否、3入出力（Reviewer失敗を含む）、4内部エラー。

## 使い分け

| 状況 | 使う経路 |
|---|---|
| OpenSpec changeを完成させるため、実装と独立レビューを自動で数往復したい | **spec-review-loop** |
| 人の承認を毎回挟む通常QA、クラウドReviewerへの手渡し | `quality-qa` |
| 監査ブランチ・Yip commit・4成果物による固定SHA監査 | `blind-qa-cycle` |
| `case.json`を正本とする正式QMS、Owner裁定・残余リスク受容 | `quality-review`／`quality-response` |

起動しない例: 「spec-review-loopの仕組みを教えて」「このPRをレビューして」「openspec applyして」「レビュー結果はPASSでした」。この場合はループを起動せず、既存QA経路の記録も変更しない。

## 手順

### 0. 起動前の確認

1. 依頼から対象change IDを特定し、`openspec list`で存在を確認する。曖昧なら確認する。
2. `spec-review-loop-cli doctor`（`--reviewer`で選択可）でReviewer CLIの導入と必要フラグを確認する。利用不可なら導入方法を示して止まる。
3. main／master上なら開始しない。topic branchへの切替を案内する（作成は利用者の指示があれば行ってよい）。

### 1. start

```bash
spec-review-loop-cli start <change-id> [--reviewer codex|cursor|claude] [--model <name>] [--effort low|medium|high] [--max-rounds 3] [--pause round]
```

- 基準を抽出して`openspec/changes/<id>/review/criteria.json`に固定し、HEADをbase SHAとして`state.json`に記録する。抽出一覧を利用者に見せる。0件や想定外の件数なら開始しない（CLIが拒否する）。
- 追加の必須checkは任意で`review/checks.json`に置く（`[{"id": "CHK-PYTEST", "argv": ["pytest", "-q"], "cwd": ".", "timeout": 600, "expected_exit": 0}]`）。`CHK-VALIDATE`（`openspec validate --strict <id>`）は常に含まれる。
- Reviewer既定値は`review/config.json`（`reviewer`／`model`／`effort`／`timeout`／`max_rounds`）でも指定できる。`review`でも`--reviewer`／`--model`／`--effort`で上書きできる。
- 指定例: Codex `--reviewer codex --model gpt-6.1-sol --effort medium`（`codex exec -m … -c model_reasoning_effort=…`になる）、Cursor `--reviewer cursor --model gpt-5.3-codex-high`（`agent --print --mode ask`で読取り専用。`agent --list-models`でモデル一覧。effortは`model[effort=…]`として渡すため、対応するモデルだけで使う）、Claude `--reviewer claude --model claude-opus-5-5`。

### 2. 各round（実装担当の作業）

1. 受入基準と（2 round目以降は）前roundの`r<N-1>_review.md`のFindingを読み、実装・修正する。タスクを`[x]`にしてよい（指紋は変わらない）。
2. 実際に検証する（テスト等）。未検証を検証済みと書かない。
3. 実装報告`review/r<N>_report.md`を書く: 対応した基準ID、変更内容、実行した検証と結果、Findingごとの対応、未対応事項。
4. 対象の変更を自分で`git add`する（`git add -A`は使わない）。round 1ではchange配下の計画ファイルが未commitならstageする。
5. `spec-review-loop-cli commit-round <change-id>`。unstaged／untrackedがあれば拒否されるので、pathごとにstageか除外かを判断する。判断できないものは利用者に確認する。
6. `spec-review-loop-cli review <change-id>`を**バックグラウンドで**実行する（Bashの`run_in_background`など）。round SHAの一時worktreeで必須checkを実行し、Reviewerを読取り専用で起動し、Gateと停止を判定する。Reviewerの出力は`review/r<N>_reviewer.log`へ逐次書き出される。
7. 実行中は`spec-review-loop-cli status <change-id>`で進行（PID・経過時間・ログ末尾）を眺め、必要なら利用者へ伝える。実行中に二重で`review`しない（CLIが拒否する）。終了後に結果（Gate・Finding）を要約して利用者に示す。

### 人の指示を受ける

- 利用者が方針や優先順位を指示したら、**利用者の発言を原文のまま**`spec-review-loop-cli instruct <change-id> --message "<発言>"`で記録する。要約・言い換え・推測で作った発言を渡さない（CLIは発言の真正性を検証できない）。
- 記録した指示は、次の`r<N>_report.md`へ原文のまま転記する。転記がないと`commit-round`は拒否する。報告には、その指示にどう対応したかも書く。
- `start --pause round`で開始したときは、各reviewの後に結果を利用者に見せ、利用者の発言を`instruct`で記録するまで次のroundに進めない。利用者が「そのまま続けて」と言った場合も、その発言を原文のまま記録する。

基準（tasks.mdのタスク本文・spec deltaのScenario・checks.json）を変えるとHOLDになる。基準の変更は利用者の明示指示がある場合だけ`refreeze <change-id> --reason "<指示>"`で再固定する。実装担当の判断で基準を緩めない。

### 3. 停止と引継ぎ

`review`の結果に従う。CLIの表示する「次の操作」を利用者へ伝える。

| 停止理由 | 対応 |
|---|---|
| Gate PASS | 終了処理（4.）へ。`openspec archive`は利用者が判断する |
| Findingの停滞（同じFindingが2 round連続で未解消、または未解消数が減らない） | 残ったFindingを示し、人の判断／`quality-review`の`review-standalone`／`blind-qa-cycle`から選んでもらう |
| round上限 | 同上。上限を超えて続けない |
| HOLD（基準ドリフト・SHA不一致） | 原因を示す。基準変更が意図的なら利用者の指示で`refreeze` |
| Reviewer失敗・timeout・スキーマ不適合 | INCONCLUSIVEとして記録される。同じReviewerは同roundで1回だけ再試行できる（計2回）。上限後は`review --reviewer <未試行の別Reviewer>`で切り替えられる。切替にも利用者の了解を得る |
| `status`が「HOLD: 記録と一致しない成果物」を示す | `r<N>_review.json`・`r<N>_prompt.md`が保存後に書き換えられている。原因を示し、利用者の判断を待つ（`refreeze`では解消しない） |

Reviewerが受入基準にない改善を求めた場合は提案として記録され、Gateにも停滞判定にも数えない。提案は必須修正として扱わない。

### 4. 終了（squash）

1. `spec-review-loop-cli finish <change-id>`でdry-runの計画（まとめるcommit、バックアップref、commit message）を表示し、利用者に確認を求める。これは履歴改変なので、利用者の明示確認なしに`--confirm`を付けない。
2. 確認後に`finish <change-id> --confirm [--message "<件名>"]`。`summary.md`を加え、`refs/spec-review/<id>/<JST timestamp>`へバックアップしてから1 commitにまとめ、tree一致を検証する。
3. PASS以外で終える場合は、利用者の判断を`--accept-residual "<判断>"`で明示する。Gateと残余Findingは要約とtrailerに残る。
4. round commitがpush済み、他のcommitが混在、作業ツリーがdirtyの場合、CLIはsquashしない。force-pushは行わない。
5. バックアップrefの削除は利用者が求めたときだけ`prune <change-id>`で表示し、確認後に`--confirm`で削除する。

## 守ること

- Reviewerのログ（`*.log`）とロックはcommit・squashの対象外。Reviewerの出力に含まれる内容を、実装担当が根拠なく採用しない。
- Reviewerは別プロセス・読取り専用。Reviewerの判定を実装担当が書き換えない。過去roundのPASSを根拠にしない。
- 成果物は`openspec/changes/<id>/review/`に残り、`openspec archive`でchangeとともに保存される。
- 外部Skillディレクトリへの配備、main／masterへのmerge、push、force-push、`openspec archive`の自動実行をしない。

参照: [Reviewer契約](references/reviewer_contract.md)、[出力スキーマ](references/review.schema.json)
