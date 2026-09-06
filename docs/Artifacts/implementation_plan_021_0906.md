# Capability Parity残件2件の完了計画

created: 2026-09-06 13:54 (JST)
update: 2026-09-06 13:54 (JST)
author: Codex (GPT-5)

## 1. 目的

OpenSpec Change `spec-driven-qa-capability-parity-and-legacy-compat` に残る2件の未完了タスクを、既存の三版比較・安全境界・Evidence設計を変更せずに完了する。

## 2. 対象

- `5.1`: Candidate／compactの安全契約回帰検証を、自己クローズ、Reviewer正本書込み、未知Finding、空・欠落Evidence、Workspace外パスについて実行し、正本不変性と終了コードを記録する。
- `6.1`: Agent／RunごとのPrompt、出力、条件、時刻、実行件数、Bundle digest、結果、未実行項目の必須形式を固定し、manifestとresultsの整合性を検証する。

## 3. 実施方針

1. 作業開始時のGit差分と既存Evidenceを確認する。
2. 既存の `stage/safety_regression.py`、`stage/agent_aggregator.py`、fixture、テストを最小限修正または補強する。
3. Candidateの空Evidence受理は、修正可能なら拒否動作へ修正する。修正が仕様範囲を越える場合は、Evidence gapとして残し、タスクを完了扱いにしない。
4. Agent／Run Evidenceの必須項目、識別子、manifest/results整合性を構造化検証する。
5. キャッシュを生成せずテスト、比較スクリプト、OpenSpec検証を実行する。
6. Evidenceと実装報告を更新し、実際に確認できたタスクだけを完了へ変更する。

## 4. 安全境界

- 既存ユーザー変更、既存QA正本、外部リポジトリ、外部Skill配置先は変更しない。
- `master`へのcommit、remoteへのpush、旧版削除、OpenSpec ChangeのArchiveは行わない。
- 既存の `accepted-with-residual-risk` 裁定を上書きしない。
- Candidateの安全契約違反を、Evidenceの追記だけで合格へ昇格させない。

## 5. 完了条件

- `5.1` と `6.1` の要求項目が実行可能なテストまたは検証結果として記録される。
- 正本不変性、非ゼロ終了、版別適用可能性、Agent／Run帰属がEvidenceで追跡できる。
- 未検証または修正未完了の項目は `unverified`、`evidence-gap`、または未完了として明示される。
- OpenSpecの進捗と実装報告が一致する。
