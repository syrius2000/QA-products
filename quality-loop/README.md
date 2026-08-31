# Quality Loop

人間Owner、Reviewer、Implementerが、FindingとEvidenceを使って改善を前進させる最小QMS協働ループです。

## 公開操作

1. `create-case` (Owner): 案件初期化とQuality Intent設定
2. `review` (Reviewer): 初回QAレビュー・Proportionality評価
3. `submit-plan` (Implementer): Response Planの提出 (Plan Before Fix)
4. `review-plan` (Reviewer): Response Planの評価・合意・自己訂正
5. `submit-response` (Implementer): 許可範囲内での修正提出・Evidence添付
6. `verify` (Reviewer): 独立検証・申告外変更の検出
7. `assess-risk` (Reviewer): 最終リスク評価 (Final Risk Assessment)
8. `adjudicate` (Owner): 最終裁定 (Go/No-Go/条件付き受入)
9. `status` (All): 決定論的信号機要約 (`resume.md`)・最新Handoffの取得

詳細な契約は[機能仕様](FUNCTIONAL_SPEC.md)を参照してください。

## 入力Templateと実例

`templates/`には9操作の入力雛形があります。`intake.json`、`review_input.json`、`submit_plan.json`、`review_plan.json`、`response_input.json`、`verify_input.json`、`assess_risk.json`、`adjudicate_input.json`、`status.json`を使用し、`REPLACE_WITH_CURRENT_HANDOFF_ID`、revision、Actor、Evidence参照は必ず`status`の最新結果に置き換えます。

`examples/`には、標準サイクル、Evidence反証、回帰検出、残余リスク付き受入の4ケースを収録しています。例示の`case.json`は参照用であり、実案件の正本へコピーして直接編集しません。

## 変更観測

有限manifestはOwnerが明示したroot配下の相対パスだけを対象にSHA-256を記録します。Git観測は`base_ref`を明示した読取り専用操作として実行し、ignored、submodule内部、外部サービスは変更なしと推測しません。

```python
from pathlib import Path
from quality_loop import build_file_manifest, observe_git_changes

manifest = build_file_manifest(Path("../target"), ["artifact/example.txt"])
git_observation = observe_git_changes(Path("../target"), "HEAD")
```

manifest対象がroot外、存在しない、または読取り不能な場合は安全側へ停止します。`resume.md`と`final-risk-assessment.md`はcanonicalな`case.json`から生成される派生表示です。

## 開発時の実行

```bash
cd quality-loop
python3 -B -m unittest discover -s tests -v
python3 -B -m quality_loop.cli --help
```

Python標準ライブラリだけを使用します。外部ライブラリへの依存はありません。

## AI Skill

- `skills/quality-review/`: 初回レビュー、Plan合意、独立検証、最終リスク評価
- `skills/quality-response/`: Response Plan提出、修正提出とEvidence添付

どちらも最初に`status`を確認し、CLIが返した次Roleとhandoffを次工程へ渡します。Skillは案件正本`case.json`を直接編集しません。
