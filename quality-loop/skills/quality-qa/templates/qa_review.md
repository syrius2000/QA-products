# 独立QAレビュー

created: 2026-10-04 10:45 (JST)
update: 2026-10-04 10:45 (JST)
author: 担当AI (実際のモデル名)

## 識別

- 契約: unified-qa-review-v1
- 依頼ID: QA-NNN
- リポジトリ: OWNER/REPOSITORY
- 開発ブランチ: TOPIC_BRANCH
- 初回基準SHA: INITIAL_FULL_SHA
- 差分基準SHA: BASELINE_FULL_SHA
- 対象SHA: REVIEWED_FULL_SHA
- サイクル: 1
- 要件指紋: REQUIREMENTS_SHA256
- `quality-loop/skills/quality-qa/SKILL.md`: SHA256:EXPECTED_HASH
- `quality-loop/skills/quality-qa/references/reviewer_contract.md`: SHA256:EXPECTED_HASH
- 担当: 別のレビュー担当名
- 実行経路: クラウド
- 提出版: 1
- 訂正ID: なし
- 置換元SHA256: なし
- 保存先: docs/Artifacts/qa_review_NNN_MMDD.md
- 結論: INCONCLUSIVE
- 必須確認: 未完了

## 確認範囲

確認した対象版のファイルと要件、根拠を記載。

## 参照資材の検証

対象Reviewed SHAの指定QA Skillと出力契約を読み、全hashが一致することを記録。不一致または取得不能ならGateをHOLDとする。

## 受入基準の照合

- AC-001: 依頼に記載された受入基準の原文を保持 | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果

## 実施した検証

実行した方法・結果・根拠を記載。実行していない場合は「なし」。

## 未検証事項

実行できなかった必須確認と理由を記載。ない場合は「なし」。

## 指摘

指摘がなければ「なし」。指摘がある場合は次のブロックを必要数追加。

```markdown
### 指摘 QA-F01
- 種別: 要求未達
- 重大度: 重大
- 状態: OPEN
- 要求対応: 受入基準の項目
- 根拠: src/example.py:12 対象版での観測
- 影響: 利用者への影響
- 対応案: 修正または確認の具体案
- 対象: src/example.py
- 完了条件: 観察できる完了条件
- 検証方法: 手順と期待結果
```

## 前回指摘の再確認

- 対象: なし

## 残余事項

改善提案、残る確認と返却参照を記載。ない場合は「なし」。
