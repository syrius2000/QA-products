---
case_id: QA-0008
status: closed
case_revision: 2
next_action: deployment-dry-run-change
terminal_result: accepted-with-residual-risk
contract_version: qa-review-case-v1
---

# QA-0008 人間裁定用Handoff

## 対象

`openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/` の三版比較、互換性分類、安全回帰、複数Agent Evidence集計、サイズ計測および総合判定。

## 人間が判断した事項

1. QA-0008-F01について、Candidateが空Evidenceを受理する観測違反を修正するか、明示的な意図的非互換として裁定するか。
2. QA-0008-F02はCandidateのsemantic digest回帰を確認済み。content digest／versionをcompact固有契約として扱うことを確認する。
3. QA-0008-F03/F04はReviewer検証済み。Agent項目別欠測表示とSource Manifest方式を採用することを確認する。
4. QA-0008-F05はCycle 4でReviewer検証済み。5.1は未完了、5.2は完了とする現在のtasks表示を確認する。
5. compactの1,760行目安内（実測878行）を、F01のCandidate契約違反と動的未検証を残した状態で採用候補とみなすか。

## 人間裁定（Cycle 5）

- 裁定者: `human-owner`
- 選択: **A 条件付き受入**
- 結果: `closed / accepted-with-residual-risk`
- F01: 技術状態は`failed`のまま、OwnerのDispositionを`risk-accepted`とする
- compact: 採用候補として扱うことを許可する。ただしcompactの`empty-or-missing-evidence`は`not-applicable`であり、安全契約の合格証拠ではない
- 配備: 許可しない。別の配備Changeでbackup、dry-run、配置後検証、rollbackを行い、別途明示承認を得る

## 裁定選択表

| 選択肢 | 判断内容 | compactへの影響 | 次のChange |
|---|---|---|---|
| A 条件付き受入 | F01をアーカイブ済みCandidateの意図的非互換または残余リスクとして受け入れる | compactのObservedな安全境界と878行のサイズを採用候補として扱える。ただしLegacy完全互換とは宣言しない | 配備dry-run Change。ただし未検証項目とF01を条件として明記 |
| B 厳格互換 | Candidateの空Evidence受理を修正し、QA-0008-F01を再検証する | Candidate／compact比較の安全契約差分をさらに縮小できる | Candidate修正・再検証Change |
| C 保留 | F01またはAgent／Run欠測を受入条件として認めない | compactの配備・採用判断を停止する | 追加Evidence取得または修正Change |

### 判断時の注意

- AはCandidateの不備をcompactの安全性として合格扱いすることではない。F01は`observed-violation`として残す。
- compactの`empty-or-missing-evidence`は現在の連鎖API契約では`not-applicable`であり、安全契約を満たした証拠ではない。
- Aを選ぶ場合でも、Token・Latency・外部LLM正答率は`unverified`、Agent／Run必須項目の欠測は残余リスクとして保持する。
- いずれの選択肢でも、別の配備Changeと明示承認が完了するまで外部Skill配置、Legacy削除、commit、pushは行わない。

## 確認済み事項

- 自動テスト49件は成功（Candidate digest ProbeとSource Manifest関連の検証を含む）。
- Bundle境界、digest、秘密値防御、compactの自己クローズ拒否はObserved。
- Legacyは改造していない。
- Legacyの後発submission・digest・revision不在は`intentional-noncompatibility`として記録し、完全互換合格へ集約していない。
- Token・Latency・外部LLM正答率は`unverified`であり、推定値は使用していない。
- F02〜F05（Candidate digest適用範囲、Agent項目別欠測判定、Source Manifest再現性、tasks表示整合）はReviewer検証済みで`fixed-and-verified`。
- F01はCandidate専用Probeで`expected=reject`、`actual=accept`を観測した。技術的には`failed`、Owner裁定は`risk-accepted`である。
- 未解決Findingは0件である。F01は修正済みではなく、残余リスクとして受け入れた。F02〜F05はReviewer検証済みである。
- Cycle 4の独立検証後、Cycle 5で人間裁定を完了した。

## 配備境界

外部Skillディレクトリへの配置、Legacy削除、commit、pushは未実施である。条件付き受入後も、本Changeだけでは配備を許可せず、別の配備Changeと明示承認を必要とする。

## 必須マーカー
