# Codex アプリ向け: spec-review-loop の実機検証手順（T-6.3）

対象: PR #9（`feat/in-agent-review-controls`）
OpenSpec change: `add-in-agent-review-controls`
目的: macOS上の実際の Codex CLI を Reviewer にして、spec-review-loop を通しで1回動かし、結果を記録する。

このファイルは検証専用です。実装の変更や、この手順の範囲を超える作業はしないでください。

---

## 0. 守ること（最初に読んでください）

- 作業は **使い捨てのブランチ** で行います。`feat/in-agent-review-controls` や `main` に直接コミットしないでください。
- **push しないでください。** PR も作らず、マージもしないでください。
- `refreeze`、`waive`、`finish --accept-residual` は、**利用者の発言がない限り実行しないでください**。この手順では使いません。
- `instruct` に渡す発言は、**利用者が実際に言った言葉を原文のまま** 使ってください。要約や推測で作った発言を渡さないでください。発言が無い場合は、`instruct` は実行せず、利用者に確認してください。
- Codex CLI の導入や認証を、この作業のために新たに行わないでください。未導入・未認証なら、**そこで止めて報告**してください（§5）。
- 途中で想定外の結果が出たら、無理に進めず、§5 の形式で報告してください。

---

## 1. 準備

リポジトリのルートで実行します。

```bash
cd ~/Programing/00TotalRWD/QA-products   # 実際のパスに読み替えてください
git fetch origin
git switch feat/in-agent-review-controls
git merge --ff-only origin/feat/in-agent-review-controls
git status --short            # 何も出なければ正常（clean）
git log --oneline -1          # c4d02a5 以降であること
```

`git status` に変更が出る場合は、作業を止めて報告してください。

使い捨てのブランチを作ります。

```bash
git switch -c check/t63-codex
```

CLI の場所を変数に入れておきます。

```bash
CLI=quality-loop/skills/spec-review-loop/bin/spec-review-loop-cli
```

## 2. 事前確認

```bash
python3 $CLI doctor --reviewer codex
```

期待する結果:
- `git` と `openspec` が見つかる
- `Reviewer codex` が「利用可」
- 必要なフラグ（`--sandbox`、`--output-last-message`、`--ephemeral`、`--cd`）に対応している

次のどれかになった場合は、作業を止めて §5 で報告してください。
- `codex` が見つからない
- 必要なフラグに対応していない
- `codex` の認証が切れている（この場合、`doctor` がどう表示するかも記録してください）

## 3. 検証対象の change

検証に使う change は、`openspec/changes/add-in-agent-review-controls/` です。これを、このブランチ上で対象にします。

このブランチには、この change の変更がすでに入っています。そのため、既存の実装を対象に、もう一度レビューの流れを回します。

## 4. 通し実行

### 4-1. 開始（一時停止付き）

```bash
python3 $CLI start add-in-agent-review-controls --reviewer codex --pause round
python3 $CLI status add-in-agent-review-controls
```

`start` が成功すること、基準の件数が表示されることを確認してください。

### 4-2. 実装報告とround commit

このブランチでは、この change の実装がすでに完了しています。`review/r1_report.md` を書き、対象をステージして round commit を作ります。

報告の書き方:
- 実装内容は、既存の差分（`git log` と `git diff` で確認）を簡潔に書く
- 検証は、実際に実行したコマンドと結果を書く（未実行なら「なし」と書く）
- T-6.3 の結果は、この時点ではまだ「未実施」と書く（これがこの検証の目的です）

```bash
git add openspec/changes/add-in-agent-review-controls/review/r1_report.md
python3 $CLI commit-round add-in-agent-review-controls
```

`commit-round` が「unstaged または untracked の変更があります」と拒否した場合は、対象かどうかを判断してください。対象外なら作業ツリーから外し、判断できなければ報告してください。

### 4-3. Reviewer の実行（バックグラウンド）と進行の確認

このコマンドは時間がかかります（数分〜15分）。別のターミナルを使い、進行を確認します。

ターミナル1:
```bash
python3 $CLI review add-in-agent-review-controls
```

ターミナル2（review の実行中に行う）:
```bash
python3 $CLI status add-in-agent-review-controls
tail -f openspec/changes/add-in-agent-review-controls/review/r1_reviewer.log   # Ctrl-C で停止
```

確認すること:
- `status` が「実行中」と PID・経過時間を表示する
- ログ（`r1_reviewer.log`）が時間とともに増える（codex は stderr の進行が逐次出るはずです）
- 実行中に `review` を再度実行すると、二重実行として拒否される

### 4-4. 指示の記録（利用者の発言がある場合のみ）

利用者から指示が無い場合は、この項目は省略して、その旨を報告に書いてください。

利用者の実際の発言がある場合のみ、次を実行します（review の実行中でも可）。
```bash
python3 $CLI instruct add-in-agent-review-controls --message "<利用者の発言を原文のまま>"
```

### 4-5. 結果の確認

review が終わったら、結果を確認します。

```bash
python3 $CLI status add-in-agent-review-controls
cat openspec/changes/add-in-agent-review-controls/review/r1_review.md | head -40
```

`r1_review.md` の先頭で確認すること:
- Gate（PASS、FAIL、INCONCLUSIVE、HOLD のいずれか）
- Reviewer のツール名とバージョン、モデル名（記録されていること）
- round SHA

### 4-6. 終了処理（PASS の場合のみ）

Gate が PASS の場合だけ、終了処理を通します。

```bash
python3 $CLI finish add-in-agent-review-controls            # dry-run（計画のみ）
python3 $CLI finish add-in-agent-review-controls --confirm  # 実行
```

Gate が PASS 以外なら、`finish` は実行せず、結果を報告してください。PASS 以外でのfinishには利用者の判断（`--accept-residual`）が必要で、この手順では行いません。

## 5. 報告の形式

検証の結果は、次の形式で報告してください。コマンドの出力は、そのまま貼ってください（要約しないでください）。

```
## T-6.3 検証結果

- 実行日時:
- 実行環境: macOS <バージョン> / codex <バージョン>（`codex --version`）
- 対象ブランチ・コミット: check/t63-codex / <git rev-parse --short HEAD>

### 2. doctor の出力
<貼り付け>

### 4-3. 実行中の status の出力
<貼り付け>
（ログが増えたかどうか: はい／いいえ）
（二重実行が拒否されたかどうか: はい／いいえ）

### 4-5. r1_review.md の先頭
<貼り付け>

### 4-6. finish（実行した場合のみ）
<貼り付け>

### 結果
- Gate:
- Reviewer ツール・モデル名の記録: あり／なし
- 想定外の出来事:
- 未実施の項目とその理由:
```

止めた場合（§0 や §2 に該当）は、上の「結果」だけを埋めて、止めた理由を具体的に書いてください。

## 6. 後片付け

検証が終わったら、使い捨てのブランチを捨てます。push はしないでください。

```bash
git switch feat/in-agent-review-controls
git branch -D check/t63-codex
```

作業中に作られた `review/` 配下のファイル（ログやロック）は、コミットに含めないでください。`.gitignore` で除外されているはずです。`git status` で確認してください。

## 7. この検証の結果の使い道

報告を受けた後、次を行います。
- 結果を `openspec/changes/add-in-agent-review-controls/implementation-record.md` に記録する
- T-6.3 を完了にする（成功した場合）、または未実施の理由を記録する（失敗・中断の場合）

このファイル（`CODEX_VERIFICATION.md`）は、検証のための手順書です。検証が完了したら、利用者の判断で削除できます。

---

## 8. 既知の注意点（検証前に必ず読むこと）

検証の結果を解釈するための前提です。ここに書かれていない挙動を見つけた場合は、推測で判断せず報告してください。

### 対象環境
- 対象は **macOS と Linux** です。ロックに `fcntl.flock` を使うため、**Windowsのネイティブ環境では動きません**。Windowsで検証しないでください。
- 検証は、macOS上の実際の `codex` CLI で行います。コンテナ内のテストでは、Codex は偽物で代用しています。

### 排他制御とデッドロック
- Reviewer の実行は、レビューロック（`.review.lock`）で排他します。状態の更新は、状態ロック（`.state.lock`）で直列化します。
- ロックの取得順は「レビューロック → 状態ロック」です。`commit-round` と `finish` は、状態ロックを持ったままレビューロックを非ブロッキングで試すだけです。
- デッドロックしない設計ですが、**それを確かめる専用のテストはありません**。`review` と `commit-round`・`finish` を同時に動かして、固まらないことも確認してください。
- `commit-round` が一時的にレビューロックを取る瞬間に、別の `review` が開始しようとすると、「実行中」として拒否されることがあります。これは安全側の失敗です。少し待って、やり直してください。

### 改ざん検知の性質
- SHA-256 による改ざん検知は、**事後の検出**です。書き換えを防ぐものではありません。
- stateファイルとハッシュを同時に書き換えられた場合は、検知できません。

### 指示（instruct）の扱い
- `instruct` の発言が本当に利用者のものかは、CLIでは確認できません。担保は、実装担当が原文を渡すという手順だけです。
- 発言を要約したり推測で作ったりしていないかを、必ず確認してください。

### Reviewerごとの出力の違い
- Codex は、stderr の進行が実行中のログに逐次出ます。
- Claude と Cursor は JSON 出力のため、**Reviewerが終わるまでstdoutが出ません**。実行中のログには開始行とstderrしか出ないことがあります。ログが増えないのは異常ではありません。
- `doctor` が「利用可」でも、実際の認証やモデルの利用可否は、実行してみるまで分かりません。

### 未実装・未確認
- `waive`（Findingの格下げ）は導入していません。
- 既存の `spec-review-loop`（0.1.0）は置き換えず、0.2.0 として拡張しています。
- T-6.3（この検証）は未実施です。結果が出るまで、このPRのマージは保留です。

### Macのローカル環境
- 作業用のローカルブランチ `add-spec-review-loop-base` が残っています。不要なら、利用者の判断で削除してください。
- `.pytest_cache/` に、取り込み用の bundle ファイルが残っています（git の管理外です）。
- 取り込みには、必ず `git fetch origin` を実行してください。ローカルのブランチが古いことがあります。
