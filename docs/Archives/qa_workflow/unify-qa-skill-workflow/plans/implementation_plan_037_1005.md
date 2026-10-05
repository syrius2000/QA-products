# QA-003 Cycle 3 Finding 対応計画

created: 2026-10-05 (JST)
update: 2026-10-05 23:35 (JST)
author: Codex (GPT-6)

## 受領した独立QA結果

QA-003 Cycle 3はGate FAIL。QA-F01とQA-F02は解消確認済み。新規Finding `QA-C3-F01`（Medium / OPEN）は、最終依頼走査が拒否された場合、製品対象commitが既に作成されている一方で、正式なReviewed SHAと最終依頼hashが状態へ保存されず、再試行時に状態と本文が不整合になる点を指摘する。レビュー原文・4成果物は[Cycle 3出力](../artifacts/qa_cycles/unify-qa-skill-workflow/c3/01_review.md)に保存されており、変更しない。

## 修復方針

対象SHAは最終依頼本文に記載されるため、製品対象だけを含むローカルtarget commitの作成と依頼最終化は最終本文走査に先行する。したがって走査が拒否した場合も、製品対象commitはローカルに存在し得る。実装と文書の停止契約をこの順序に合わせ、次を保証する。

1. 製品snapshotだけを含むtarget commitを作成し、最終依頼本文を生成する。
2. 最終依頼本文のhash、Reviewed SHA、Reviewer資材hashをcase状態へ保存する。
3. 保存後に最終公開走査を実行する。走査が拒否したら拒否stage・理由を状態へ保存し、招待commitとremote pushは行わない。
4. 拒否時点のReviewed SHA・依頼本文・状態hashを一致させる。走査拒否を「target commitも存在しない」と説明しない。
5. 入力自体に危険情報があり同じ依頼を安全に再生成できない場合、既存caseを改変しない。原因を除いた置換QA依頼を新規作成し、target SHAを再利用できる手順を案内する。

既存の「公開内容の走査前に招待commit/pushしない」境界は維持する。拒否で作成され得るのは、走査済み製品snapshotだけのローカルtarget commitである。テストで既存indexを保持し、依頼commitとremote更新がないことを確認する。

## 実施計画

| タスク | Finding | 変更内容 | 完了条件・検証 |
|---|---|---|---|
| T-01 | QA-C3-F01 | `_finalize`後、最終走査の前にReviewed SHA・最終招待hashを状態へ保存する。走査拒否を捕捉してstage、検出分類、時刻、再開案内を記録する。拒否時に招待commit/pushへ進まないことを明示する。 | secret/個人パスの最終化後fault injectionで、state.reviewed・state.invite_hash・実ファイルhash・target commitが一致し、publish errorが保存され、招待commit/remote更新がない。対象外indexは不変。 |
| T-02 | QA-C3-F01 | 最終走査の停止契約、target commitが作られる範囲、拒否後の状態と再開方法をOpenSpecと公開手順へ反映する。誤解を招く「対象commitより前に停止」を限定し、依頼commit・remote pushより前の拒否を規定する。 | spec、publish手順、実runtimeと拒否fixtureの状態遷移が一致する。過去QA Cycle 1〜3成果物は編集しない。 |
| T-03 | QA-C3-F01 | 再試行/置換依頼の案内を実装の現行能力に即して規定する。固定要件を黙って書き換えず、必要時は新しい依頼・新規stateを作り、既存target SHAを利用する。 | scan拒否後の同一依頼再試行が曖昧なhash不一致にならず、状態に保存された理由・次操作を返す。置換依頼手順で前ケースの状態・依頼を上書きしない。 |
| T-04 | QA-C3-F01 | F01/F02既存回帰に拒否後state/hash、invite commit未作成、remote不変、ユーザーindex保持、再開案内のケースを追加する。 | 個別fixtureと全quality-loop suiteが成功し、正本runtimeと配布runtimeが同期。strict OpenSpec valid。 |

## データ・provenance契約

- 走査前確定情報: `reviewed` SHA、`invite_hash`、product snapshot hash、check contract hashを永続状態へ保存する。
- 走査結果: `publication_scan`に成功/拒否の区別、拒否stage、検出分類、時刻、依頼hashを記録する。secret本文そのものや検出値は状態ログへ重複保存しない。
- 拒否時の不変条件: invite commitなし、remote tip不変、index保持。ローカルtarget commitは指定製品snapshotのみを含み、`state.reviewed`と一致する。
- 拒否履歴は次の再試行で消去せず、成功時は同一対象hashの成功scanを別イベントとして追記する。

## 検証マトリクス

| Fixture | 検査 | 期待結果 |
|---|---|---|
| 最終化時にsecret様値を注入 | final scan拒否後のHEAD/state/file hash/index/invite commit/remote | targetは製品限定で存在しstateに一致。最終本文hashもstate・fileで一致。招待commitなし、remote/index不変、拒否stage記録あり |
| 最終化時に個人絶対パスを注入 | secretケースと同じ不変条件 | 同上 |
| 拒否後に同じ依頼を再試行 | stateと安全状態/案内 | 曖昧な外部改変hashエラーでなく、保存済み拒否理由と安全な次操作を返す。invite commit/pushなし |
| 拒否後に置換依頼を作る | 新case、前case、target SHA | 新caseは前caseを上書きせず、明示指定された既存target SHAを使える。前caseは拒否履歴を保持 |
| 従来の走査後改変 | scan hash vs commit snapshot | 招待commit前に停止し、既存ユーザーindex・remote不変 |
| 成功系 | state hash、commit blob hash、remote到達可能性 | 既存契約どおり全hash一致後に限り公開 |

## 修正対象パス

```text
docs/Artifacts/implementation_plan_037_1005.md
quality-loop/qa_workflow/workflow.py
quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
quality-loop/skills/quality-qa/references/publish.md
openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md
openspec/changes/unify-qa-skill-workflow/tasks.md
quality-loop/tests/test_qa_workflow_contract.py
```

既存のCycle 3レビュー4成果物、Cycle 2記録、ユーザーの`gomi.memo.md`、implementation_report_002、既存未コミットの`tasks.md`差分は保持する。OpenSpec tasks.mdは末尾への限定追記のみとし、既存行を置換しない。

## 実装後の確認

```bash
cd quality-loop
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q
```

基盤/runtime同期検査、OpenSpec strict validation、`git diff --check`を行い、実行結果を次の独立QA依頼へ記録する。別担当によるローカル独立QAを再実施し、QA-C3-F01の判定を固定Reviewed SHAで確認する。

## 実行境界

QA Cycle 3 reviewerはOwner判断を行わず、`QA-C3-F01`を修復対象として提示した。リポジトリの`AGENTS.md`は製品コード・仕様修正前にimplementation planの明示承認を要求しているため、この計画への承認前にコード・仕様・テスト・OpenSpec tasksを変更しない。承認後も上記path集合内に限定する。新しい修正commitと独立QA依頼は実装・検証後に作成する。push、merge、既存QA記録の編集は本計画に含まない。
