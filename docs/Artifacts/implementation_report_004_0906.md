# Capability Parity残件の実装報告

created: 2026-09-06 13:54 (JST)
update: 2026-09-06 14:10 (JST)
author: Codex (GPT-5)

## 1. 対象

- OpenSpec Change: `spec-driven-qa-capability-parity-and-legacy-compat`
- 対象計画: [implementation_plan_021_0906.md](implementation_plan_021_0906.md)
- 開始時点: 23/25タスク完了、残件は5.1と6.1

## 2. 実施内容

- CandidateのEvidence validatorで、空または欠落したEvidence bundleを拒否するよう修正した。
- Candidateの空Evidence拒否プローブを、`expected=reject`、`actual=reject`として再実行した。
- Candidate／compactの自己クローズ、Reviewer正本書込み、未知Finding、Evidence、Workspace境界の安全回帰を再実行した。
- Agent／Run集計器に、異なるmanifest項目名を正規化して必須項目別の状態を保存する処理を追加した。
- 欠測のPrompt、件数、未実行項目などは推定せず、`unverified`として保持する設計にした。

## 3. 検証結果

- Candidate／Reviewer／Author／Parityの全テスト: 128件成功。
- 安全回帰: `observed`。
- Candidate空Evidence拒否: `observed`。
- 契約適用可能性: `observed`、blocking rows 0件。
- Agent／Run集計の単体テスト: 成功。

## 4. 6.1の完了

Source Manifestの不一致は、過去の文書整理で評価プロトコルの相対リンクだけが変更されていたことを確認した。元のSHA-256を`rebaseline_history`へ保存し、現行ファイルのサイズ・SHA-256を再基準化した。

- Source Manifest検証: 成功。
- Agent／Run集計: 5 Agent／Run、`observed-with-unverified`。
- 必須8項目の状態を各Runへ保存し、欠測は`unverified`として保持。
- manifest／resultsのAgent／Run識別子整合性: 成功。

以上によりOpenSpec Task 6.1を完了へ更新した。

## 5. 残余事項

外部LLMのToken・Latency・正答率は取得不能なため`unverified`である。また、総合レポートは人間裁定未完了のため`evidence-gap`であり、互換性全体の合格や外部配備可否を意味しない。

## 6. Git・外部操作境界

- 外部Skill配置、他リポジトリ変更、旧版削除、commit、pushは実施していない。
- 作業開始時点の差分はなく、今回の変更は計画、Candidate validator、Parity検証コード・テスト・Evidenceに限定した。
- OpenSpec ChangeのArchiveは実施していない。
