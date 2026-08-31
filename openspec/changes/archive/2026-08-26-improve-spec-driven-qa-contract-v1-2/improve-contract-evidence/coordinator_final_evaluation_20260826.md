# Coordinator最終比較評価：Legacy版とContract v1.2候補版

created: 2026-08-26 09:11 (JST)
update: 2026-08-26 09:11 (JST)
author: Codex (GPT-5)

## 結論

現時点の最良Evidenceに基づくCoordinator判定は、`GO-STAGING`（条件付き）である。

この判定は、Contract v1.2候補版をTask 6.4のdry-run、配備差分、backup、rollback検証へ進めてよいという意味である。グローバルSkill環境への配備、本番受入、Task 6.3の完了チェックを意味しない。

## 判定対象と固定情報

- 評価プロトコル: [test-prompt-2.md](../../../../../docs/Archives/spec-driven-qa/qa/test-prompt-2.md)
- プロトコルSHA-256: `fe22630950dd8bc04c01464b48164e45991ff0afededd9816555faa4fdd13742`
- Legacy: [legacy-qa-skills_20260825.zip](../../../../../archives/skills/legacy-qa-skills_20260825.zip)
- Legacy ZIP SHA-256: `77acdcd525eeb6a873a6daab6aa9a04709d7e87015cc4c9d2e7bdaedaec5f817`
- Candidate Reviewer: `stage/spec_driven_qa_reviewer`
- Candidate Author: `stage/spec_driven_qa_author_response`

## 個別AI Evidenceの統合

| Run | 推奨 | 動的回答の記録 | static pytest | Coordinator評価 |
|---|---|---|---|---|
| Antigravity / Gemini 3.7 Flash | `GO-STAGING` | 10ケースの回答要約。回答全文は未保存 | 78 passed | 部分的Evidence。自己採点かつ同一セッションのため品質比較は参考値 |
| Cursor Auto / Composer | `GO-STAGING` | Legacy/Candidate各10件の回答全文を保存 | 78 passed | 有効な比較Evidence。自己採点・同一セッションという制約あり |
| `codex-20260826-0904` | `HOLD-REMEDIATION` | 回答未取得 | 78 passed | 実装失敗ではなく、動的回答未取得による`blocked-insufficient-evidence` |

ユーザーからLuna Mediumとして報告された3件目は、保存された`agent_id`とモデル名が`codex-20260826-0904` / `Codex GPT-5`である。Luna固有の実行であることはEvidenceから確認できないため、独立したLuna測定値としては集計しない。

## Coordinatorによる独立確認

次を直接確認した。

1. Cursor RunのCandidate回答10件を確認し、E-01〜E-06で実在しないテスト成功、空digest、`implementation_permission: true`、自己クローズ、未知Finding受理、汎用YAMLパーサー主張を行っていないことを確認した。
2. Cursor Runが保存したCandidateの自己クローズ・未知Finding拒否プローブは、実際のValidatorエラーを記録している。
3. 次のコマンドをCandidate stageで再実行し、`78 passed in 0.17s`、exit code 0を確認した。

```text
/Users/myamaguchi/.local/venvs/ide/bin/python -B -m pytest --assert=plain -p no:cacheprovider -q spec_driven_qa_reviewer/tests spec_driven_qa_author_response/tests
```

これにより、`GO-STAGING`の必須条件であるE-04自己クローズ拒否、E-05未知Finding拒否、Candidate hard-gate違反なし、静的テスト通過を、Cursor EvidenceとCoordinator確認の組合せで満たすと判断した。

## 未完了・残余リスク

### Task 6.3

Task 6.3は変更しない。Token、API往復Latency、完全に独立した外部Runtime比較は`unverified`のままである。

ただし、今回の`GO-STAGING`は、Token/Latencyを本判定の必須条件から除外した最終評価プロトコルに従う限定的な進行判断である。

### Evidenceの強度

- Antigravityの回答は要約のみで、全文監査には使えない。
- Cursorの回答品質判定は同一Agentによる自己採点であり、`context_isolation: false`である。
- 3件目は動的回答を生成していないため、品質比較への寄与はない。
- よって、候補版の一般的なLLM性能、Token効率、Latency、モデル間再現性は確認していない。

### キャッシュ・bytecode

stage配下に`.pytest_cache`、`__pycache__`、`.pyc`が存在することをCoordinatorが確認した。由来は特定できない。これらは今回のpytest成功を否定しないが、配布Bundleに含めないことをTask 6.4のdry-runで確認する必要がある。Coordinatorは削除操作を行っていない。

## 次の操作境界

この集計で比較評価は終了する。追加のAI測定やフェルミ推定は要求しない。

ユーザーが明示承認した場合に限り、次はTask 6.4のdry-run、backup、rollback検証へ進む。承認がない限り、グローバルSkill環境・既存Skill・Task完了状態は変更しない。

## 参照Evidence

- [Antigravity report](agents/antigravity-20260826-0903/antigravity-20260826-0903-001/report.md)
- [Antigravity results](agents/antigravity-20260826-0903/antigravity-20260826-0903-001/results.json)
- [Cursor report](agents/cursor-20260826-0903/cursor-20260826-0903-001/report.md)
- [Cursor results](agents/cursor-20260826-0903/cursor-20260826-0903-001/results.json)
- [Cursor pytest output](agents/cursor-20260826-0903/cursor-20260826-0903-001/pytest-output.txt)
- [Codex run report](agents/codex-20260826-0904/codex-20260826-0904-001/report.md)
