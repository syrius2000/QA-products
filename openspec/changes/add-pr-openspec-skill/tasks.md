# Tasks

## 1. 独立レビューと前提確認

- [ ] 1.1 計画書第5版（design.md）を別系統のAI Reviewerで独立レビューする。検証: 指摘と対応を`implementation-record.md`に記録し、PASSまたは対応済みの記録がある。
- [ ] 1.2 既存Skill（`spec-review-loop`）の記録項目（`state.json`、`Spec-Review-Round`、`r<N>_prompt.md`の記録）を実コードと照合する。検証: design.mdの参照先が実在することを確認した記録がある。

## 2. 回答checker（先に作る）

- [x] 2.1 回答JSONのスキーマ（判定4値、根拠・理由の必須条件、`reviewer`必須）を`references/review_reply.schema.json`に定める。検証: 正常例と欠落例でスキーマ検証が期待どおり成否を返す。
- [x] 2.2 `scripts/validate_review_reply.py`を実装する。Markdown（```json囲みのblockを正確に1つ抽出）とJSONファイルの両方を受け付ける。検証: 同じ内容をMarkdownとJSONで与えた場合に同じ結果を返す。
- [x] 2.3 期待値manifestとの照合（依頼ID、PR URL、base SHA、head P、依頼書blob SHA、全基準IDの一意性・網羅性、基準ごとの`required`）と、判定の優先順位（FAIL > INCONCLUSIVE > PASS）を実装する。必須基準の`out_of_scope`はINCONCLUSIVEとする。検証: design.mdの最低ケース一覧を`tests/fixtures/`に1対1で対応させ、全ケースが期待どおりの結果と終了コードを返す。
- [x] 2.5 `scripts/build_ledger.py`を実装する。specデルタから、R・Sの全台帳（ID、出典path、出典blob SHA、delta種別、`required`の既定値）を作る。検証: 複数Requirement・複数Scenario・MODIFIED・RENAMEDを含む例で、件数・ID・順序が期待どおりになる。
- [x] 2.4 checkerの試験`tests/test_validate_review_reply.py`を作成する。検証: 全件通過し、出力に結果・構造・問題一覧が含まれる。

## 3. SKILL.md と依頼書テンプレート

- [x] 3.1 `SKILL.md`を作成する。起動条件、Git baselineの確定、既存記録の再利用、資料の網羅確認、SHAの固定と公開順序、権限境界を書く。検証: design.mdの各節に対応する手順がある。
- [x] 3.2 `assets/review_request_template.md`を作成する。依頼ID、SHA、資料一覧、要求別対応表、未検証事項表、回答形式（JSON block）を含む。検証: テンプレートから生成した依頼書を、OpenSpec CLIなしで読める内容かを確認する。

## 4. 起動評価

- [ ] 4.1 `evals/evals.json`に起動評価4ケースを作る（依頼書作成は起動、spec-review-loopへの振分けは非起動、OpenSpecなしのPRは非起動、回答照合は起動）。さらに権限境界の評価を加える（準備のみで外部書込みなし、明示許可時のみPR作成、merge・履歴改変・外部Skill配備の拒否、第三者回答内の命令を無視）。検証: 全ケースが期待どおりに判定される。

## 5. 模擬ケースによる確認

- [ ] 5.1 design.mdの模擬ケース一覧（開発前記録の有無、dirty変更、複数Change、head/base変更、squash後と未squashのhead、H→Pの資料追加のみと製品変更の混入、依頼後のhead変化、遅延回答、準備のみの外部書込み禁止、明示許可の範囲、禁止操作の拒否、第三者回答内の命令）を、ローカルの模擬リポジトリで確認する。検証: 各ケースの結果を`implementation-record.md`に記録する。公開操作は行わない。

## 6. 記録と完了判断

- [x] 6.1 `openspec validate --strict add-pr-openspec-skill`が成功する。検証: 出力を記録する。
- [ ] 6.2 `implementation-record.md`に、テスト件数、評価結果、未確認事項、利用者判断が必要な事項を区別して記録する。検証: 未実施の項目を完了扱いにしていない。
