# 比例的QAゲート代表ケース評価

評価日: 2026-08-25 (JST)
対象: `spec-driven-qa-review`
評価方式: スキル本文・参照資料・記録テンプレートの静的適合性確認

## ケース1: 家庭内LANの未指定認証強化

期待結果: `proportional-home`を選択し、仕様・目的・脅威モデルに根拠がない認証強化を自動的なCritical/Highにしない。運用衛生または判断要求として分類する。

結果: 合格。`SKILL.md`のProportionality Gate、`risk-profiles.md`の比例プロファイル、Finding分類に規則を確認した。

## ケース2: 実機未接続・外部サービス未起動

期待結果: 証拠不足を`unverified`または`evidence-gap`とし、再現した`failed`と区別する。

結果: 合格。`SKILL.md`、`qa-principles.md`、`risk-profiles.md`に明記されている。

## ケース3: 所有者による残余リスク受容

期待結果: 技術判定を`fixed-and-verified`へ変更せず、所有者、理由、範囲・前提、管理策、期限または見直しトリガーを記録する。

結果: 合格。`SKILL.md`、`templates/findings.yaml`、`templates/author-response.md`に記録項目を確認した。

## ケース4: CSV固定値補完と再起動時キュー損失

期待結果: `proportional-home`でも観測値の意味変質、欠損、復旧不能なデータ損失を`purpose-critical`または`spec-required`として評価する。

結果: 合格。新規仕様、`qa-principles.md`、`risk-profiles.md`に優先事項とCSV補完の扱いを確認した。

## 検証制約

本評価はスキル資材の静的確認であり、別AIによる実プロンプト実行の性能ベンチマークではない。実際のQA対象を用いたAI間評価は、次回のSkill改善サイクルで追加実施する。
