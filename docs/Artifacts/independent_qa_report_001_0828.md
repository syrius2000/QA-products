# Quality Loop 初期版 独立QA報告

created: 2026-08-28 17:27 (JST)
update: 2026-08-28 17:34 (JST)
author: Codex (GPT-5)

## 結論

`quality-loop/`初期版は、低リスク実案件`QMS-README-0001`の記録整合性を満たした。しかし、製品全体としての受入は保留する。独立・読み取り専用レビューで、Role境界とEvidence保証に関する未解決Findingを5件検出したためである。

## 実施範囲

- 承認済み計画: [人間中心の最小QMS協働ループ新規実装計画](implementation_plan_011_0827.md)
- 対象: `quality-loop/`、`qms-cases/QMS-README-0001/case.json`
- 方法: 実装、テスト、実案件正本の静的照合。独立Reviewerは書込み、Git操作、案件正本の更新を実施していない。

## 実案件の確認結果

`QMS-README-0001`はrevision 1から10までのhandoff連鎖、Role別Invocation、Ownerによる最終`accepted`裁定を確認できた。現行`quality-loop/README.md`のSHA-256は、最終修正・検証Evidenceの`39264948f0d89b58a9cf0be7647f606432725ae9169fe418d17dafea6c346c25`と一致する。この案件記録固有のFindingはない。

## 製品実装のFinding

| ID | Severity | 内容 | 影響 |
| --- | --- | --- | --- |
| IQA-01 | high | `adjudicate`がpayload上の`role: owner`だけを確認し、`actor_id`と登録済みOwnerを照合しない。 | 任意の呼出者が自己許可または自己受入を記録できる。 |
| IQA-02 | medium | baseline変更で`requires-rereview`となった既存FindingをReviewerが再評価・更新する経路がない。 | 基準変更後の再レビューを正しく完了できない。 |
| IQA-03 | medium | FindingおよびVerificationが空の`evidence_refs`を受理できる。 | 根拠のない判定を`verified`として記録できる。 |
| IQA-04 | medium | `accepted-with-risk`で条件と期限または再確認トリガーを強制していない。 | 残余リスクが追跡不能なまま終端受入され得る。 |
| IQA-05 | low | `status`が存在しないcase-rootを作成する。 | 公開している読取り操作の契約に反する。 |

## 是正方針

IQA-01からIQA-05は、計画11に既に記載されたOwner境界、Evidence、baseline再評価、リスク付き受入、読取り安全性を実装へ反映し切れていない欠陥である。新たな機能スコープを増やさず、テストを追加したうえで是正した。33件の自動テストは合格している。

## 是正後の独立再確認

別Reviewerによる読み取り専用の再確認を実施した。IQA-01からIQA-05はすべて`fixed-and-verified`であり、新規Findingは0件だった。`QMS-README-0001`はrevision 10、`accepted`、未解決Finding 0件であり、読み取り前後の`case.json` SHA-256も一致した。Reviewerはファイル編集、案件正本の更新、Git操作を行っていない。

この結果により、実装は初期版のOwner裁定に提示できる状態となった。製品全体の受入、保留、却下、または追加修正の最終判断は人間Ownerが行う。
