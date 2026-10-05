# 独立QAレビュー

created: 2026-10-04 12:17 (JST)
update: 2026-10-04 12:17 (JST)
author: ChatGPT (GPT-5.6 Sol)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-001
- リポジトリ: syrius2000/QA-products
- 開発ブランチ: codex/qa-skill-integration-cloud-qa
- 初回基準SHA: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
- 差分基準SHA: 3b502f2168028831bf43d6cb1a27cf9f4d04797f
- 対象SHA: 7d8880b2558cfabcc517b95b10b87b5ccebae03a
- サイクル: 1
- 要件指紋: a85bad11b55caa0140297df2be9cee37d0fc99ed299912684dc27855437f7d0c
- 担当: ChatGPT / 独立QA
- 実行経路: クラウド
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_001_1004.md
- 結論: FAIL
- 必須確認: 未完了

## 確認範囲

固定対象 `7d8880b2558cfabcc517b95b10b87b5ccebae03a` を GitHub から直接読み、差分基準 `3b502f2168028831bf43d6cb1a27cf9f4d04797f` との差分を確認した。対象版は基準より1 commit aheadで、変更57ファイルを列挙し、依頼に明示された製品対象との対応を確認した。重点確認は通常QAの正本 `openspec/specs/unified-qa-workflow/spec.md`、要求正本 `quality-loop/REQUIREMENTS.md`、`quality-loop/qa_workflow/` の状態遷移・Git公開・レビュー検査、`quality-loop/tests/`、`quality-loop/skills/quality-qa/`、配布スクリプトと配置ガイド、正式Quality Loop用3仕様との適用範囲境界である。

通常QAの正本SpecとChange内Specは、タイトル・日時・`## Requirements` / `## ADDED Requirements` の差を正規化した本文が一致した。正式Quality Loop用 `spec-driven-qa`、`reviewer-verification-integrity`、`proportional-qa-gates` は通常QAとの適用範囲を明示しており、`openspec/specs/README.md` の正本索引とも整合している。

開発用 `quality-loop/qa_workflow/` と配布用 `quality-loop/skills/quality-qa/runtime/qa_workflow/` の8モジュール（`__init__.py`, `cli.py`, `github.py`, `gitops.py`, `legacy.py`, `review.py`, `store.py`, `workflow.py`）は対象SHAでそれぞれGit blob SHAが一致した。

## 実施した検証

- GitHub上で基準SHA→対象SHAを比較し、1 commit・57変更ファイルであること、改名として報告されたパスがないことを確認した。
- 正本SpecとChange内Specの本文を正規化比較し、一致を確認した。
- `qa_workflow` 開発正本と `quality-qa` 同梱runtimeの8モジュールをblob SHAで比較し、全件一致を確認した。
- レビュー契約の生成・解析・検査、修正承認、修正提出、再QA、公開前flight、関連テストを静的に照合した。
- 実行環境には Python 3.13.5 と pytest 9.0.2 が存在することを確認した。対象リポジトリのcheckoutを取得して必須pytestを実行しようとしたが、実行環境から `github.com` の名前解決ができず対象版を取得できなかった。

## 未検証事項

- 必須確認 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quality-loop pytest quality-loop/tests` は対象SHAのcheckoutを取得できなかったため未実施。pytest自体は利用可能だが、固定対象のファイル群をローカル実行環境へ取得できていないため、既存のテスト記録を今回の実行成功として代用しない。
- Python 3.10実ランタイムでの実行、および `quality-qa` を入口にした実クラウドQAのend-to-end動作は今回実施していない。対象文書がこれらを未検証として扱っていることは確認した。

## 指摘

### 指摘 QA-F01
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: 「クラウドレビューは一つのMarkdownで提出する」の全基準記載、および「結果の整合確認と原文保持」の依頼との全基準一致検査
- 根拠: quality-loop/qa_workflow/review.py:8 `LABELS` は要件指紋を持つが受入基準自体の項目を持たず、同:83-86 の整合検査も `requirements_hash` だけを比較し、同:114-124 のレビューTemplateにも全受入基準を出力しない。正本Specは openspec/specs/unified-qa-workflow/spec.md:95 と同:127 でレビューへの全基準記載と全基準一致検査をMUSTとしている。
- 影響: レビュー担当は依頼の要件指紋をコピーするだけで構造検査を通過でき、レビュー本文にどの受入基準を実際に確認したかが残らない。基準の欠落・改変・部分レビューをレビュー成果物単体から検出できず、自己完結したクラウド成果物と後続の訂正確認の監査性が正本Specを満たさない。
- 対応案: レビュー契約に受入基準の完全な列挙を追加し、Templateへ固定順序で出力する。parser/checkではレビューに記載された基準集合または順序付き列を `state["criteria"]` と照合し、欠落・追加・改変を不一致として扱う。要件指紋は補助的な同一性確認として残す。
- 対象: quality-loop/qa_workflow/review.py
- 完了条件: 生成レビューに初回依頼の全受入基準が明示され、1件でも欠落・改変・追加されたレビューは構造／整合検査で無効となり、完全一致したレビューだけが内容確認へ進める。
- 検証方法: `test_qa_workflow.py` に複数基準のfixtureを追加し、全基準一致はvalid、1基準欠落・文言改変・余分な基準追加はinvalidとなることを確認する。

### 指摘 QA-F02
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: 「承認範囲内のローカル修正」と「再QAで元要求と指摘を保持する」の、承認範囲の修正だけを再QA対象へ固定する条件
- 根拠: quality-loop/qa_workflow/workflow.py:111-112 は明示 `reviewed` の再QAで前回 `submission["paths"]` だけをsnapshot照合し、同:124-130 は未commit再QAで全製品の現在snapshotを新下書きへ取り込み、同:393-397 の `requa` は旧製品集合全体をそのまま次サイクルへ渡す。test_qa_workflow.py:222-235 の再QAテストは製品が1ファイルだけで、修正提出後に別の既存製品パスが変更されるケースを覆っていない。正本Specは openspec/specs/unified-qa-workflow/spec.md:165-173 と同:181-183 で未承認の範囲拡大を再承認へ戻し、承認範囲の修正完了後に再QA対象を固定することを要求している。
- 影響: 複数製品を対象とする案件で、`submit` 完了後から `requa` / 対象確定までの間に計画対象外の製品ファイルが変更されても、その変更を新しい再QA下書きのsnapshotへ取り込める。後続の対象commit承認は「commitする対象」の承認であって元修正計画の再承認ではないため、計画外の製品変更が再QA対象へ混入し、承認境界を迂回できる。
- 対応案: 再QA作成時に前回承認時点・修正提出時点からの製品差分を再検査し、前回 `submission["paths"]` と登録済み運用成果物以外の製品変更があれば新サイクルを作らず、計画更新・再承認へ戻す。明示 `reviewed` の場合もsubmission pathsだけでなく、前回対象から指定commitまでの製品差分全体が承認済み修正範囲内か検査する。
- 対象: quality-loop/qa_workflow/workflow.py
- 完了条件: 修正提出後に未承認の製品パスを変更した状態では、未commit再QA・ユーザー作成commitを指定した再QAの双方が停止し、計画更新と再承認を要求する。承認済み提出だけの再QAは従来どおり進める。
- 検証方法: 2製品ファイルのfixtureで片方だけを計画・承認・submitし、その後もう片方を (a) 未commit変更、(b) commit済み変更してから再QAを作成するテストを追加し、双方が拒否されることを確認する。承認対象だけの変更では再QA作成・対象確定が成功することも確認する。

## 前回指摘の再確認

- 対象: なし

## 残余事項

対象版の仕様境界、正本Spec同期、配布runtime同一性には上記以外の矛盾を確認していない。ただし必須pytestが今回未実施であり、実行でのみ判明する回帰の有無は未検証である。QA-F01・QA-F02はいずれも正本SpecのMUSTに対する未達であるため、必須確認未完了と合わせて現版をPASSとはしない。修正後は両指摘の拒否系テストを追加し、固定SHAで必須pytestを実行したうえで再QAする。
