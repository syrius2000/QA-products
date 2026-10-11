# 独立再QA結果: simplify-qa-status-display

created: 2026-10-11 18:51 (JST)
update: 2026-10-11 18:51 (JST)
author: Claude Code (Claude Opus 5.5)

## 結論

固定基準AC-001〜AC-010は10件すべて合格です。初回QAの不合格所見F-01〜F-03は、いずれも解消を確認しました。基準外の所見が2件あり、固定基準の合否とは分けて記録します。

| AC | 初回 | 再QA | 根拠 |
| --- | --- | --- | --- |
| AC-001 日本語既定と5工程 | 不合格 | 合格 | F-02解消、E-02 |
| AC-002 英語選択と動作不変 | 合格 | 合格 | E-02, E-03 |
| AC-003 判定領域と値の維持 | 合格 | 合格 | E-04 |
| AC-004 状態・停止理由の区別 | 合格 | 合格 | E-02, E-04 |
| AC-005 機械契約と保存状態の不変 | 合格 | 合格 | E-03 |
| AC-006 正本・配布物と検証 | 合格 | 合格 | E-01, E-05 |
| AC-007 独立QAの証拠 | 合格 | 合格 | 本書 |
| AC-008 QA基準の事前確認と再利用 | 合格 | 合格 | 基準と版 |
| AC-009 状態対応と複合条件 | 不合格 | 合格 | F-03解消、E-02 |
| AC-010 評価対象版とサイクル | 不合格 | 合格 | F-01解消、E-04 |

## 基準と版

基準は初回と同じ[基準票](qa_acceptance_criteria_001_1011.md)のAC-001〜AC-010です。基準の追加・削除・緩和は行っていません。対象版は[修正結果と再QA依頼](qa_repair_report_001_1011.md)が示す修正後の作業ツリーです。

| 対象 | SHA-256 | 照合 |
| --- | --- | --- |
| 基準票 | `c34090dd95bcb51b51a387ffa3e26d2c43b8c4d0c40eea0ed8437fe76e2cc0ec` | 一致 |
| 計画書040 | `07823805fc1e8014f16745146ab5d7a8b0c60c3366650a74c3f3e726a498ed00` | 一致 |
| OpenSpec仕様差分 | `ba38d766052b32e4fa49a3bb6af1ac9a896d27ff4a5f0ddf3167f388d392cd98` | 一致 |
| 初回独立QA報告 | `c59a91693f9818e792fa893a513029c7aa7945768c8eb58ab8f61e6dce1a25b7` | 一致 |
| `quality-loop/`作業ツリー | `e1ccd7fe1e9f9a14fb72077b2e8c5a5818b61871e0cdb80a65f874e11c428114` | 開始時・終了時とも一致（31ファイル） |

ブランチは`codex/qa-status-ja-default`、HEADは`aacdbe77e29072bf604aa0bb727c618bfae2a62d`です。

### 独立性と実行経路

実装・修正担当はCodex (GPT-6)です。本再QAは初回と同じ別担当のClaude Code (Claude Opus 5.5)が、実装とは別のチャットで実施しました。修正報告書の自己申告は合否の根拠にせず、すべて自分で実行して確かめました。

動作確認には一時ディレクトリのGitリポジトリと正式案件を使いました。初回QAで作成したプローブを再利用し、正式案件用のプローブを1本追加しました。初回のプローブは作成時から改変されていないことを更新日時で確認しました。比較には、初回QAで`git archive HEAD`から展開した変更前の版を使いました。

## 初回所見の解消確認

### F-01 過去の評価勧告の表示: 解消

- 対象: [quality_loop/status_display.py:60-80](../../quality-loop/quality_loop/status_display.py#L60-L80)。テキスト表示と再開用Markdownが、この共通関数を使うようになりました。
- 方法: 対象版`rev-1`で`accept-with-conditions`を記録しました。その後、Ownerが`rework-requested`と`baseline_update`で対象版を`rev-2`へ変更しました。正本と2つのruntimeで同じ手順を実行し、3つの出力は完全に一致しました。
- 期待: 過去の勧告を、現在版`rev-2`の結果として表示しないこと。
- 観測: 評価直後は、勧告に対象版`rev-1`、サイクル3、case Revision 9が付きました。`rev-2`への変更後は、日本語テキスト・英語テキスト・再開用Markdownのいずれも、現在版は未記録で、勧告は過去評価と表示しました。

```
評価対象版（baseline.target_revision）: rev-2
Reviewer評価勧告: 未記録（現在版）。過去評価（case Revision 9、対象版・サイクル未特定）: 条件付き受入推奨（accept-with-conditions）
Reviewer recommendation: not recorded for current revision; historical assessment (case Revision 9, target and cycle unknown): accept-with-conditions
```

### F-02 依頼文と不備一覧の欠落: 解消

- 対象: [qa_workflow/status_display.py:184-191](../../quality-loop/qa_workflow/status_display.py#L184-L191)
- 方法: quality-qaの全経路で、変更前の版のテキスト出力に含まれる依頼文の本文と各「確認事項」行を取り出しました。修正後の日本語・英語の出力に、それぞれが全文含まれるかを照合しました。正本では16の状態、quality-qa runtimeでは11の状態で実行しました。
- 観測: 実行した全状態で、日本語・英語とも全文が含まれていました。対象は、prepared、finalize後、handoff後、invalid（不備、訂正待ち）、content_pending、reviewed（FAIL、INCONCLUSIVE、HOLD、PASS）、planned、approved、submitted、decision、再QA依頼です。invalidの不備一覧は50件すべてが表示されました。`prepare`の操作直後のテキスト出力にも「渡す文書」が表示されました。JSONの`依頼文`と`issues`は変更前の版と同一でした。

### F-03 訂正版受領後の矛盾: 解消

- 対象: [qa_workflow/status_display.py:39-40](../../quality-loop/qa_workflow/status_display.py#L39-L40)
- 方法: `correction`の後に訂正版を`acquire`しました。これで状態が`content_pending`、`pending_correction`記録ありになります。
- 観測: 停止としての訂正待ちが、一般工程の説明より先に詳細欄に表示されました。詳細と次の操作は矛盾しません。

```
QA依頼 QA-001 ／ サイクル 1 ／ 工程 QA・確認
詳細: 停止: レビュー結果の不備または訂正待ち。記録された次の操作と必要入力を確認してください
担当: ユーザー→別のレビュー担当
操作: 訂正依頼文を渡してください
必要入力: docs/Artifacts/qa_correction_001_1011.md
```

## 証拠

### E-01 自動テストと構造検証

`quality-loop/`で、Pythonキャッシュを生成しない設定で`pytest -q`を実行しました。332件とsubtest 125件がすべて成功しました。`openspec validate simplify-qa-status-display --strict`はvalidでした。

### E-02 quality-qaの工程表示

全状態の工程は、初回QAと同じく仕様の対応表どおりでした。

| 状態 | 工程 |
| --- | --- |
| `draft`、`prepared` | 準備 |
| `waiting`、`content_pending`、`submitted` | QA・確認 |
| `invalid`、訂正待ちを伴う`content_pending` | QA・確認（詳細に停止理由） |
| `reviewed`、FAIL・未達あり | 修正 |
| `reviewed`、INCONCLUSIVE・必須確認未完了またはHOLD | QA・確認 |
| `reviewed`、PASS | 判断待ち |
| `planned` | 判断待ち |
| `approved` | 修正 |
| `decision` | 終了 |

### E-03 言語選択と不変性

正本では16の状態すべて、quality-qa runtimeでは11の状態すべてで、次の5点がすべて成り立ちました。runtimeでは、handoff後とPASS・HOLD・decisionの経路を実行していません。

- 言語未指定と`--lang ja`の出力が一致しました。
- `--json`の出力が`ja`と`en`で同一でした。
- `--json`の出力が変更前の版と同一でした。
- 表示前後で保存ファイルのハッシュが不変でした。
- 表示前後で`git status`が不変でした。

`--lang en`は、変更前と同じ「状況 <phase>」の形式と状態コードを使いました。正式案件でも、4つの時点すべてでテキスト表示の前後のJSONと案件ディレクトリのハッシュが一致しました。

### E-04 判定と勧告の表示

総合QA判定の4値は、工程とは別の行に、対象SHA・サイクル・依頼IDと共に表示されました。日本語ラベルは基準充足、基準未達、保留、判定不能です。再QA依頼では、現在サイクルを「なし（未記録）」とし、前回のFAILを過去の依頼・対象版・サイクルの結果として区別しました。正式案件の勧告4値、Finding状態、検証結果のラベルは初回から変わっていません。

### E-05 正本と配布物の一致

次の3組を内容比較し、差分はありませんでした。

- `qa_workflow/`と`skills/quality-qa/runtime/qa_workflow/`
- `quality_loop/`と`skills/quality-review/runtime/quality_loop/`
- `quality_loop/`と`skills/quality-response/runtime/quality_loop/`

正式案件プローブの出力も3つの経路で完全に一致しました。

### 実行ログ

ログは`/tmp/qa_reqa_simplify/`にあります。

| ファイル | SHA-256 |
| --- | --- |
| `out_formal_*.txt`（正本・2 runtimeで同一） | `2618f7a7286b5d0bc7d49d1259311bfcffa89dad3f2eb58198cfa15459be5ce4` |
| `out_qa_canon.txt` | `8060dd06efbaa8ce70f84d0c9b4ccfecd89afab2700e6afd3bab288c5ed53fdc` |
| `out_qa_runtime.txt` | `7884d7288ec191ce661dd212a5e3f34fb5768cdb1521783950f48ca943b89a26` |
| `out_pass.txt` | `57efc591a4d140970c26863987b9f22a7e28c87c8cd986c7c784d62e615e6bb9` |
| `probe_formal_reqa.py` | `b3ecc2dbc7ba7182d96c56d51548bff9f99120a2337eb1037916dbeb20ff7f6a` |

## 基準外の所見

固定基準の合否には含めません。

### O-01 対象版が変わらない裁定後も勧告を「現在版は未記録」と表示する

- 重大度: 低
- 観測: 評価後にOwnerが`held`、続けて`accepted-with-risk`を裁定しました。対象版は`rev-1`のまま変わっていません。それでも勧告は「未記録（現在版）。過去評価（対象版・サイクル未特定）」と表示されます。
- 影響: 過去の結果を現在版の結果と誤認させる方向ではないため、AC-010の不合格には当たりません。ただし残余リスク付き受入の案件を見た人が、評価なしに受入れたと読む可能性があります。
- 原因: 勧告記録のcase Revisionと現在のcase Revisionが一致するときだけ現在版と結び付けるため、Owner裁定でRevisionが進むと照合できなくなります。勧告記録自体に評価時の対象版とサイクルを保存するか、評価後に`baseline_update`がないことを裁定記録から確認する方法で改善できます。

### O-02 訂正版の受領後も「訂正依頼文を渡してください」と案内する

- 重大度: 低
- 観測: 訂正版を`acquire`した後の`content_pending`では、操作が「訂正依頼文を渡してください」、必要入力が訂正依頼のファイルのままです。実際には`confirm-content`で内容確認へ進めます。
- 位置づけ: この文言は変更前の`describe()`と同じで、本Changeは状態の案内ロジックを変更しない方針です。今回の表示はこの記録と整合しており、F-03は解消しています。案内の改善は別のChangeでの検討を推奨します。

## 作業上の記録

再QAの途中で、私のプローブがquality-reviewとquality-responseのruntime配下にPythonキャッシュを生成しました。生成は18:47で、ディレクトリ内の全ファイルが同時刻であることを確かめてから、2つの`__pycache__`ディレクトリを削除しました。以降はキャッシュを生成しない設定で実行し、終了時にruntime配下にキャッシュがないことを確認しました。作業ツリーのSHA-256には影響していません。

## 次の工程

固定基準の全項目が合格したため、OpenSpecタスク5.2の再QAは完了条件を満たしています。最終報告と利用者の終了判断は実装担当と利用者の工程です。基準外所見O-01とO-02を扱うかどうかは、利用者が判断してください。
