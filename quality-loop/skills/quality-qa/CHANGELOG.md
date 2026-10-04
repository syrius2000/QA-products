# 変更履歴

## 0.2.2

- クラウド公開前に、製品snapshotとQA依頼の機密・個人パス検査、および固定argvで実行した必須checkのEvidence照合を追加。
- 再QAで既存check契約の削除・弱化・変更を拒否。
- Gate優先順位をprovenanceのHOLD、確認済みFAIL、必須check未完了のINCONCLUSIVE、PASSの順に統一。
- 静的Reviewer templateをparser契約へ合わせ、計画所在・Archive記録と相対リンクを訂正。

## 0.2.1

- Reviewer参照を新しい単一Markdown契約へ固定し、旧blind QAの4成果物契約との競合を解消。
- 修正提出時に承認済み計画の実施方式を必須照合。
- 会話による不足情報の整理例を追加。

## 0.1.0

QA依頼・クラウド結果確認・承認後のローカル修正・再QAを単一入口へ統合した。旧Quality Loopと配布先は保持し、実クラウドQAと外部配置の状態はローカルfixtureから分けて報告する。
# 0.2.0

- Git preflightを依頼前に追加し、既存差分を自動変更しない契約を明確化。
- argv等を固定する実行check契約、全受入基準照合、Python等の条件付きCloud実行Evidenceを追加。
- 提出snapshotで修正後の別製品path変更を拒否する回帰確認を修正。
