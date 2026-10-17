# 実装記録: add-spec-review-loop

実施日: 2026-10-16（JST）／ 環境: macOS、Python 3.14.8、git 2.54.0、OpenSpec CLI 1.14.0 ／ branch: `feat/add-spec-review-loop`

## 自動テスト

- `quality-loop/skills/spec-review-loop/tests/`: 112 passed（一時gitリポジトリ・偽Reviewer・偽openspecを使用）。runtimeの行カバレッジは83%。CLIの表示部分はsubprocessで実行されるため計測外。
- 既存スイートへの影響なし: `quality-loop/tests` 333 passed（129 subtests）、ルート`tests` 3 passed。

## 2.1 抽出件数の照合

archive済みchange 4件と本changeで、抽出件数を`grep`による独立の数え上げ（チェックボックス行・`#### Scenario:`行）と照合した。

| change | タスク（抽出／数え上げ） | Scenario（抽出／数え上げ） |
|---|---|---|
| 2026-10-11-improve-quality-qa-loop | 37／37 | 25／25 |
| 2026-10-11-require-explicit-qa-request | 5／5 | 5／5 |
| 2026-10-11-simplify-qa-status-display | 15／15 | 18／18 |
| 2026-10-11-unify-blind-qa-cycle | 11／11 | 23／23 |
| add-spec-review-loop | 19／19 | 24／24 |

原文の一致は`tests/test_criteria.py`（タスク本文の行一致、Scenario原文の先頭一致）で確認した。

## 7.2 実機Reviewerでの通し実行

本リポジトリの外の一時リポジトリ（`/tmp/srl-sandbox`）に、小さなOpenSpec change `add-slugify`（タスク2件、Scenario2件、必須check `CHK-VALIDATE`と`CHK-UNITTEST`）を作り、実際のCLIで実行した。本リポジトリの履歴は変更していない。

| round | 内容 | Reviewer | Gate |
|---|---|---|---|
| r1 | `slugify`だけを実装（テストなし、前後のハイフンが残る不具合を意図的に含む） | codex-cli 0.160.1 ／ gpt-6-luna | FAIL（F-001〜F-003。不具合F-003も独立に検出） |
| r2 | 不具合修正とテスト追加 | codex-cli 0.160.1 ／ gpt-6-luna | PASS（F-001〜F-003を`resolved`と再判定） |

- `finish --confirm`でround commit 2件（＋summary commit）を1 commitへまとめ、tree一致を確認した。trailerに`Spec-Review-Gate: PASS`、`Spec-Review-Rounds: 2`、`Spec-Review-Reviewer: codex codex-cli 0.160.1 / gpt-6-luna`、`Spec-Review-Pre-Squash`が記録され、`summary.md`にround SHAとGate推移（FAIL→PASS）が残った。1 roundのレビュー所要時間は約20〜30秒。
- 実機実行で見つかった不具合: 必須check（`python3 -m unittest`）が一時worktreeに生成した`__pycache__`を、Reviewerの書込みと誤検出した。check実行後の状態を基準に比較するよう修正し、回帰テスト`test_files_created_by_checks_are_not_reviewer_writes`を追加した。誤検出したr2の1回目はINCONCLUSIVEとして記録され、許可された1回の再試行でPASSした（`r2_review.attempt1.raw.txt`に原文が残る）。
- `commit-round`は、テスト実行で生成された未追跡の`__pycache__`を検出して拒否した（仕様どおり）。削除してから再実行した。
- Claude CLI（2.1.296、model `claude-opus-5-5`）でも同changeを1 round実行し、PASSと、受入基準外の指摘（非ASCII文字の扱い）が提案として記録されGateに影響しないことを確認した。

証跡: [evidence/sandbox-add-slugify-codex/](evidence/sandbox-add-slugify-codex/)（criteria、各roundの報告・レビューJSON／Markdown、r2の1回目の原文、summary.md、squash commitのメッセージ）。

## 実際のchange（本change自身）での通し実行

本リポジトリのlocal clone（`/tmp/srl-dogfood`、base＝master `ac998ea`）で、本change `add-spec-review-loop`を受入基準として実行した。本リポジトリのbranch履歴は変更していない。Reviewerは利用者指定の `--reviewer codex --model gpt-6.1-sol --effort medium`（`codex exec -m gpt-6.1-sol -c model_reasoning_effort=medium`）。必須checkは`CHK-VALIDATE`と`CHK-PYTEST`（本Skillのテスト）。

| round | Gate | 内容 |
|---|---|---|
| r1 | FAIL（約6分） | F-001 squash失敗時の復元不足、F-002 スキーマ検証前の格下げ処理で内部エラー、F-003 4.1の実機確認未了、F-004 summary.mdに全基準IDがない、F-005 実機実行の証跡不足、F-006 PASS以外のfinishでtrailerに残余Findingがない |
| r2 | FAIL（約6分）→ **停滞で停止** | F-001・F-002・F-004・F-005・F-006を`resolved`と再判定。F-003（4.1）は2 round連続で未解消のため、仕様どおりround上限前に停止し、人の判断・`review-standalone`・`blind-qa-cycle`への引継ぎを案内した。新規F-007: 固定後に全基準を削除するとHOLDではなく通常の抽出エラーになる |

r1を受けた修正: F-001（commit失敗も含めバックアップへ`reset --hard`で完全復元。前提条件で作業ツリーがcleanであることを確認済み）、F-002（スキーマ検証を格下げ処理より前に実施）、F-004（summary.mdに最終roundの全基準・check判定表を追加）、F-006（`Spec-Review-Residual-Findings`trailerを追加）、F-005（本節と`evidence/`を追加）。各Findingに回帰テストを追加した。r2を受けて、F-007（ドリフト検出用の再抽出では0件を許し、削除された基準IDを示すHOLDにする）を修正し、回帰テスト2件を追加した。ループは停滞で停止しているため、finish（squash）はclone上でも実行していない。

証跡: [evidence/dogfood-add-spec-review-loop-codex/](evidence/dogfood-add-spec-review-loop-codex/)（criteria、checks、state、r1／r2の報告とレビューJSON／Markdown。SHAはclone上のもの）。

## 実際のchangeでの再実行（2〜4回目、2026-10-17）

4.1の決定（Cursor CLIの採用）後、本changeを受入基準として新しいclone上でループを最初から実行し直した。Reviewerはいずれも `codex --model gpt-6.1-sol --effort medium`、1 roundあたり約5〜6分。

| 実行 | round | Gate | 主なFinding（すべて妥当と判断し修正） |
|---|---|---|---|
| 2回目 | r1 | FAIL | 原文照合が空白を正規化していた／checkとReviewerが同じworktreeを使い、checkの改変をReviewerが読む／最終roundのレビュー失敗で前roundの残余Findingが消える |
| 2回目 | r2 | FAIL → 停滞で停止 | 上記2件を`resolved`。原文照合の前後空白許容が残り（未解消）停滞 |
| 3回目 | r1 | FAIL | finishがレビュー済みSHAとの一致を確認せず、amendした未レビューcommitをsquashできる／指紋の入力で空白をstripしていた。指紋算出の変更により以降は基準ドリフト（HOLD）になるため、この実行は終了し4回目を新たに開始した |
| 4回目 | r1 | FAIL | 前roundのFindingを提案としてだけ返すと再判定を回避できる／squash失敗の復元後にstateがfinishedのまま残る |
| 4回目 | r2 | FAIL | 上記2件を`resolved`。新規: summary commit自体の失敗時に復元されない |
| 4回目 | r3 | FAIL → round上限・停滞で停止 | 上記を`resolved`。新規: バックアップref作成が同名refで失敗すると既存refを消す |

4回目r3のFinding（バックアップrefの扱い）も修正した（今回作成したrefだけを削除し、同名refがあればfinish開始前に拒否）。回帰テストを含め112 passed。いずれの実行も、PASS以外ではround上限前でも停滞で止まり、人の判断・`review-standalone`・`blind-qa-cycle`を案内した（仕様どおり）。

### 最終版の検証ループ（5回目、1 round）と既知の課題

利用者の判断（2026-10-17）により、最終版で検証ループを1 roundだけ実行して開発を終了した。結果はFAIL（約7分）で、次の2件は妥当と判断したが、本changeでは修正せず既知の課題として残す（後続changeで対応する）。

- 既知の課題1: Reviewerが失敗（起動失敗・timeout・スキーマ不適合・書込み検出）した経路では、実行済みの必須check結果がround記録に残らず、Gateは常にINCONCLUSIVEになる。必須checkがFAILでもFAILを優先できない（review_round.py）。
- 既知の課題2: Claude／CursorのstdoutのJSONがオブジェクトでない（配列・null）場合、`final_text`／`model_name`がAttributeErrorを送出し、INCONCLUSIVEとして記録されずCLIの内部エラー（終了コード4）になる（reviewers.py）。

いずれも異常系の処理であり、正常系（実装→round commit→独立レビュー→Gate→停止→squash）は一時リポジトリでのCodex・Cursor・Claudeの実機通し実行と112件のテストで確認済み。

証跡: [evidence/dogfood2-add-spec-review-loop-codex/](evidence/dogfood2-add-spec-review-loop-codex/)、[evidence/dogfood3-add-spec-review-loop-codex/](evidence/dogfood3-add-spec-review-loop-codex/)、[evidence/dogfood4-add-spec-review-loop-codex/](evidence/dogfood4-add-spec-review-loop-codex/)、[evidence/dogfood5-add-spec-review-loop-codex/](evidence/dogfood5-add-spec-review-loop-codex/)

## Reviewerの選択肢: Cursor CLI（agent）と推論effort（4.1）

- 利用者の決定（2026-10-17）: Gemini CLIはAntigravity CLI（`agy`）へ移行したが、`agy`は使わない。代わりにCursor CLI（`agent`）を選択肢とする。Reviewerは`codex`（既定）、`cursor`、`claude`の3種。経緯: `agy` 1.3.5／1.4.0はこの実行環境で`--print`が応答を返さなかった（0 tokenのまま`--print-timeout`で終了）。
- `--model`に加え`--effort`を、codex（`-c model_reasoning_effort=`）、claude（`--effort`）、cursor（`--model 'M[effort=E]'`。パラメータ化モデルのみ）へ渡す。
- Cursor CLI `2026.10.14-941492e`の実機確認: `agent --print --mode ask --sandbox enabled --trust --workspace <dir> --output-format json`。askモードでは「ファイルを作成して」という指示を拒否し、実際に作成されないことを確認した。stdinのプロンプトを受け付け、最終出力はJSONの`result`。
- 一時リポジトリの`add-slugify`で通し実行した（`--reviewer cursor --model gpt-5.3-codex`）。r1は意図的な不具合（前後のハイフン）とテスト不足を残してcommitし、CursorがF-001・F-002として独立に検出してFAIL。r2で修正してPASS（2件とも`resolved`）。`finish --confirm`でsquashし、tree一致とtrailer（`Spec-Review-Reviewer: cursor 2026.10.14-941492e / gpt-5.3-codex`）を確認した。
- r1の1回目は「Reviewerが作業ツリーへ書き込んだ」としてINCONCLUSIVEになった（当時は書込みpathを記録していなかったため原因は未確定。単独再現では書込みなし。Cursorが検証のためにテストを実行し`__pycache__`を生成したと推定）。これを受け、Reviewerとcheckを`PYTHONDONTWRITEBYTECODE=1`で実行し、書込み検出時はpathを列挙するよう変更した（回帰テスト2件）。2回目（許可された再試行）は正常に完了した。

証跡: [evidence/sandbox-add-slugify-cursor/](evidence/sandbox-add-slugify-cursor/)
