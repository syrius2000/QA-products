---
case_id: QA-0002
cycle: 1
action: author-response
performed_by:
  agent_id: "codex-implementer"
  role: implementer
  tool: "Codex (GPT-5)"
completed_at: "2026-08-26T00:52:08+09:00"
base_revision: "working-tree"
result_revision: "working-tree"
disposition_summary:
  QA-0002-F01: fix-submitted
  QA-0002-F02: fix-submitted
  QA-0002-F03: fix-submitted
---

# Author Response — Cycle 1

## 概要

QA-0002の公開`handoff.md`、`review.md`、`findings.yaml`、`traceability.yaml`、`events.jsonl`、Cycle 1独立レビューを確認した。対象は`compact-spec-driven-qa-skills`の設計段階であり、実装コード、実配備、比較ハーネス実行はまだ存在しない。そのため、3件すべてを設計・タスク修正の`fix-submitted`として提出する。`fixed-and-verified`、`closed`、QAケース終端の`accepted`への変更は行わない。

## Finding Responses

### QA-0002-F01

共有コアのインポート解決境界

Disposition: fix-submitted

- **指摘への回答**: 指摘を受け入れた。Bundleを論理的に構成するだけでは、`~/.gemini/config/skills/`や`~/.agents/skills/`のようなSkill単位の実行環境で共有コアを安全に解決できることが保証されない。
- **提出した修正**:
  1. `design.md`の配布単位に、Launcherが自身の実ファイル位置からBundleルートを決定する方式を追記した。
  2. Launcherは`shared_core/`の存在、Manifest、共有コアの内容digestを検証してから、検証済みBundleルートだけを限定的にimport解決対象へ追加する。
  3. `PYTHONPATH`、cwd、環境変数、未検証シンボリックリンクには依存せず、配置またはdigest不一致時はfail-closedとする。
  4. `tasks.md`へstandalone配置negative testを追加し、共有コア不足、digest不一致、cwd変更、未検証リンクを拒否対象とした。
- **Evidence**:
  - `openspec/changes/compact-spec-driven-qa-skills/design.md:45`
  - `openspec/changes/compact-spec-driven-qa-skills/tasks.md:23`
- **未実施**: Launcher実装、実際のstandalone配置、ImportErrorが発生しないことの実行確認。
- **次の担当**: Reviewerが設計反映を確認し、実装後にstandalone配置negative testを検証する。

### QA-0002-F02

3版比較ハーネスの正本判定基準

Disposition: fix-submitted

- **指摘への回答**: 指摘を受け入れた。未検証のContract v1.2候補版の挙動を期待値にすると、候補版の不具合を圧縮版の正しさと誤認する可能性がある。
- **提出した修正**:
  1. 判定正本を当該OpenSpec Changeの`spec.md`と明記した。
  2. Bundle内の`SPEC.md`は、`spec.md`から生成され、digest固定された場合のみ派生仕様として扱う。
  3. `design.md`、`tasks.md`、旧版挙動、未検証Contract v1.2候補版の挙動は、正本を上書きしない。
  4. 仕様違反、旧版互換差分、診断文差分を別々に記録するよう比較タスクを更新した。
- **Evidence**:
  - `openspec/changes/compact-spec-driven-qa-skills/design.md:69`
  - `openspec/changes/compact-spec-driven-qa-skills/tasks.md:15`
  - `openspec/changes/compact-spec-driven-qa-skills/tasks.md:51`
- **未実施**: 比較ハーネス、SPEC.md生成・digest固定、3版fixtureの実行。
- **次の担当**: Reviewerが正本優先順位を検証し、実装後に候補版が正本を上書きしないことを確認する。

### QA-0002-F03

決定論的サイズ計測スクリプト

Disposition: fix-submitted

- **指摘への回答**: 指摘を受け入れた。行数目標は集計条件が曖昧なままでは再現できないため、Phase 0の成果物として計測スクリプトを明示する。
- **提出した修正**:
  1. `design.md`の移行計画へ、標準ライブラリのみの`measure_size.py`作成を追加した。
  2. `tasks.md`のTask 1.5へ、Manifest対象、空行、コメント、テスト、サンプル、Schemaの含否を決定論的に扱い、行数・バイト数・常駐対象をJSON出力する要件を追加した。
- **Evidence**:
  - `openspec/changes/compact-spec-driven-qa-skills/design.md:103`
  - `openspec/changes/compact-spec-driven-qa-skills/tasks.md:7`
- **未実施**: `measure_size.py`の実装、実行、出力値の保存。
- **次の担当**: Reviewerがタスク反映を確認し、実装後に同一Manifestから同一結果が得られることを検証する。

## 実行テストと残余リスク

- **今回実施**: 指定QAケースと公開handoffの読み取り、設計・タスクの修正、Author Response、`findings.yaml`・`review.md`・`events.jsonl`の更新。
- **今回未実施**: 実装コード、pytest、比較ハーネス、Launcher、`measure_size.py`、Bundle Validator、standalone配置、実配備、rollback。
- **残余リスク**: 設計記述だけではF01のimport解決、F02の裁定実装、F03の計測再現性を証明できない。
- **QA状態**: `author-response-submitted`。F01〜F03はReviewer verification待ちであり、`fixed-and-verified`や`closed`には変更していない。

独立Reviewer（AI-2）へCycle 1の再検証を依頼する。
