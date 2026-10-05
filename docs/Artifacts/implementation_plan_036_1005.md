# QA-003 Cycle 2 HOLD 解消計画

created: 2026-10-05  (JST)
update: 2026-10-05  (JST)
author: Codex (GPT-6)

## 受領したQA結果

QA-003 Cycle 2 のGate HOLDとQA-F01・QA-F02を未解決として受領する。Cycle 2報告は[qa_review_003_cycle2_local_1005.md](qa_review_003_cycle2_local_1005.md)に保存済みであり、原文と判定は変更しない。Cycle 2のReviewer契約hash不一致（依頼値とReviewed SHA上の実hashの不一致）もprovenance上のHOLD理由として維持する。修正後に新しいQA依頼を生成するとき、依頼対象commitのQA Skill・Reviewer契約からhashを再取得して依頼へ固定する。

## 実施計画

| タスク | Finding | 方針・変更内容 | 完了条件・確認方法 |
|---|---|---|---|
| T-01 | QA-F01 | `publish`の検査順序を改める。対象製品のsnapshot・必須check Evidence・公開前提を確認し、未確定なら対象を確定して依頼本文を最終生成した後、実際にcommitする製品対象と依頼本文の最終バイト列を再走査する。最終依頼本文のSHA-256を公開状態/Evidenceへ記録し、依頼commitに含まれたblobのhashと照合してからpushを許可する。検査後に本文が変わった場合はcommit/push前に停止する。 | `reviewed`未確定でfinalizeが依頼を更新する経路、既確定経路、検査後改変、危険内容をfixtureで確認する。拒否時にHEAD・index・remote tipが不変。成功時は走査hash＝state記録hash＝招待commit内blob hashである。 |
| T-02 | QA-F02 | 再QA時、旧契約の全必須checkについてIDの保持、`required=true`、実行仕様（type/argv/cwd/env/timeout/expected exit/Python minimum等）の非弱化を構造的に検査する。承認文の語句一致だけでは契約変更を通さない。変更承認は旧・新契約のhash、差分、承認文を状態へ結び付ける。必須checkの削除・任意化・実行条件の弱化を承認文だけで許可しない。非必須checkの追加等、非弱化変更の承認条件を明示する。 | 旧必須checkの全削除、ID置換、required=false、argv/cwd/env/timeout/期待終了値/Python最低版の弱化を、承認文の有無にかかわらず拒否する。同一契約継承と非弱化の追加を確認し、承認記録に両hashと差分が残る。 |
| T-03 | HOLD provenance | Cycle 2成果物は訂正せず、修正後対象で次のQA cycleを作成する際に、Reviewer SkillとReviewer契約の実ファイルhashが対象commitのtree内容と一致することを確認する。依頼本文のhashも最終生成内容に固定する。 | 新規依頼の各参照hashを対象SHAから独立計算し、依頼本文記載値・state値・対象tree値の三者一致を確認する。不一致なら公開を停止する。 |
| T-04 | 回帰検証 | 基盤実装と配布runtimeの同期を保ち、QA-F01/F02の正常系・拒否系を既存契約テストへ追加する。 | 指定pytest suite、runtime同期検査、OpenSpec strict validationを実行し、実行結果と対象SHAを実装報告に記録する。 |

## データ・provenance契約

- 最終依頼本文: UTF-8の公開対象バイト列とSHA-256。
- 公開走査Evidence: 製品snapshot hash、最終依頼hash、check contract hash、走査結果、時刻。走査後にいずれかが変われば無効。
- 招待commit: commit tree内の依頼ファイルblob hashを公開走査Evidenceの依頼hashと一致させる。
- check契約変更: 旧契約hash、新契約hash、構造化差分、明示承認文を記録。承認文の語句だけによる許可は禁止。
- 既存JSON状態との互換性を保ち、過去のCycle 2記録は書き換えない。

## 検証マトリクス

| 対象 | Fixture | Check | 期待結果 |
|---|---|---|---|
| F01 | cloud publish、対象未確定、最終化で依頼が更新される | 最終依頼本文と公開走査対象を照合 | 走査hashとcommit blob hash一致で公開可能 |
| F01 | 最終依頼本文へsecret様文字列/個人絶対パスを含める | 最終化後の走査 | 公開拒否、HEAD/index/remote不変 |
| F01 | 走査後からcommit前に依頼本文を改変 | hash再照合 | 公開拒否、remote不変 |
| F01 | 既確定依頼、製品snapshot固定 | 既存の必須Evidenceと最終依頼hashを照合 | 合格時のみ公開し、記録・commit hash一致 |
| F02 | 旧必須checkを空配列にする/IDを削除・置換 | 承認文なし/ありの両方 | 拒否 |
| F02 | required=false、argv変更、cwd緩和、timeout延長、expected exit拡大、Python最低版引下げ | 承認文あり | 必須check弱化として拒否 |
| F02 | 必須checkを完全保持し任意checkを追加 | hash結合された変更承認 | 新契約を記録して再QA作成 |
| F02 | check契約を変更し、旧新hash/差分と結合しない承認文のみ提示 | parser/contract guard | 拒否 |
| Sync | 基盤と配布runtime | 同期検査 | 差分なし |

## 修正対象パス

```text
docs/Artifacts/implementation_plan_036_1005.md
quality-loop/qa_workflow/workflow.py
quality-loop/qa_workflow/gitops.py
quality-loop/qa_workflow/store.py
quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
quality-loop/skills/quality-qa/runtime/qa_workflow/gitops.py
quality-loop/skills/quality-qa/runtime/qa_workflow/store.py
quality-loop/tests/test_qa_workflow_contract.py
quality-loop/tests/test_sync_productivity_skills.py
quality-loop/skills/quality-qa/references/publish.md
quality-loop/skills/quality-qa/references/reviewer_contract.md
openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md
openspec/changes/unify-qa-skill-workflow/tasks.md
```

`git diff`で計画承認後の変更が上記path集合内に限定されていることを確認する。Cycle 2のレビュー成果物、既存のユーザー変更、未追跡メモは変更対象外。

## 実装後の確認コマンド

```bash
cd quality-loop
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q
```

加えて`openspec validate unify-qa-skill-workflow --strict --json`、基盤/runtime同期テスト、対象差分と作業treeの確認を行う。commit・push・外部QA依頼はこの計画の範囲に含めない。

## 実行境界

この文書の作成は実装承認ではない。QA-productsの`AGENTS.md`が製品コード・仕様の修正に計画の明示承認を要求しているため、計画のpath集合と内容に対する承認を受けるまでコード、テスト、OpenSpec成果物を変更しない。Cycle 2のHOLD/Findingを変更・削除せず、修正後の独立QAは別途明示依頼を受けてから実施する。commit・push・mergeは別の明示指示が必要。
