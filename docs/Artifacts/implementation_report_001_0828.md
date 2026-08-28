# 人間中心の最小QMS協働ループ 初期実装報告

created: 2026-08-28 05:27 (JST)
update: 2026-08-28 18:18 (JST)
author: Codex (GPT-5)

## 実装結果

正本計画[implementation_plan_011_0827.md](implementation_plan_011_0827.md)に基づき、`quality-loop/`へ人間中心の最小QMS協働ループ初期版を実装した。

- 単一正本`case.json`、原子的更新、直前revisionバックアップ、revision競合拒否
- 6操作: `create-case`、`review`、`submit-response`、`verify`、`adjudicate`、`status`
- Reviewer、Implementer、OwnerのRole境界、handoff、Invocation ID、再送idempotency
- Finding、Evidence SHA-256、変更範囲の三者照合、申告外変更の拒否
- 3サイクル停止、Ownerによる追加サイクル許可、保留からの再開、終端裁定のdry-runと明示確認
- 2つのSkill: `quality-review`、`quality-response`

既存OpenSpec成果、Legacy Skill、shared coreを新実装へimport、複製、転記していない。

## 検証結果

次を実行し、成功した。

```text
cd quality-loop
python3 -B -m unittest discover -s tests -v
```

- 33 tests passed
- 正常な4段階ループ、Evidence gap、改善提案、反論、回帰Finding、リスク付き受入を確認
- Role外操作、Owner識別子の偽装、自己クローズ、古いrevision、誤handoff、未知Finding、Evidence欠落・改ざん、申告外変更、保存失敗を安全に拒否することを確認
- Skill本文とeval JSONの契約を回帰テストした
- JSON Schema、テンプレート、eval JSONの構文を確認した
- `git diff --check`、キャッシュ・bytecode残存なしを確認した

### 低リスク実案件の試行状況

`quality-loop/README.md`を対象に、案件`QMS-README-0001`を開始した。初回レビューで「READMEだけでは`create-case`の最小入力を準備できない」ことを`evidence-gap`として記録し、Implementerの無変更回答、別InvocationのReviewer検証まで実行した。

試行中、実装許可なしの`cannot-verify`がAI間を繰り返す遷移を検出したため、Reviewer検証後に直ちにOwner裁定へ移すよう修正し、回帰テストを追加した。Ownerは`F-README-001`と`quality-loop/README.md`だけへの修正を許可し、READMEへ最小入力項目、`templates/intake.json`への導線、`create-case`実行例を追加した。別InvocationのReviewer検証は`verified`で完了し、変更範囲はOwner許可と一致した。Ownerのdry-runと`confirm: true`による裁定後、案件はrevision 10で`accepted`、未解決Finding 0件となった。

## 独立QAと是正

独立・読み取り専用QAは、実案件記録の整合性を確認した一方、製品実装にHigh 1件、Medium 3件、Low 1件を検出した。詳細は[独立QA報告](independent_qa_report_001_0828.md)に記録している。計画11の範囲内の実装漏れとして、次を是正し、回帰テストを追加した。

- 登録済みOwner識別子と`actor_id`を照合し、Owner偽装を拒否
- baseline変更後の`requires-rereview`をReviewerが記録・完了できる経路を追加
- FindingとVerificationへEvidence参照、または未検証理由と必要Evidenceを要求
- `accepted-with-risk`へ条件と再確認トリガーを要求
- 存在しないcase-rootへの`status`がディレクトリを作らないよう修正

Skillの安全停止評価は[skill_behavior_evaluation.md](../../quality-loop/evals/skill_behavior_evaluation.md)に記録した。実案件の入力を与えない評価では、Evidenceを捏造せずRole外操作を避ける挙動を確認した。

## 未実施と制約

- Ownerによる初期版の受入、保留、却下、追加修正の裁定
- 本番Skill環境への配備、既存資産の削除、Commit、Push

外部Skill検証ツールは、この環境で`PyYAML`が不足しているため起動できなかった。製品本体には外部依存を追加しておらず、Skill本文とeval JSONは標準ライブラリの回帰テストで検証している。

## 次の安全な行動

別Reviewerによる是正後の読み取り専用再確認は完了し、5件すべて`fixed-and-verified`、新規Finding 0件となった。33件の自動テストとこの結果を根拠に、Ownerは初期版を受入れた。裁定の対象と境界は[初期版Owner受入裁定](initial_release_adjudication_001_0828.md)に記録した。
