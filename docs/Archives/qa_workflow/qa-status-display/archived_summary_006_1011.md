# QA状態表示ChangeのArtifactアーカイブ

created: 2026-10-11 20:00 (JST)
update: 2026-10-11 20:14 (JST)
author: Codex (GPT-6)

## 対象と結論

対象期間: 2026-10-11

QA状態表示Change `simplify-qa-status-display` の計画、実装報告、基準票、初回QA、修正報告、独立再QAの6文書を一つの履歴単位として保存しました。原文の判断や判定は変更していません。文書の移動で変わる参照先のみ、現行のアーカイブ配置に合う相対リンクへ修正しました。

独立再QAでは固定基準AC-001〜AC-010がすべて合格し、初回所見F-01〜F-03の解消が確認されています。成果物と検証記録は[実装計画](artifacts/implementation_plan_040_1011.md)、[最終実装報告](artifacts/implementation_result_001_1011.md)、[初回独立QA](artifacts/qa_independent_review_001_1011.md)、[修正報告](artifacts/qa_repair_report_001_1011.md)、[独立再QA](artifacts/qa_independent_review_002_1011.md)を参照してください。

## 確定した決定と理由

- 人向けQA状態表示は日本語を既定とし、英語表示を選択可能にする。
- QA工程、総合判定、対象版、サイクル、過去の評価、正式案件の評価勧告を区別する。
- 機械JSON、保存状態、状態遷移、Role制約、承認境界は変更しない。
- 初回QAの不合格記録と修正前の報告は履歴として保持し、再QA結果で上書きしない。
- 実装正本と配布runtimeの一致、外部Skillへの配置、利用者の最終受入は別の工程として扱う。

## 主要成果と検証の限界

- 固定ACは10件すべて合格。F-01〜F-03は独立再QAで解消を確認。
- 実装検証では332テストとsubtest 125件が成功し、OpenSpec strict検証はvalid。
- QA状態表示、CLI・Markdown、言語選択、機械契約と保存状態の不変、runtime同期を検証したと各証拠文書に記録されている。
- このアーカイブ作業では製品テストを再実行していない。実装検証の数値は当時の証拠であり、本作業の再実行結果ではない。
- 移動前SHA-256とArchive側SHA-256を下表で記録した。リンク修復した文書はSHAが変わる。各変更は相対リンク先の修正だけであることを元文書との比較で確認する。
- セキュリティ走査で、これら6文書および本まとめ文書に個人ホームディレクトリ、OS絶対パス、ローカルfile URI、秘密鍵・トークン形式は検出されなかった。
- Archive 6文書、まとめ文書、Archive案内、ルートREADMEの計9ファイルについてMarkdown相対リンク検査が成功した。移動した6文書を移動前Git内容と比較し、本文を維持して承認済みのリンク先だけ修正したことを確認した。`git diff --check`も成功した。

### 基準外所見

- O-01（低）: 一部の裁定後表示で、評価結果が現行版に適用できないことと評価記録自体がないことを読み分けにくい。後続表示改善の候補。
- O-02（低）: 訂正版を受領した後も、案内文が訂正依頼のまま残る。今回の固定受入基準外であり、通常QA案内の後続改善候補。

これらは固定ACの合否を変えず、本アーカイブで修正していません。詳細は[独立再QA](artifacts/qa_independent_review_002_1011.md)と[最終実装報告](artifacts/implementation_result_001_1011.md)に記録されています。

## 未解決事項と引継ぎ

- O-01とO-02を扱う場合は、それぞれの表示・案内範囲を確定して別Changeで検討する。
- blind-qa-cycleの独立QA Cycle 1は後日別途アーカイブされました。Gate `FAIL`と未解決Finding、追加の独立QAを省略する利用者判断は[Cycle 1アーカイブ](../unify-blind-qa-cycle/archived_summary_007_1011.md)を参照してください。元のQA記録は変更していません。
- アーカイブした文書に記載されたテスト結果・仕様判定は当時の履歴であり、現行環境で再検証したとの主張ではない。

## 元文書と復元情報

元文書はすべてアーカイブ下の `artifacts/` に移し、ファイル名を維持しました。元内容へ戻す場合は、Git上の移動前版（`399c8e463cb00a53307f5a3d0e7e18c77309ee82`）から復元できます。Archive内の現行ファイルは、記録した修復後SHA-256と照合してください。

| 元文書 | Archive文書 | 移動前SHA-256 | Archive SHA-256 |
|---|---|---|---|
| `docs/Artifacts/implementation_plan_040_1011.md` | [実装計画](artifacts/implementation_plan_040_1011.md) | `07823805fc1e8014f16745146ab5d7a8b0c60c3366650a74c3f3e726a498ed00` | `07823805fc1e8014f16745146ab5d7a8b0c60c3366650a74c3f3e726a498ed00` |
| `docs/Artifacts/implementation_result_001_1011.md` | [実装報告](artifacts/implementation_result_001_1011.md) | `de9240ad5b3a55994ec067e7c6da020a957b735dbc8d8e5bd23aaa81923cf065` | `223997ce3eed851b84c4bc465f015786e663d835a50abffc7660a37768470571` |
| `docs/Artifacts/qa_acceptance_criteria_001_1011.md` | [固定基準票](artifacts/qa_acceptance_criteria_001_1011.md) | `c34090dd95bcb51b51a387ffa3e26d2c43b8c4d0c40eea0ed8437fe76e2cc0ec` | `c3cd841159adfd06cab6f7dea69a70b501c829f24a7699173f5186429c28e4df` |
| `docs/Artifacts/qa_independent_review_001_1011.md` | [初回独立QA](artifacts/qa_independent_review_001_1011.md) | `c59a91693f9818e792fa893a513029c7aa7945768c8eb58ab8f61e6dce1a25b7` | `d8bf3fc83bec4e17afe95045ea02a26bbbb8740d958ab7d2ef9cec8dbe49edaa` |
| `docs/Artifacts/qa_repair_report_001_1011.md` | [修正報告](artifacts/qa_repair_report_001_1011.md) | `837d33e79ef5c6724e87101336a0c2734673a63c4dd6d72437e996f58ef958fa` | `297a33f81b67834c4334c6abdaa9932ab7523b08114cf2971297e4f7613cc767` |
| `docs/Artifacts/qa_independent_review_002_1011.md` | [独立再QA](artifacts/qa_independent_review_002_1011.md) | `e503cf8b0f548b00ec1b5077cc772c1488cfeb2809067c59249d056182adfe16` | `be5b579f919c0e2137ba13d9fddabc117f72085c6b97671f0672dc87aee9e940` |
