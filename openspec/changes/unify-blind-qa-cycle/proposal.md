# Proposal

## Why

`blind-qa-cycle`が複数の場所で別々に進化し、事前基準づくり、実装後の固定SHAレビュー、ローカル／クラウドの受け渡し、Finding対応、再QA、サイクル終結の手順が分散している。既存QA Skillの役割を保ちながら、監査ブランチ上の独立QAを一貫して進め、人がQA後に理解を振り返る手段も用意する。

## What Changes

- 分散した`blind-qa-cycle`の知見を、監査ブランチ上で開始から終結まで扱う単一のSkill契約へ統合する。
- 実装前Baselineを用意する理想経路と、実装後に対象をYip commitへ固定して開始する経路を定義する。
- ローカル／クラウドReviewerが固定された対象SHAを点検し、所定のcycle DIRに評価・Finding別修正依頼を保存し、Yip commitによる対応・再QAへ引き継ぐ手順を明確にする。
- QA結果、修正・再QA履歴、残余リスクを追跡して監査ブランチ上でcycleを終結する。既定ブランチへのmergeは自動化せず、Ownerとの別判断にする。
- QA cycle終結時にHuman Understanding Noteを人が約5分で記入できる作成支援を加える。Noteはcycleと関連SHA・Gateへ結び付けるが、本文をAIが代筆・採点せず、QA GateやOwner受入の根拠にしない。
- `.agents/skills/blind-qa-cycle/`と正本の関係を明確にし、古い本文が意図せず使われる状態を解消する。既存cycle記録は書き換えない。
- `quality-qa`、`quality-review`、`quality-response`は統合・改変・削除せず、通常QAおよび正式Quality Loop案件での既存用途を維持する。利用場面、成果物、case正本、CLI、Git操作の境界を`blind-qa-cycle`側に示す。

## Capabilities

### New Capabilities
- `blind-qa-cycle`: 固定SHA、Yip commit、ローカル／クラウドhandoffを使う独立QAサイクル、Finding対応・再QA・監査ブランチ上の終結、およびHuman Understanding Note作成支援を定義する。

### Modified Capabilities

なし。通常QAと正式Quality Loop caseの既存仕様要件は変更しない。

## Impact

- `quality-loop/skills/blind-qa-cycle/`配下のSkill本文、出力契約、machine schema、Git運用・参照資料。
- `.agents/skills/blind-qa-cycle/`にある旧版との関係と、正本／参照配置の扱い。
- `docs/Artifacts/qa_cycles/<topic>/c<N>/`の新規cycle成果物。Human Understanding Noteのファイル形式と作成支援方式はDesignで確定する。
- 対象外: `quality-loop/skills/quality-qa/`、`quality-review/`、`quality-response/`の実装・既存caseデータ、QA対象製品コード、外部Skill配置、main/masterへのmerge。
