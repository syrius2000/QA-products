# QA-0006 人間裁定記録（Cycle 4）

- case_id: `QA-0006`
- cycle: 4
- 裁定者: `human-owner`
- 裁定日時: `2026-08-26 23:44 JST`
- 裁定結果: `accepted-with-residual-risk`
- 対象Finding: `QA-0006-F06`

## 裁定

QA-0006-F06は、共有基盤Change `separate-semantic-content-digests`で技術的に解消された。QA-0007の独立QAにおいて、semantic/content digestの分離、本文改変検知、旧同値digest拒否、秘密値防御、未知version拒否、および67件の回帰テスト合格が確認されている。

したがって、F06の技術状態を`fixed-and-verified`として記録し、QA-0006全体を`closed / accepted-with-residual-risk`とする。

## 残余リスクと管理策

- Git未初期化のため、実装revisionは`unverified-no-git`である。
- 外部Skill配置、旧版削除、commit、pushは未実施である。
- 本番配置は別Changeでbackup、dry-run、配置後検証、rollbackを完了してから行う。
- digest契約変更、外部配置、またはGit管理導入時に再評価する。

## 参照Evidence

- `../QA-0007-separate-semantic-content-digests/review.md`
- `../QA-0007-separate-semantic-content-digests/evidence/pytest-results.txt`
- `../QA-0007-separate-semantic-content-digests/evidence/probe-verification.txt`
