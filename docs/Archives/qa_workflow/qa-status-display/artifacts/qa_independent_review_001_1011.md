# 独立QA結果: simplify-qa-status-display

created: 2026-10-11 18:24 (JST)
update: 2026-10-11 18:24 (JST)
author: Claude Code (Claude Opus 5.5)

## 結論

AC-001〜AC-010のうち、合格7件、不合格3件です。不合格はAC-001、AC-009、AC-010です。未検証として残したACはありません。

| AC | 判定 | 根拠となる所見 |
| --- | --- | --- |
| AC-001 日本語既定と5工程 | 不合格 | F-02 |
| AC-002 英語選択と動作不変 | 合格 | E-03, E-04 |
| AC-003 判定領域と値の維持 | 合格 | E-05, E-06 |
| AC-004 状態・停止理由の区別 | 合格 | E-02, E-07 |
| AC-005 機械契約と保存状態の不変 | 合格 | E-04, E-08 |
| AC-006 正本・配布物と検証 | 合格 | E-01, E-09 |
| AC-007 独立QAの証拠 | 合格 | 本書 |
| AC-008 QA基準の事前確認と再利用 | 合格 | 基準の確認記録 |
| AC-009 状態対応と複合条件 | 不合格 | F-03 |
| AC-010 評価対象版とサイクル | 不合格 | F-01 |

## 基準と対象版

基準は[独立QA基準票](qa_acceptance_criteria_001_1011.md)のAC-001〜AC-010です。基準の追加・削除・緩和は行っていません。再QAでも同じ基準票と下表の版を使います。

### 基準の確認記録

2026-10-11、利用者がこの基準票を独立QAの基準として渡すよう指示しました。指示には、ブランチと作業ツリーSHA-256、計画書040と規範仕様を根拠とすること、proposal・design・tasksを参考資料とすることが含まれます。本QAではこの指示を基準票への利用者確認として扱いました。

### 照合した版

QA開始時に全ハッシュを再計算し、基準票の記載と一致することを確認しました。QA終了時にも作業ツリーSHA-256は同値でした。

| 対象 | SHA-256 | 照合 |
| --- | --- | --- |
| 基準票 | `c34090dd95bcb51b51a387ffa3e26d2c43b8c4d0c40eea0ed8437fe76e2cc0ec` | 本QAで使用した版 |
| 計画書040 | `07823805fc1e8014f16745146ab5d7a8b0c60c3366650a74c3f3e726a498ed00` | 一致 |
| OpenSpec仕様差分 | `ba38d766052b32e4fa49a3bb6af1ac9a896d27ff4a5f0ddf3167f388d392cd98` | 一致 |
| OpenSpec提案 | `7e0fef5a24f23f82eb59f97c1783ceaec3faf2de4ad66b390d5daa32bbdb77ef` | 一致 |
| OpenSpec設計 | `40c354a6e0fd2ddce2cd7cdd23914c05b44c532fd6b41df8d10ebc58e43cc71c` | 一致 |
| `quality-loop/`作業ツリー | `60d856d02bf6d03da9e9695848212690c169eb000f45546117be6edb0576a7cf` | 一致（31ファイル、基準票の算出方法） |

ブランチは`codex/qa-status-ja-default`、HEADは`aacdbe77e29072bf604aa0bb727c618bfae2a62d`です。

### 独立性と実行経路

実装担当はCodex (GPT-6)です。本QAは別の担当であるClaude Code (Claude Opus 5.5)が、別のチャットで実施しました。対象コードは変更していません。動作確認は`/tmp/qa_probe_simplify/`の一時ディレクトリに作ったGitリポジトリと正式案件で行いました。比較用に`git archive HEAD`で変更前の`quality-loop/`を同ディレクトリへ展開し、変更前後のCLI出力を並べました。

## 所見

### F-01 正式案件で過去の評価勧告を現在の対象版と並べて表示する

- 重大度: 高
- 対象AC: AC-010
- 対象: [quality_loop/status_display.py:178-185](../../../../../quality-loop/quality_loop/status_display.py#L178-L185)、[quality_loop/markdown_report.py:225-235](../../../../../quality-loop/quality_loop/markdown_report.py#L225-L235)
- 観測: `status --format text`と再開用Markdownは、最新の最終リスク評価を対象版やcase revisionと照合せずに「Reviewer評価勧告」として表示します。
- 再現: 対象版`rev-1`で`assess-risk`に`accept`を記録しました。続けてOwnerが`rework-requested`と`baseline_update`で対象版を`rev-2`に変更しました。
- 期待: 仕様「修正後の版が未評価」では、過去の結果を過去版・過去サイクルの結果として示し、現在版の判定として再利用しません。
- 実際: 状況表示が次のとおり並び、`rev-2`が受入推奨と評価されたように読めます。

```
評価対象版（baseline.target_revision）: rev-2
サイクル: 3/5
Reviewer評価勧告: 受入推奨（accept）
```

再開用Markdownも同じく`rev-2`と「Reviewer評価勧告: 受入推奨（accept）」を並べます。最終リスク評価Markdownだけは評価時のrevisionで照合しており、`rev-1`の評価として正しく示します。テキスト表示と再開用Markdownにも同じ照合が必要です。

### F-02 状況のテキスト表示から渡す依頼文と不備一覧が消えた

- 重大度: 中
- 対象AC: AC-001（詳細の意味を失わない）。英語表示にも同じ欠落があります。
- 対象: [qa_workflow/cli.py:92-107](../../../../../quality-loop/qa_workflow/cli.py#L92-L107)、[qa_workflow/status_display.py:119-174](../../../../../quality-loop/qa_workflow/status_display.py#L119-L174)
- 観測: JSONを指定しない`status`と、依頼IDを返す全操作のテキスト出力が新しい表示関数を通ります。この関数は「渡す文書」と「確認事項」を出力しません。
- 期待: 変更前のテキスト出力は、渡す依頼文の本文と、レビュー不備の各項目を表示していました。quality-qaのSKILL.mdも、利用者に渡す依頼文を示すよう指示しています。
- 実際: 不備のあるレビューを取り込んだ`invalid`状態で、変更前は不備50件を列挙していました。変更後は日本語・英語とも「結果の不備または訂正待ちです」だけを表示し、何が不備かを示しません。`prepare`、`finalize`、`handoff`の後も依頼文の本文が出なくなりました。

JSON出力の`issues`と`依頼文`は変更前と同一です。欠落は人向けテキスト表示に限られます。

### F-03 訂正版の受領後に工程の詳細と次の操作が矛盾する

- 重大度: 中
- 対象AC: AC-009
- 対象: [qa_workflow/status_display.py:29-50](../../../../../quality-loop/qa_workflow/status_display.py#L29-L50)
- 観測: 工程の判定は`phase`だけを見ており、`pending_correction`を参照しません。訂正版を`acquire`すると、内容確認まで`phase`が`content_pending`、`pending_correction`が記録済みの状態になります。
- 期待: 設計の優先順位1では、訂正待ちを一般工程より先に停止状態として表示します。
- 実際: 次のとおり、詳細はレビュー内容の確認待ち、操作は訂正依頼文を渡すことを示します。利用者はどちらを行えばよいか判断できません。

```
QA依頼 QA-001 ／ サイクル 1 ／ 工程 QA・確認
詳細: 取得したレビュー内容の妥当性を確認待ち
操作: 訂正依頼文を渡してください
理由: 結果の不備または訂正待ちです
```

操作と理由の文言は変更前の`describe()`と同じです。工程表示がその記録と整合していないことが不合格の理由です。

## 合格ACの証拠

### E-01 自動テスト

`quality-loop/`で`python3 -m pytest -q`を実行し、328件とsubtest 123件がすべて成功しました。`openspec validate simplify-qa-status-display --strict`はvalidでした。

### E-02 quality-qa CLIの工程表示

実際のCLIで依頼を進め、各状態で既定・明示`ja`・`en`のテキストとJSONを取得しました。

| 状態 | 表示された工程 |
| --- | --- |
| `draft` | 準備 |
| `prepared` | 準備 |
| `waiting` | QA・確認 |
| `invalid` | QA・確認（詳細に不備・訂正待ち） |
| `content_pending` | QA・確認 |
| `reviewed`、FAILで未達あり | 修正 |
| `reviewed`、INCONCLUSIVEで必須確認未完了 | QA・確認 |
| `reviewed`、HOLD | QA・確認 |
| `reviewed`、PASS | 判断待ち |
| `planned` | 判断待ち |
| `approved` | 修正 |
| `submitted` | QA・確認 |
| `decision` | 終了 |

`published`、公開走査拒否、未知の状態は、単体テストで確認しました。いずれも担当・操作・理由・必要入力が併記されました。

### E-03 日本語既定と英語選択

全状態で、言語未指定と`--lang ja`の出力は一致しました。`--lang en`は変更前と同じ「依頼 … ／ サイクル … ／ 状況 <phase>」の形式と状態コードを使いました。正式案件の`status --format text --lang en`も状態コードと評価コードを表示しました。`--lang fr`はどちらのCLIでも入力エラーで終了コード2となり、許容値を示しました。

### E-04 JSONと保存状態の不変

quality-qaの全状態で、次の4点がすべて一致しました。

- `--json`の出力が`ja`と`en`で同一でした。
- 変更前の版のJSONと同一でした。
- 表示前後で保存ファイルのハッシュが不変でした。
- 表示前後で`git status`が不変でした。

正式案件でも、`--format text`の日本語・英語表示の前後でJSONと案件ディレクトリ全体のハッシュが一致しました。既定の`status`はJSONを返し、textと`--resume-format`の同時指定は拒否されました。

### E-05 総合QA判定の4種類

実際のCLIで、PASS、FAIL、HOLD、INCONCLUSIVEの4値すべてが工程とは別の行に表示されました。日本語では基準充足、基準未達、保留、判定不能と表示し、原コードを併記しました。各判定には対象SHA、サイクル、依頼IDが付きました。結果がない場合は「なし（未記録）」と表示し、新しい判定値は生成しませんでした。

### E-06 正式案件の勧告とFinding結果

評価勧告4値、Finding状態11値、検証結果9値のすべてに日本語ラベルがあり、原コードを併記しました。受入基準別の判定と実行checkの結果は、状況表示コードの表示対象ではありません。この2つは4スキルの参照文書が日本語の意味と原コードの保持を指示しており、文書の確認とSkill契約テストで確認しました。

### E-07 停止と終了の区別

未検証（`unverified`）、保留（HOLD、`held`）、失敗（FAIL）、修正提出（`submitted`）、独立検証済み（`verified`）、利用者の終了判断（`decision`）は、互いに異なる表示になりました。`accepted`、`accepted-with-risk`、`rejected`は終了工程の中で別の詳細を示しました。`held`は停止理由とOwner裁定の必要を表示しました。

### E-08 変更範囲

`engine.py`、状態遷移、認可のコードは変更されていません。`workflow.py`の変更は読み取り専用の`status_text`の追加だけです。

### E-09 正本と配布物の一致

正本と各Skillの`runtime/`の内容比較で差分はありませんでした。比較した組は次の3つです。

- `qa_workflow/`と`skills/quality-qa/runtime/qa_workflow/`
- `quality_loop/`と`skills/quality-review/runtime/quality_loop/`
- `quality_loop/`と`skills/quality-response/runtime/quality_loop/`

## 基準外の所見

固定基準の合否には含めません。

- **日本語ラベルの文言差**: 正式案件の評価勧告は計画書040の表示案と文言が異なります。例えば`accept`は計画書の「受入を推奨」に対し「受入推奨」です。実行checkの`PASS`も計画書の「確認成功」に対し、Skill文書では「実行成功」です。意味と種類数は保たれています。
- **未達と必須確認不足の重なり**: `reviewed`でFAILと必須確認未完了が重なると、工程はQA・確認になります。これは記録済みの次操作と整合しています。ただし仕様と設計はこの重なりの優先順位を明記していません。

## 再QAの条件

F-01〜F-03の修正後、新しい作業ツリーSHA-256を基準票と同じ方法で算出してください。再QAは同じ基準票とAC-001〜AC-010を使い、全ACを再判定します。
