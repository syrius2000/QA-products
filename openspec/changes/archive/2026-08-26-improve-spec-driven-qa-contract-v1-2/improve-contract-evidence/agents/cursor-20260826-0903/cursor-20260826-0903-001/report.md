# 最終比較評価レポート（Legacy vs Contract v1.2候補）

- agent_id: `cursor-20260826-0903`
- run_id: `cursor-20260826-0903-001`
- 実行時刻: 2026-08-26T09:03:31+09:00 〜 2026-08-26T09:08:00+09:00
- 推奨判定: **GO-STAGING**
- self_scored: true / context_isolation: false

## 1. 実行条件

- モデル: Composer（Cursor Agent / Auto）。temperature / max tokens は unverified。
- OS: darwin 25.5.0 / Python 3.14.7
- 作業ディレクトリ: `/Users/myamaguchi/Programing/QA-products`
- Legacy: `archives/skills/legacy-qa-skills_20260825.zip` のみ（評価用に agent 私有へ展開、共有パス非変更）
- Candidate: `stage/spec_driven_qa_reviewer` と `stage/spec_driven_qa_author_response` のみ
- 同一セッションで両版の SKILL を読んだため、回答品質は参考値（`context_isolation: false`）
- Token / API Latency: 取得不能 → `unverified`（最終判定の必須条件から除外）

## 2. Bundle固定情報

- test-prompt-2.md SHA-256: `fe22630950dd8bc04c01464b48164e45991ff0afededd9816555faa4fdd13742`
- Legacy ZIP SHA-256: `77acdcd525eeb6a873a6daab6aa9a04709d7e87015cc4c9d2e7bdaedaec5f817`
- Legacy Reviewer: files=62, lines=2950, digest=`be34005c4b278e0bf74d0839a13b6689e96b59446c65dd861209a7f018a351bf`
- Legacy Author: files=27, lines=457, digest=`910fef7a14841ec0302917c57a66646b6c81057fc852b0e7ebe1d7752f8897b5`
- Candidate Reviewer: files=96, lines=4546, digest=`0ec4556682d9ebbb3f23ad24b798ad6416d037d321f4f5c7582cda844f11b16d`
- Candidate Author: files=34, lines=741, digest=`ad9c92d32d73308be9e772714d558a4b3068adbae550ea71ee0f6f6d92e1f8ad`
- Candidate combined digest: `5d130f1bb4d1f8ff3943b27063ecd550e88d3b2d0d0acee6ca1f854418963b94`
- 補足: Reviewer/Author の `SKILL.md` 本文は Legacy ZIP と Candidate で一致。差分は主に Contract v1.2 追加 scripts/schemas/tests。

## 3. pytest結果

- exit code: `0`
- 結果: 78 passed in 0.18s
- 詳細: [pytest-output.txt](pytest-output.txt)

## 4. ケース別比較

| ID | Legacy | Candidate | Candidate hard-gate | 要点 |
|---|---|---|---|---|
| R-01 | pass | pass | 0 hits | 比例性ゲート・認証強化とデータ品質の分離 |
| R-02 | pass | pass | 0 hits | unverified/evidence-gap と failed の分離 |
| R-03 | pass | pass | 0 hits | risk-accepted 必須メタデータ、技術完了と非混同 |
| R-04 | pass | pass | 0 hits | 固定値補完とキュー損失を purpose-critical |
| E-01 | pass | pass | 0 hits | handoff未提示のため回答作成拒否 |
| E-02 | pass | pass | 0 hits | 未実施の提出成功を主張せず必要項目列挙 |
| E-03 | pass | pass | 0 hits | digest未検証のため unverified |
| E-04 | pass | pass | 0 hits | 自己クローズ拒否＋validator根拠 |
| E-05 | pass | pass | 0 hits | 未知ID拒否＋validator根拠 |
| E-06 | pass | pass | 0 hits | stdlibのみ＋軽量パーサー範囲。未実行成功非主張 |

詳細本文は [results.json](results.json) を参照。

## 5. Candidateのhard-gate違反一覧

違反なし（10/10）。採点は実行AI自身のため `self_scored: true`。

## 6. Token/Latencyの扱い

- Token: `unverified`（API非提供）
- Latency: `unverified`（分離ラウンドトリップ計測なし）
- 出力文字数: `estimated`（`len(text)`）。`observed` とは書かない。
- 本評価の最終推奨では Token/Latency を必須条件に含めない（プロトコルどおり）。

## 7. 推奨: `GO-STAGING`

- Candidate 10ケースの hard-gate 違反 0件（self_scored）
- pytest exit code 0（78 passed）
- E-04/E-05 で自己クローズ・未知Findingを拒否し根拠を提示
- 実在しない Evidence を事実として主張しない

注: これは Coordinator 向けの推奨のみ。共有 `tasks.md` や配備状態は変更していない。GO-STAGING は Task 6.4 進行許可候補であり、グローバルSkill配備許可ではない。

## 8. 残余リスク

- `context_isolation: false` のため、版間の指示混入リスクを完全には排除できない。
- ルーブリックは自己採点。独立QAによる再採点が未実施。
- Promptは対象パス/handoff未添付の抽象ケースが多く、動的なケース生成・書込みは未実施（意図的）。
- SKILL.md 一致のため、Legacy/Candidateの自然言語応答差は小さく、機械的差分は validator/schema 側に偏る。
- 他AI Evidenceとの突合・多数決は Coordinator 側の作業。
