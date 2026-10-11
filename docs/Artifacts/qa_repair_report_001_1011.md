# 独立QA指摘への修正結果と再QA依頼

created: 2026-10-11 18:39 (JST)
update: 2026-10-11 18:40 (JST)
author: Codex (GPT-6)

## 対応状況

[独立QA報告](qa_independent_review_001_1011.md)のF-01（高）、F-02（中）、F-03（中）を、計画書040とChange `simplify-qa-status-display`の承認済み範囲で修正しました。利用者の指示は「独立QA結果の対応おねがい」です。元の受入基準、QA報告、基準票は保持し、合否を上書きしていません。

修正担当によるローカル検証が成功しても、独立QAによる指摘の解消確認とは扱いません。前回の結果は7件合格・3件不合格で、F-01〜F-03は再QA確認待ちです。

## 修正前後の対象版

- リポジトリ: `QA-products`、ブランチ: `codex/qa-status-ja-default`。
- 基点HEAD: `aacdbe77e29072bf604aa0bb727c618bfae2a62d`。
- 初回独立QAの実装作業ツリーSHA-256: `60d856d02bf6d03da9e9695848212690c169eb000f45546117be6edb0576a7cf`。
- 修正後の実装作業ツリーSHA-256: `e1ccd7fe1e9f9a14fb72077b2e8c5a5818b61871e0cdb80a65f874e11c428114`（`quality-loop/`配下31ファイル）。
- 算出方法: HEADとの差分ファイルと未追跡ファイルを相対パス順に並べ、`相対パス + NUL + 各ファイルのSHA-256 + LF`を連結したバイト列のSHA-256。基準票と同じ方法を使用します。
- 未コミットの作業ツリーを対象とします。ブランチ名だけから別チェックアウトを作成すると今回の修正は取得できないため、同じ作業ツリーの実ファイルと上記ハッシュを照合してください。

| 固定文書 | SHA-256 |
| --- | --- |
| [基準票](qa_acceptance_criteria_001_1011.md) | `c34090dd95bcb51b51a387ffa3e26d2c43b8c4d0c40eea0ed8437fe76e2cc0ec` |
| [計画書040](implementation_plan_040_1011.md) | `07823805fc1e8014f16745146ab5d7a8b0c60c3366650a74c3f3e726a498ed00` |
| [規範仕様](../../openspec/changes/simplify-qa-status-display/specs/qa-status-display/spec.md) | `ba38d766052b32e4fa49a3bb6af1ac9a896d27ff4a5f0ddf3167f388d392cd98` |
| [初回独立QA報告](qa_independent_review_001_1011.md) | `c59a91693f9818e792fa893a513029c7aa7945768c8eb58ab8f61e6dce1a25b7` |

基準票に記載された初回対象ハッシュは過去の対象版として保持し、再QA対象には本書の修正後ハッシュを使用します。受入基準AC-001〜AC-010と規範仕様の版は同一です。

## 指摘別の対応と確認

| 指摘 | 理解と対応 | ローカルの確認 | 独立再QA |
| --- | --- | --- | --- |
| F-01／AC-010 | 正式案件テキストと再開Markdownが古い勧告を現在版へ結び付けていた。共通の表示関数で勧告記録Revisionと現case Revisionを照合し、不一致は現在版未記録・過去評価と明示する | 日本語・英語の単体テスト、再開Markdown、初回QAの正式案件再現スクリプトで確認 | 確認待ち |
| F-02／AC-001 | 新しい状況表示で依頼本文と不備一覧が欠落していた。両言語で「渡す文書」と全「確認事項」を復元する | 50件の不備を省略しない単体テスト、実際のprepareと不正レビュー取得後のCLIで確認 | 確認待ち |
| F-03／AC-009 | 訂正版受領後のcontent_pendingで、pending_correctionを工程表示に反映していなかった。公開拒否に続いて訂正待ちを優先する | 訂正フラグを伴う複合条件、実際のcorrection→acquire経路、保存状態とJSON不変を確認 | 確認待ち |

F-01では評価記録に過去の対象版・サイクルのsnapshotが保存されていない場合、それらを「未特定」と示します。現在のbaselineやサイクルから過去値を補記しません。評価記録と現case Revisionが一致するときは記録された現対象版とサイクルを関連付けます。Owner裁定や後続操作でRevisionが変わった場合も、照合できない古い勧告を現在版へ適用しません。

F-03は表示の優先順位を既存の次操作案内と整合させる修正です。訂正版の受理・内容確認・有効化の処理と操作認可は既存の経路を使用します。

## 本ラウンドの変更範囲

- 正本: `quality-loop/quality_loop/status_display.py`、`quality_loop/markdown_report.py`、`qa_workflow/status_display.py`、`qa_workflow/workflow.py`。
- 配布コピー: `quality-review`と`quality-response`の正式案件表示2ファイル、`quality-qa`の通常QA表示2ファイル。
- 回帰確認: `tests/test_formal_status_display.py`、`test_markdown_report.py`、`test_qa_status_display.py`、`test_cli_outcomes.py`、`test_qa_workflow_contract.py`。
- OpenSpec記録: 別担当・別チャットによる初回独立QA報告の受領に基づき、タスク5.1を完了としました。5.2・5.3は再QAと最終報告が完了するまで未完了です。

開始時点の実装差分と未追跡文書を保持し、このラウンドでは上記の追加修正を行いました。

## 検証証拠

- 重点検証: `PYTHONPATH=. python -m pytest -q tests/test_formal_status_display.py tests/test_markdown_report.py tests/test_qa_status_display.py tests/test_cli_outcomes.py tests/test_qa_workflow_contract.py::ExecutionContractIntegrationTests::test_invalid_review_is_preserved_and_old_path_cannot_replace_reserved_correction`。53件とsubtest 64件が成功。
- 全体回帰: `quality-loop/`から`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q`を実行。332件とsubtest 125件が成功（83.24秒）。
- 配布比較: 通常QA正本とquality-qaの16ファイル、正式案件正本とquality-review／quality-responseそれぞれ13ファイルの完全一致を確認。
- 正式案件の実行確認: 初回QAの`/tmp/qa_probe_simplify/probe_formal.py`を正本と両runtimeで再実行し、3経路の出力は完全一致。対象版rev-2への変更後、日本語は「未記録（現在版）。過去評価」、英語は`not recorded for current revision; historical assessment`を表示。表示前後のJSONと保存ツリーの比較は両方True。
- 正式案件の実行ログ: `/tmp/qa_formal_repair_1011.txt`、SHA-256 `0547acbb9a1d4ee17683373e850548f3e913d9c2fe96d4d8006d18d72661425c`。
- 全体回帰ログ: `/tmp/qa_repair_pytest_1011.txt`、SHA-256 `201423177266e892e9ffc0ecf8e620def30567df8a0f877ad3bf9c1f6dc274f0`。
- `openspec validate simplify-qa-status-display --strict`: valid。
- `git diff --check`: 成功。

最初の全体回帰では、runtimeの実行確認で生成したPythonキャッシュが配布同期の追加ファイル検査に検出され、5件が失敗しました。生成日時2026-10-11 18:34:57〜58 JSTの26ファイルを確認して除去し、`PYTHONDONTWRITEBYTECODE=1`で全体回帰を再実行し、全件成功しました。製品コードで検査を回避する変更は行っていません。

## 再QA担当へ渡す依頼文

Change `simplify-qa-status-display`の修正後作業ツリーについて独立再QAをお願いします。本書の対象版ハッシュと固定文書のハッシュを開始前に照合し、固定AC-001〜AC-010の全項目を「合格／不合格／未検証」で再判定してください。F-01〜F-03の各IDについて解消・未解消と期待／観測結果、対象ファイル、実行方法・出力を記録してください。

実装担当はCodex (GPT-6)です。別の担当・チャットで評価し、担当と実行経路を残してください。元のQA報告と基準を保持し、基準外の所見は固定基準の合否から分けてください。初回の不合格をローカル修正の自己申告だけで合格へ変更しないでください。

F-01では対象版rev-1で勧告を記録し、Ownerのrework-requestedとbaseline_updateでrev-2へ変更した後の、日本語テキスト・英語テキスト・再開Markdownを確認してください。F-02ではprepare／finalize／handoffの依頼本文とinvalid状態の全不備一覧を、両言語とJSONで確認してください。F-03ではcorrection後の訂正版acquireによりcontent_pendingかつpending_correctionとなった状態で、停止の詳細・次担当・次操作・必要入力を確認してください。関連する保存データとJSONが表示前後で不変なことも確認してください。

成果物はこのリポジトリの`docs/Artifacts/qa_independent_review_002_1011.md`へ、リポジトリの採番・日本語・JSTヘッダー規則に沿って保存してください。同名ファイルがすでにある場合は既存成果物を保持し、同スラッグの最大連番に1を加えてください。

## 固定受入基準の原文

以下の原文は計画書040の「受入基準」節から転記し、内容を変更していません。`AC-001`から`AC-010`は独立QAでの追跡用に付与したIDです。

### AC-001 — 日本語既定と5工程

> 言語未指定で、4スキルの状態説明が日本語となり、工程・担当・操作・理由・必要入力を理解できる。基本表示は「準備／QA・確認／修正／判断待ち／終了」の5工程にまとめ、詳細の意味を失わない。

対応する仕様: 「表示言語を個別に選択できる」「進行状態を5つの基本工程で説明する」。

### AC-002 — 英語選択と動作不変

> `en`を明示した場合は現行の表示語彙を使用でき、操作モードの選択や判定条件が変わらない。

対応する仕様: 「表示言語を個別に選択できる」英語表示シナリオ。

### AC-003 — 判定領域と値の維持

> QA総合判定、正式案件の評価勧告、基準別判定、実行チェック結果が既定では日本語、`en`指定時は既存コードで表示され、それぞれの意味と種類数が維持される。

対応する仕様: 「QA判定と正式案件の評価勧告を進行工程から分ける」。

### AC-004 — 状態・停止理由の区別

> 全既知状態と停止条件に説明があり、未検証、保留、失敗、修正提出、独立検証済み、利用者の終了判断を区別できる。

対応する仕様: 「進行状態を5つの基本工程で説明する」。

### AC-005 — 機械契約と保存状態の不変

> 表示の変更により機械JSONの既存フィールド・列挙値、保存データ、CLIの機械利用、Role制約、承認範囲、QA判定が変わらない。

対応する仕様: 「人向け表示は機械契約と保存状態を変更しない」。

### AC-006 — 正本・配布物と検証

> 正本と配布用実行コードが一致し、対象に合った検証で日本語既定、英語選択、互換性、読取り専用性を確認できる。

対応する仕様: 機械契約不変のシナリオ。配布一致は設計とタスク4.1、検証範囲はタスク4.2でも確認する。

### AC-007 — 独立QAの証拠

> 新規Changeの確定した仕様・受入基準を基準とする独立QAで、全項目の結果と証拠が記録される。

対応する仕様: Change全体。実装の合否を個別のEvidenceと共に独立QA成果物へ記録する。

### AC-008 — QA基準の事前確認と再利用

> QA開始前に基準文書・版・受入基準が利用者に確認され、基準の追加・削除・緩和には変更点への承認が記録される。再QAも同じ基準を引き継ぐ。

対応する仕様: 独立QA開始手順。実装仕様の合否とは分け、利用者確認の記録と同一基準の再利用で確認する。

### AC-009 — 状態対応と複合条件

> 全内部状態と停止条件の5工程への対応、および複合条件の優先順位が仕様で確定し、そのとおりの表示が確認できる。

対応する仕様: 「進行状態を5つの基本工程で説明する」の通常状態、正式案件状態、`reviewed`、停止、未知・複合条件シナリオ。

### AC-010 — 評価対象版とサイクル

> QA評価結果には評価対象版とサイクルが示され、結果なし・過去結果を現在版の判定と誤認させず、総合QA判定の4種類が維持される。

対応する仕様: 「評価結果の対象版とサイクルを示す」および総合QA判定シナリオ。
