# Design

## Context

既存QA経路は次の3種類である。

- `quality-qa`: 通常QA。単一Markdownで、人の承認を挟む。
- `blind-qa-cycle`: 監査ブランチとYip commitによる固定SHA監査。4成果物。
- `quality-review`／`quality-response`: `case.json`を正本とする正式QMS。

利用者の主な開発はmacOS上のOpenSpec SDDで、changeごとに目的・Scenario・タスクと検証文が揃う。本changeはこれを受入基準の正本とし、往復を自動化する軽量経路を加える。動作契約は[proposal.md](proposal.md)と[spec delta](specs/spec-review-loop/spec.md)を参照する。

既存資産から次を引き継ぐ。

- `quality-qa/references/reviewer_contract.md`のGate優先順位（HOLD > FAIL > INCONCLUSIVE > PASS）と、基準のID・原文・順序の保持。
- `blind-qa-cycle`の「レビュー対象をcommit SHAで固定する」「main/masterで実行しない」。
- AGENTS.mdの安全弁。破壊的な履歴改変とforce-pushは明示承認を要する。

## Goals / Non-Goals

**Goals:**

- `/spec-review-loop <change-id>`の1回の起動で、実装→独立レビュー→修正を最大N round自動で回す。
- 受入基準をOpenSpec changeから機械的に抽出・固定し、Ownerによる書き起こしを不要にする。
- Reviewerを別系統のモデル・別プロセス・読取り専用にして、実装担当の自己評価にしない。
- 終了後のブランチ履歴を、change単位の1 commitへ整える。

**Non-Goals:**

- Owner裁定、残余リスク受容、正式case状態の生成（`quality-review`の領分）。
- クラウドへの手渡し、監査ブランチ運用（`quality-qa`／`blind-qa-cycle`の領分）。
- `openspec archive`、main/masterへのmerge、push、force-pushの自動実行。

## Decisions

### D1. 独立したSkillとcapabilityにする

`spec-review-loop`を新規capabilityとし、既存Skillの本文・runtimeは変更しない。既存の出力契約（単一Markdown、4成果物、case.json）とは成果物・停止規則・Git操作が異なるためである。

- 代替案: `quality-qa`にloopモードを足す。`quality-qa`は人の承認を毎回挟むことが要件の中核なので、自動往復と両立しないため採らない。

### D2. OpenSpec changeから受入基準を抽出して固定する

`start`で`openspec/changes/<id>/`を読み、`review/criteria.json`を生成する。

| 種類 | 抽出元 | ID | 判定の対象 |
|---|---|---|---|
| タスク | `tasks.md`の`- [ ] N.M …`／`- [x] N.M …` | `T-N.M` | タスク本文と「検証:」以降の文 |
| Scenario | `specs/<cap>/spec.md`の`#### Scenario:`とWHEN/THEN | `S-<cap>-<要件番号>.<n>` | WHEN/THENの成立 |
| 必須check | 固定 | `CHK-VALIDATE` | `openspec validate --strict <id>`の終了code 0 |
| 必須check | `review/checks.json`（任意） | `CHK-<名前>` | argv・cwd・timeout・期待終了code |

- 要件指紋は、チェックボックスの状態（`[ ]`／`[x]`）を除いた基準原文のUTF-8 bytesのSHA-256とする。実装担当はタスクを`[x]`にしてよく、指紋は変わらない。
- 各roundの開始時に基準を再抽出し、指紋集合が`criteria.json`と異なれば停止する（基準ドリフト）。基準を変える場合は、利用者の明示指示で`refreeze`する。
- `proposal.md`のWhy／対象外は判定には使わず、Reviewerが範囲外の改善を求めたときに「提案」へ格下げする根拠にする。
- MODIFIED／REMOVEDの要件は、要件見出しとScenarioを同じ規則で抽出する。REMOVEDは「該当機能が除去されている」ことを判定対象にする。

### D3. Reviewerは別系統のCLIを、round SHAの隔離worktreeで読取り専用に起動する

- Reviewerアダプタは`codex`（既定）、`cursor`（Cursor CLIの`agent`コマンド）、`claude`の3種とし、`review/config.json`または`--reviewer`で選ぶ。モデルは`--model`、推論effortは`--effort`で指定する。各アダプタの責務は「プロンプトを渡す」「読取り専用・承認なしで実行する」「最終出力をファイルに得る」の3点に限る。CLIのフラグは版によって変わるため、アダプタに閉じ込め、`doctor`で版と必要なフラグを確認する。
- レビュー対象は`git worktree add --detach <tmp> <round SHA>`で作った一時worktreeとし、Reviewerのcwdにする。作業ツリーの未commit変更がレビューに混ざらず、Reviewerが誤って書き込んでも本体の作業ツリーには影響しない。
- Reviewerへの入力: レビュー契約（`references/reviewer_contract.md`）、`criteria.json`、base SHAとround SHA、`git diff --stat base..round`、実装報告`rN_report.md`、前roundの未解決Finding。過去roundのPASS判定は渡さない。
- Reviewerの出力はJSON 1つ（`references/review.schema.json`）。Markdown版`rN_review.md`はCLIがJSONから生成する。
- Reviewerの起動失敗、timeout、スキーマ不適合は、PASSではなく`INCONCLUSIVE`としてroundを記録し、同roundの再試行を1回まで許す。

- 代替案: Claude Codeのサブエージェントで済ませる。手軽だが同系統モデルで同じ見落としが起きやすいため、既定にはしない（`claude`アダプタとして選べるようにする）。

### D4. roundごとにcommitで対象を固定する

- `start`はtopic branch（main／master以外）で、対象外の未commit変更がないことを確認し、現在のHEADをbase SHAとして`review/state.json`に記録する。
- 実装担当は各round終了時に`commit-round`を呼ぶ。CLIは実装報告`rN_report.md`を必須とし、変更pathを表示してからcommitする。件名は`spec-review: r<N> <change-id>`、trailerは`Spec-Review-Round: <change-id> r<N>`とする。`git add -A`は使わず、stage済みの変更と`review/`配下の成果物だけをcommitする。
- 前roundのレビュー成果物（`r<N-1>_review.json`／`.md`）は次のround commitに含める。

### D5. Gateと停止条件

Gateの判定はCLIが決定論的に行う。

1. Reviewer出力のbase/round SHAと`criteria.json`の指紋が一致しない、または基準ドリフトがある場合はHOLD。
2. いずれかの基準または必須checkがFAILならFAIL。
3. FAILがなく、必須checkにNOT_RUN／ERROR、または基準にUNVERIFIEDがあればINCONCLUSIVE。
4. 全基準と全必須checkがPASSの場合だけPASS。

構造検証として、全基準IDが同じ順序でちょうど1回ずつ現れることを確認し、欠落・追加・重複・原文改変はスキーマ不適合として扱う。

停止条件は次のとおり。

| 条件 | 判定 | 次の案内 |
|---|---|---|
| PASS | 完了 | `finish`（squash）→ 人が`openspec archive`を判断 |
| round上限（既定3）に到達 | 未完了 | 人の判断／`review-standalone`／`blind-qa-cycle` |
| 停滞: 同じFinding IDが2 round連続で未解消、または未解消数が前roundから減らない | 未完了 | 同上 |
| HOLD（基準ドリフト・SHA不一致） | 中断 | `refreeze`または原因の解消 |

FindingのIDはReviewerが付け、再roundでは前roundの未解決Findingを同じIDで`解消`／`未解消`／`未検証`／`撤回提案`のいずれかに判定させる。対応する基準のない改善要求は`提案`とし、Gateと停滞判定に数えない。

### D6. 終了時のsquash

`finish`はdry-runで計画を表示し、利用者の明示確認（`--confirm`）を受けてから実行する。AGENTS.mdの「破壊的な履歴改変」に該当するためである。

前提条件。満たさなければ何も変更せずに停止する。

- `base..HEAD`の全commitが、このchangeの`Spec-Review-Round` trailerを持つ（他の作業のcommitが混ざっていない）。
- `base..HEAD`のどのcommitも、リモート追跡refから到達できない（未push）。公開済みならforce-pushが必要になるため、squashしない。
- 作業ツリーとindexがclean。

手順。

1. `review/summary.md`を生成する（round数、各round SHA、Gate推移、残った提案、Reviewerのツールとモデル）。これを最終round commitへ追加する。
2. `refs/spec-review/<change-id>/<JST timestamp>`に現在のHEADを保存する（バックアップ。ローカルのみ、通常の`git log`には出ない）。
3. `git reset --soft <base>`で1 commitにまとめる。件名は利用者の確認を経た文言（既定: `feat(<change-id>): <proposal 1行目>`）とし、trailerに`Spec-Review: <change-id>`、`Spec-Review-Gate`、`Spec-Review-Rounds`、`Spec-Review-Reviewer`、`Spec-Review-Pre-Squash: <最終round SHA>`を付ける。
4. `HEAD^{tree}`とバックアップrefの`^{tree}`の一致を検証する。不一致ならバックアップrefへ戻して失敗を報告する。

バックアップrefは`prune`で削除する。削除後は`summary.md`に記録したround SHAへ到達できなくなる旨を`prune`の確認時に表示する。PASS以外で`finish`する場合は、`--accept-residual`で利用者の判断を明示させ、そのGateと残余Findingをtrailerと要約に記録する。

### D7. runtimeの構成

`quality-loop/skills/spec-review-loop/`に自己完結した形で置き、Python標準ライブラリだけで動かす（既存Skillの配布方針に合わせる）。

```text
spec-review-loop/
  SKILL.md
  VERSION
  bin/spec-review-loop-cli
  references/reviewer_contract.md   # Reviewerに渡す契約
  references/review.schema.json     # Reviewer出力スキーマ
  runtime/spec_review_loop/
    cli.py        # start / commit-round / review / status / finish / prune / refreeze / doctor
    criteria.py   # OpenSpec抽出・指紋
    gitops.py     # base固定・round commit・worktree・squash・検証
    reviewers.py  # codex / cursor / claude アダプタ
    gate.py       # 構造検証・Gate・停止判定
    report.py     # rN_review.md / summary.md 生成
  evals/evals.json
  tests/          # pytest（一時gitリポジトリ・偽Reviewerで検証）
```

実装担当（現在のセッション）の作業手順、つまり実装・報告作成・`commit-round`・`review`の呼び出し・Finding対応はSKILL.mdに書き、CLIは決定論的な部分だけを担う。

## Risks / Trade-offs

- **同系統の見落とし**: 既定のCodexでも完全な独立性の証明にはならない。→ Reviewerのツール・モデル名を毎round記録し、`summary.md`とtrailerに残す。
- **CLIの仕様変化**: Codex／Cursor／Claude CLIのフラグは版で変わる。→ アダプタに閉じ込め、`doctor`で確認、偽Reviewerでテストする。
- **squashによる証跡の喪失**: → レビュー成果物はchange配下に残り、round SHAは`summary.md`とバックアップrefに残る。`prune`は明示操作に限る。
- **基準抽出の取りこぼし**: tasks.mdの書式揺れ。→ 抽出結果を`start`時に一覧表示し、0件や想定外の件数なら停止する。

## Open Questions

- Gemini CLIで、読取り専用かつ承認なしで実行する指定方法（版依存）。実装タスク4.1で確認する。→ 解消。利用者の決定（2026-10-17）により、Gemini CLI（およびその後継のAntigravity CLI `agy`）は使わず、代わりにCursor CLI（`agent`）を選択肢とする。下記「Reviewer CLIの確認結果」を参照。

## Reviewer CLIの確認結果（タスク4.1、2026-10-16、macOS）

| Reviewer | 実機の版 | 使用フラグ | 読取り専用の担保 | 最終出力の取得 | モデル名の記録 |
|---|---|---|---|---|---|
| Codex CLI（既定） | `codex-cli 0.160.1` | `codex exec --sandbox read-only --ephemeral --color never -C <worktree> --output-last-message <file> [--model M] [-c model_reasoning_effort=E] -`（プロンプトはstdin） | sandbox `read-only`。execは非対話で承認待ちをしない | `--output-last-message`のファイル | `--model`指定値、なければ`$CODEX_HOME/config.toml`の`model` |
| Claude CLI | `2.1.296 (Claude Code)` | `claude --print --tools Read,Grep,Glob --permission-mode dontAsk --permission-prompts none --output-format json [--model M] [--effort E]`（プロンプトはstdin） | 使えるtoolをRead／Grep／Globに限定し、許可promptは自動拒否 | stdout JSONの`result` | `--model`指定値、なければJSONの`modelUsage`のキー |
| Cursor CLI（`agent`） | `2026.10.14-941492e` | `agent --print --mode ask --sandbox enabled --trust --workspace <worktree> --output-format json [--model M または M[effort=E]]`（プロンプトはstdin） | askモード（読取り専用のQ&A。ファイル作成の指示を拒否することを実機で確認）とsandbox | stdout JSONの`result`。`is_error`がtrueなら失敗 | `--model`指定値、なければ`auto（Cursor既定）` |

- `doctor`は各CLIの`--version`と、ヘルプ出力に上表の必要フラグ（codex: `--sandbox`／`--output-last-message`／`--ephemeral`／`--cd`、claude: `--print`／`--tools`／`--permission-mode`／`--permission-prompts`／`--output-format`、cursor: `--print`／`--mode`／`--sandbox`／`--trust`／`--workspace`／`--output-format`／`--model`）が含まれることを確認する。未導入・未対応なら導入方法を示し、終了コード2を返す。
- 実機での通し実行: Codex CLI、Cursor CLI、Claude CLIの3つとも、一時リポジトリの小さなOpenSpec changeで実際にレビューを実行し、読取り専用での起動、最終出力の取得、ツール・版・モデル名の記録を確認した（[実装記録](implementation-record.md)）。
- Reviewerと必須checkは`PYTHONDONTWRITEBYTECODE=1`で実行する。Cursorのaskモードは検証のためにテストを実行することがあり、その副作用の`__pycache__`がworktreeへの書込みとして検出されたため。書込み検出の際は、書き込まれたpathをエラーに列挙する。
- 追加の防御として、CLIはReviewer実行後に一時worktreeと本体作業ツリーの`git status`を必須check実行後の状態と比較し、書込みがあればそのレビューを不適合（INCONCLUSIVE）とする。
- Codexの`--output-schema`は、OpenAIの厳格スキーマ（全項目required）の制約と`review.schema.json`の任意項目が合わないため使わない。スキーマはプロンプトで渡し、CLIが検証する。
