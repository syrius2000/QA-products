# 次の作業へ進むための再開ガイド

更新日: 2026-11-12

## 現在地

- リポジトリ: `/home/manabu/Programing/00ALL-repos/qa-products`
- ブランチ: `plan/qa-agent-orchestration`
- [変更計画](qa_agent_orchestration_plan_20261112.md): 対話合意を保存し、自己点検を1回実施して修正済み。
- [falsify-me点検](qa_agent_orchestration_falsify_20261112.md): 独立QAではない。CLI実機確認と製品実装は未実施。
- 初稿はcommit `04ac253`。比較元の製品HEADは計画に記録。
- T01〜T09は未実施。今回の成果物は計画・点検・引継ぎ文書。

## 次のタスク

最初は**T01（現行workflow/Role/配布差分の棚卸し）とT02（状態正本・往復・許可の契約設計）**を行う。

1. `git status --short --branch`でブランチと既存変更を確認する。
2. `AGENTS.md`、上記計画、点検記録を読む。古いmemo.md内の過去案件へ戻らない。
3. `quality-loop/skills/quality-qa/`、`quality-loop/quality_loop/`、`quality-loop/skills/spec-review-loop/runtime/`の状態・操作・権限・保存先を比較する。Role同梱runtime、Productivity-Skill、グローバル配置はそれぞれ版/hash差を確認する。
4. 既存契約の単純連結を前提にせず、状態正本を1つ選ぶ設計案を作る。初回promptへ自己評価を注入しない再利用範囲を示す。
5. 正常例、3回の計画差戻し、3往復目の計画合意、反証による撤回、2人対立、対象版変更、重複配送・中断再開、許可失効を状態トレースで示す。
6. 計画のT01/T02と未解決事項を実際の結果に合わせて更新する。次はT03の接続実験とT04のOpenSpec化。

T01/T02は設計作業。現在の依頼を製品実装や実際のQAループ実行の許可へ広げない。T03で外部AI実験を始める際は、試験対象・モデル・権限・返却契約を具体化して実行指示の範囲を確認する。実装は計画合意だけで開始せず、ユーザーの別途変更指示に従う。これは本件で合意された権限分離である。

## 次セッションへ渡せる依頼文

```text
qa-productsのplan/qa-agent-orchestrationブランチで続けてください。
AGENTS.mdとdocs/Artifacts/qa_agent_orchestration_next_20261112.mdを読み、
変更計画とfalsify-me点検を引き継いで、T01とT02の調査・設計を進めてください。
3 workflowの状態正本とRole接続、全工程3往復のカウント、計画合意と
ユーザー実装許可の分離、spec-review-loopの再利用範囲を具体化してください。
今回は設計文書の更新まで。製品実装・外部配置・mergeは開始しないでください。
```

## 保留・後続

blind-qa-cycleのGit/Web QA連携、spec-driven-qa-reviewの専門方式接続、外部Skill配布、main統合、remote push。必要に応じて別タスクにする。家と会社の実行環境差、同一モデルの独立性限界を引き継ぐ。
