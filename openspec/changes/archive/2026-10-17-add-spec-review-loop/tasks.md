# Tasks

## 1. 契約とスキーマ

- [x] 1.1 `references/review.schema.json`を作成し、基準別判定（PASS／FAIL／UNVERIFIED）、check結果（PASS／FAIL／NOT_RUN／ERROR）、Finding（ID・種別・重大度・基準ID・`path:line`・対応案・前round判定）、提案、Reviewer情報、base／round SHAを定義する。検証: 正常例・欠落例・重複例のJSONでスキーマ検証のテストが期待どおり成否を返す。
- [x] 1.2 `references/reviewer_contract.md`を作成し、読取り専用、全基準IDの順序どおりの判定、根拠の記載、範囲外指摘の提案扱い、前round Findingの再判定を定める。検証: 契約の各項目が1.1のスキーマ項目またはGate規則に対応している。

## 2. 受入基準の抽出（criteria.py）

- [x] 2.1 tasks.mdのタスクと「検証:」文、spec deltaのADDED／MODIFIED／REMOVEDのScenarioを抽出し、`T-N.M`と`S-<cap>-<要件番号>.<n>`のIDを付ける。検証: 既存のarchive済みchange 3件以上で、抽出件数と原文が手作業の数え上げと一致する。
- [x] 2.2 チェックボックス状態を除いた原文のSHA-256で要件指紋を計算し、再抽出時のドリフトを検出する。検証: `[ ]`→`[x]`では差分なし、タスク本文の1文字変更ではドリフトになるテストが通る。

## 3. Git操作（gitops.py）

- [x] 3.1 `start`のbranch・作業ツリー検査とbase SHAの記録、`commit-round`の実装報告必須・未stage拒否・trailer付与を実装する。検証: 一時gitリポジトリでmaster拒否、報告なし拒否、untracked拒否、正常commitのtrailerをテストで確認する。
- [x] 3.2 round SHAの一時worktreeの作成と、終了時・例外時の確実な削除を実装する。検証: Reviewerの成功・失敗・timeoutのいずれでも`git worktree list`に残らないテストが通る。
- [x] 3.3 `finish`のdry-run、前提条件検査（他commitの混在・push済み・dirty）、バックアップref作成、`reset --soft`によるsquash、tree一致検証、失敗時の復元を実装する。検証: 正常squash、push済み拒否、他commit混在拒否、tree不一致の模擬で復元される各テストが通る。
- [x] 3.4 `prune`を実装し、到達不能になるround SHAを表示して確認後にだけrefを削除する。検証: 確認なしでは削除されず、確認後に`refs/spec-review/`から消えるテストが通る。

## 4. Reviewerアダプタ（reviewers.py）

- [x] 4.1 Codex CLI（既定）、Cursor CLI（`agent`）、Claude CLIの読取り専用・非対話での実行方法と最終出力の取得方法を、macOS上の実機の版で確認し、design.mdのOpen Questionを解消する。検証: 各CLIの版と使用フラグをdesign.mdに追記し、`doctor`がそれらを検出できる。
- [x] 4.2 アダプタ共通インタフェース（プロンプト入力、cwd、timeout、出力ファイル）と3実装、`doctor`を実装する。検証: 偽Reviewer（固定JSONを返すスクリプト）で3アダプタ経路のテストが通り、未導入CLIでは`doctor`が導入方法を示す。

## 5. Gateと停止判定（gate.py）、成果物（report.py）

- [x] 5.1 構造検証（ID順序・重複・原文・SHA一致）とGate優先順位、提案の除外を実装する。検証: spec deltaの「レビュー結果を構造検証してGateを判定する」の全Scenarioをテストで再現して期待結果になる。
- [x] 5.2 round上限と停滞（同一Finding 2連続未解消、未解消数の非減少）の判定を実装する。検証: spec deltaの「停止条件に達したら止めて引き継ぐ」の全Scenarioをテストで再現して期待結果になる。
- [x] 5.3 `r<N>_review.md`と`summary.md`をJSONから生成する。検証: 生成物に全基準ID・Gate・Finding・提案・Reviewer情報・round SHAが含まれる。

## 6. SkillとCLIの統合

- [x] 6.1 `bin/spec-review-loop-cli`とサブコマンド（start／commit-round／review／status／finish／prune／refreeze／doctor）を実装する。終了コードは既存Skillに合わせる（0成功、2契約拒否、3入出力、4内部エラー）。検証: 各サブコマンドの正常系・拒否系がテストで期待どおりの終了コードを返す。
- [x] 6.2 `SKILL.md`を作成する。明示起動の条件と非起動例、実装担当の手順（実装→報告→commit-round→review→Finding対応）、停止時の引継ぎ、既存QA経路との使い分けを記載する。検証: descriptionが`quality-loop-skill-deployment`の明示起動要件と同じ形式（適用範囲・明示依頼例・非発火例）を満たす。
- [x] 6.3 `evals/evals.json`に起動・非起動の代表発話を追加する。検証: 起動例と非起動例をそれぞれ3件以上含む。

## 7. 統合確認

- [x] 7.1 一時リポジトリ上の小さなOpenSpec changeで、偽Reviewerにより「1 round目FAIL → 2 round目PASS → finish」を通しで実行する。検証: round commit 2件が1 commitにまとまり、tree一致、`summary.md`とtrailerの内容が正しい。
- [x] 7.2 macOS実機でCodex CLIを使い、実際のchange 1件で通しで実行する。検証: Reviewerのツール・モデル名が記録され、Gate推移が`summary.md`に残る。実行できない場合は理由を記録し、完了扱いにしない。
- [x] 7.3 OpenSpec成果物と変更範囲を最終確認する。検証: `openspec validate --strict add-spec-review-loop`が成功し、差分に`quality-qa`、`blind-qa-cycle`、`quality-review`、`quality-response`、既存QA記録の変更が含まれない。
