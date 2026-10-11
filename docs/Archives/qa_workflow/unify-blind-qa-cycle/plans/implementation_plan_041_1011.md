# blind-qa-cycle Baseline選択記述の整合計画

created: 2026-10-11 20:06 (JST)
update: 2026-10-11 20:06 (JST)
author: Codex (GPT-6)

## 目的

独立QA Cycle 1 の未解決Finding `QA-FLOW-M01` に対応し、実装済み変更から独立QAを始める場合のBaseline選択ルールを、blind-qa-cycleの正本と参照文書で一貫させる。

## 現状

- `quality-loop/skills/blind-qa-cycle/SKILL.md` のcloud手順は、明示的なcloud操作で新しいtopic branchを作成し、branch開始前のHEAD等の条件を満たす場合に `branch_start` Baselineを許可している。
- 同ファイル内の概要・invite経路、および参照文書にはcheckpoint必須と読める一般記述が残り、入口によって説明が矛盾する。
- Cycle 1 の記録は `FAIL` のまま保持し、本計画では変更しない。

## 対象

1. `quality-loop/skills/blind-qa-cycle/SKILL.md`
2. `quality-loop/skills/blind-qa-cycle/references/audience_channels.md`
3. `quality-loop/skills/blind-qa-cycle/references/git_wip_flow.md`

## 実施内容

- 3文書のBaseline選択説明を、次の選択肢で整合させる。
  - prepared cycleでは対応する計画commit
  - 通常の事後開始では対応するcheckpoint
  - `cloud`から明示的に開始し、同一操作で新topic branchを作成した場合に限り、条件を確認したbranch開始前HEAD
  - Re-QAでは前cycleのReviewed SHA
- branch開始経路には、同一の明示cloud操作、切替前HEADの固定、対象SHAからbranchが始まること、Reviewed前に別commitがないこと、および招待への理由記録を明記する。
- local、plain invite、条件を満たさない事後開始ではcheckpoint要件を維持する。
- Cycle 1のQA成果物、OpenSpecアーカイブ、他のSkill、`.agents`配置、製品コードには変更を加えない。

## 確認

- 3文書の `branch_start` / checkpoint / prepared / re-QA 説明を相互照合し、条件と例外が矛盾しないことを確認する。
- 変更対象Markdownの相対リンクを検査する。
- `openspec validate --strict unify-blind-qa-cycle` を実行する。アーカイブ済みChangeを現行CLIが対象にできない場合は、実行結果と制約を記録し、成功したと主張しない。
- `git diff --check` と差分パスを確認する。
- これは実装側の静的・仕様検証であり、独立QAのPASSやCycle 1の終結を意味しない。

## 完了条件

- 対象3文書が同一のBaseline選択規則を説明する。
- 例外条件が明示され、local/plain/checkpoint経路の要件が維持される。
- 上記確認の実結果と制約が報告される。

## 作業境界

- 作業ブランチ: `codex/fix-blind-qa-baseline-guidance`
- 先行するアーカイブ作業は `e33901c` として別コミットに保存済み。
- 本計画では、Cycle 1を編集・削除せず、独立Reviewerへの再QA依頼、commit、push、merge、Skill配備も行わない。
