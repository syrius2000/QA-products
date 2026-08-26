## Why

QA-0004（Reviewer lifecycle）は技術 High ギャップを解消したうえで `conditionally-accepted` となったが、Acceptance Conditions **C2/C3** として、handoff の stale digest 拒否と verify 時の Evidence パス実在／`modified_files` 扱いが未充足のまま残っている。Author Change・完全互換検証に進む前に、偽陽性の `fixed-and-verified` と「handoff 完全性の過大主張」を機械的に防ぐ必要がある。

## What Changes

- Reviewer `verify_submission` を強化し、`test_evidence` がリポジトリ相対パスを指す場合は実在を必須とする（非パス文字列は従来どおり非空検査、または明示ポリシーで区別する）
- Author 提出の `modified_files` を、handoff／契約が要求する範囲では存在確認の対象とする（任意のまま放置しない）
- handoff の **stale digest**（正本再計算と不一致）入力を拒否する自動テストと、必要なら runtime 拒否経路を追加する
- capability／tasks／Evidence の表記を実測に合わせ、未達を完了扱いにしない
- Schema・digest・revision の共有契約自体は変更しない（計算結果の検証を厳格化する）
- 外部 Skill 配備・旧版削除・commit／push は行わない

## Capabilities

### New Capabilities
- `reviewer-verification-integrity`: Reviewer による Author 提出検証と handoff digest 鮮度の厳密化（stale digest 拒否、Evidence パス実在、`modified_files` 存在確認、対応する negative／golden テスト）

### Modified Capabilities
- `spec-driven-qa`: 公開 handoff の digest 不一致時拒否と、Evidence 参照の実在／非成功扱い（`unverified` / `evidence-gap`）を、Reviewer verify 経路でも MUST として明示・補強する

## Impact

- 主対象: `openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/spec-driven-qa-review/lifecycle.py`（または本 Change の stage への取り込み後の同相当）と関連 pytest
- 共有コア: digest 再計算・Validator 呼び出しの再利用のみ。契約 Schema の破壊的変更はしない
- 依存: QA-0004 条件 C2/C3 の消化。Author Change（`spec-driven-qa-author-response-submission`）着手前の前提強化
- 非対象: Contract v1.2 の tokens/latency 評価（C4）、外部配備（C5）、共有基盤 Schema 改訂
