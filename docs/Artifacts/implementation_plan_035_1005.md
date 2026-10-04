# QA-003指摘対応・再検証計画

created: 2026-10-05 05:08 (JST)
update: 2026-10-05 05:08 (JST)
author: Codex (GPT-6)

## 受領したQA結果

QA-003 Cycle 1 の独立レビューをFAILとして正式に受領する。QA-F01〜QA-F05を改修対象とし、QA-F06は追試対象とする。独立QAの本文は[qa_review_003_1004.md](qa_review_003_1004.md)、評価・整合報告は[qa_review_evaluation_001_1005.md](qa_review_evaluation_001_1005.md)を参照する。

QA-003のReviewed SHAは`d9bad5c125791306e38bca8830b4082f7f38fc6b`。QA結果の取込時、必須pytestがERRORである場合のINCONCLUSIVE要求と、受入基準FAIL時のFAIL要求が衝突し、状態は`invalid`になった。これはQA-F03の対象として修正し、原レビューのFAILと6件のFindingを変更・削除しない。

## 実施計画

| タスク | Finding | 方針・変更内容 | 完了条件・確認方法 |
|---|---|---|---|
| T-01 | QA-F01 | `publish`の直前に、公開対象snapshotと招待文を対象とした機密・個人ローカルパス検査、および全必須checkの成功Evidenceを照合する。検査Evidenceを対象hashへ結び付け、検査後の内容変化、未実施・失敗、対象不一致ではcommit/push前に停止する。合成fixtureは実秘密と区別できる明示規則を設ける。 | 未検査、必須checkのFAIL/NOT_RUN/ERROR、検査後の改変、機密・個人パスの合成fixtureを一時bare remoteで実行し、全拒否時にHEAD・index・remoteが不変である。許可された安全な対象のみ成功する。 |
| T-02 | QA-F01 | `quality-qa`の公開手順へ検査対象、実行順、停止条件、Evidence、合成テストfixtureの例外規則を記載し、runtimeの公開条件と一致させる。 | Skillの説明とruntime条件が一致し、公開前確認手順が再現可能である。 |
| T-03 | QA-F02 | 再QAでは既存必須checkのID・必須性・argv・cwd・env・timeout・期待終了値・最低Python版を保持する。単なる再QA入力による削除・任意化・弱体化を拒否し、契約変更は新しい明示承認を要する経路へ分離する。 | `checks=[]`、ID省略、`required=false`、最低版引下げ、argv等の変更を拒否し、同一契約の継承と追加checkの登録を確認する。 |
| T-04 | QA-F03 | Gate優先順位をruntime、Reviewer契約、OpenSpecへ統一する。確認済みの受入基準FAILまたは必須check FAILがあればFAILを記録し、必須checkのERROR/NOT_RUNはその事実と理由を併記する。既知FAILがなく必須確認が未完了の場合はINCONCLUSIVE、識別・hash等のprovenance不備はHOLDとする。 | 「基準FAIL＋必須ERROR」「基準PASS＋必須ERROR」「必須FAIL＋別check NOT_RUN」「資材不一致＋必須NOT_RUN」を表形式で検査し、各理由を保持しながら一貫したGateを受理する。QA-003のFAILレビューが原文のまま取り込み可能である。 |
| T-05 | QA-F04 | 静的配布templateの参照資材hash行と「実施側タスク」節を動的template・パーサーに合わせる。品質Skillの変更履歴と版を更新する。 | 指摘なし・指摘あり・必須checkありの完成template例を`review.check`で検証し、必須節・参照資材hashが不備なく通る。runtimeとの同期検査も通る。 |
| T-06 | QA-F05 | 対象SHAのGit treeと実際の保管状態に合わせて、Plan 033とQA履歴の「退避済み」「復元可能」等の記録を訂正する。9原文を本対象に再追加するのではなく、未同梱・別記録・復元未検証の状態を正確に記す。 | クリーンcloneのtreeと文書記述が一致し、原文の所在・hash・復元可否を誤認させない。必要な場合は実在する記録だけを個別に参照する。 |
| T-07 | QA-F05 | `focus_provenance_plans.md`のArtifacts README相対リンクを実在する参照先へ直す。 | 変更対象Markdownの相対リンク検査でリンク切れが0件。 |
| T-08 | QA-F06 | 独立環境で元Reviewed SHA `d9bad5c125791306e38bca8830b4082f7f38fc6b`に対する必須`pytest tests -q`を追試する。Python 3.10以上とpytestが既に使える環境を用い、無承認の依存追加はしない。修正後候補でも同じ必須検証を再実行し、実行Evidenceを次回独立QAへ渡す。 | 両対象SHAについてPython版、pytest版、argv/cwd/env/timeout、exit code、所要時間、stdout/stderrとSHA-256を記録する。利用可能な環境が得られなければERROR/未検証を保持し、PASS扱いしない。 |

## 修正対象パス一覧

承認対象は次のパスに限定する。T-08は同じsuiteを実行するが、検証環境の設定・依存変更は含めない。

```text
docs/Artifacts/implementation_plan_033_1004.md
docs/Archives/qa_workflow/qa_workflow_history_001_1004.md
openspec/changes/unify-qa-skill-workflow/design.md
openspec/changes/unify-qa-skill-workflow/specs/unified-qa-workflow/spec.md
openspec/changes/unify-qa-skill-workflow/tasks.md
quality-loop/qa_workflow/cli.py
quality-loop/qa_workflow/gitops.py
quality-loop/qa_workflow/review.py
quality-loop/qa_workflow/store.py
quality-loop/qa_workflow/workflow.py
quality-loop/skills/blind-qa-cycle/references/focus_provenance_plans.md
quality-loop/skills/quality-qa/CHANGELOG.md
quality-loop/skills/quality-qa/VERSION
quality-loop/skills/quality-qa/references/publish.md
quality-loop/skills/quality-qa/references/reviewer_contract.md
quality-loop/skills/quality-qa/runtime/qa_workflow/cli.py
quality-loop/skills/quality-qa/runtime/qa_workflow/gitops.py
quality-loop/skills/quality-qa/runtime/qa_workflow/review.py
quality-loop/skills/quality-qa/runtime/qa_workflow/store.py
quality-loop/skills/quality-qa/runtime/qa_workflow/workflow.py
quality-loop/skills/quality-qa/templates/qa_review.md
quality-loop/tests/test_qa_workflow_contract.py
quality-loop/tests/test_sync_productivity_skills.py
```

## 実装後の検証

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q`をPython 3.10以上で実行する。
- QA公開・再QA・Gate優先順位の拒否系を一時bare remote/fixtureで確認する。
- `quality-loop/qa_workflow`と`quality-loop/skills/quality-qa/runtime/qa_workflow`の同期を検査する。
- `openspec validate unify-qa-skill-workflow --strict --json`と変更Markdownの相対リンク検査を行う。
- QA-F06の元SHA追試と修正後候補の検証結果を分けて記録し、独立QAへ提出する。

## 実行境界

本書は修正の承認依頼であり、コード変更・テスト実行・branch/worktree操作・commit・push・外部配置を許可しない。承認後も実装範囲は上記対象パスとT-01〜T-08に限定する。計画hashと対象path集合の両方が一致する明示承認を受けるまで実装を開始しない。
