# spec-driven-qa-author-response

詳細仕様: [../SPEC.md](../SPEC.md)

Authorとして公開契約の`handoff.md`を読み、各Findingへの回答と修正提出を作成する。対象範囲は`respond`、`submit`、`chain-submit`である。`chain-submit`はhandoffのsemantic/content digestとcase revisionを再提示して提出する。

Reviewer正本、Reviewerイベント、closureへ直接書き込まない。Findingを勝手に`fixed-and-verified`へ変更せず、Disposition、理由、修正内容、検証Evidenceを提出してReviewerへ戻す。未検証事項は隠さず`unverified`または`evidence-gap`として記録する。

共有仕様とCLIはBundle内の`shared_core`、`schemas`、`templates`を参照する。外部配置先の変更、旧版削除、commit、pushは禁止する。
