# Spec-Driven QA Review

`spec-driven-qa-review` は、AI実装を別AIが独立レビューし、Purpose / Spec / Plan / Tasks / Implementation / Implementation Report / Tests / Evidence の整合性を追跡するためのSkill一式です。

## 中核思想

> Purposeを最上位に置き、Spec・Plan・Implementation・Evidenceを相互に批判可能な証拠として扱う。

このSkillは「コードを説明して理解したことにする」ためのものではありません。AI-1が実装した成果物について、AI-2が独立にQA Findingを作成し、AI-1が回答・修正し、AI-2が再検証する反復可能なQAワークフローを提供します。

## 典型フロー

```text
Purpose / Spec / Plan
        ↓
AI-1 Implementation
        ↓
AI-2 Blind-first Independent Review
        ↓
QA Findings
        ↓
AI-1 Author Response / Correction
        ↓
AI-2 Reviewer Verification
        ↓
Closure / Rework / Human Adjudication
```

## 対象範囲

- デフォルトは明示されたファイルまたはディレクトリのみ。
- 指定モジュールを優先し、リポジトリ全体は明示依頼時のみ。
- 理解に必要な関連テスト・型・Spec等は参照できますが、勝手に主対象へ広げません。

## 出力先

```text
docs/ADR/QA/QA-XXXX-short-title/
```

主要ファイル:

- `review.md`: 現在状態、QA Pulse、次の担当者とアクション
- `handoff.md`: `review.md`と`findings.yaml`から生成する次AI向け受け渡し契約
- `findings.yaml`: Findingの機械可読状態
- `traceability.yaml`: Purpose/Spec/Implementation/Evidenceの対応
- `events.jsonl`: append-only進捗ログ
- `cycles/`: 各サイクルの独立レビュー、作成者回答、再検証

新規ケースのサイクル名は`cycle-01-author-response.md`、`cycle-01-verification.md`の形式に統一します。既存の`01-*`履歴は改名せず、後方互換として扱います。

## REQUIREDバリデーション

未処理の必須項目には `REQUIRED:` を付けます。

```text
REQUIRED:AUTHOR-RESPONSE:QA-0007-F05:CYCLE-2
```

`validate_review_case.py` および `detect_unresolved_markers.py` は、残存タグや矛盾した状態を検出します。

## QA Profile

- `lite`: 低リスク変更向け
- `standard`: 通常の機能実装向け（既定）
- `strict`: 高リスク・規制・統計ロジック・データ破壊・認証等
- `proportional-home`: 家庭内LAN・非安全系・非リアルタイム・リソース制約下の観測系向け

詳細は `references/risk-profiles.md`。

Findingは、目的適合性分類（`spec-required` / `purpose-critical` / `operational-hygiene` / `out-of-scope`）と、技術判定・所有者裁定を分けて記録します。`unverified`は証拠不足、`failed`は再現した不合格を示します。`risk-accepted`は技術的修正済みを意味せず、所有者・理由・管理策・見直し条件が必要です。

## SDD Adapter

Skill自体はOpenSpec等へ固定しません。

- `adapters/openspec.md`
- `adapters/spec-kit.md`
- `adapters/generic-sdd.md`

SDD成果物の場所や命名がプロジェクトで異なる場合はAdapterの探索規則を調整します。

## Python補助スクリプト

ランタイム依存はPython標準ライブラリのみです。

```bash
python scripts/create_review_case.py --root . --title "patient normalization" --target src/normalization --profile standard
python scripts/detect_unresolved_markers.py docs/ADR/QA
python scripts/validate_review_case.py docs/ADR/QA/QA-0001-patient-normalization
python scripts/render_handoff.py docs/ADR/QA/QA-0001-patient-normalization --check
```

pytestを使うテストは開発用です。

開発用のPyYAMLは`pip install -e '.[dev]'`等で導入できますが、実行時スクリプトはPyYAMLなしで動作します。

## pre-commit / CI

`integrations/` に例があります。ローカルpre-commitは即時フィードバック用であり、`--no-verify` で回避できます。強制する場合はCI/branch protection側でも検証してください。

## 重要な限界

- 2つのAIの合意は正しさを保証しません。
- Spec自体が誤っている可能性があります。
- AI間レビューは人間の規制上の承認や安全責任を代替しません。
- AI-2はAI-1の説明を先に読まず、可能な限りblind-firstで評価します。
