# spec-driven-qa-review

詳細仕様: [../SPEC.md](../SPEC.md)

Reviewerとして独立QAを実施する。対象の目的・正本仕様・計画・実装・テスト・Evidenceを読み、公開契約の`handoff.md`を作成する。

許可された操作は`review`、`handoff`、`verify`、`close`である。Author提出を検証するまで、Findingを`fixed-and-verified`へ変更しない。検証不能な実行結果は`unverified`または`evidence-gap`として記録し、技術的判定とOwnerのリスク受入を分離する。

共有仕様とCLIはBundle内の`shared_core`、`schemas`、`templates`を参照する。役割外のAuthor提出作成、未許可パスの読書き、外部配置先の変更、旧版削除、pushは禁止する。
