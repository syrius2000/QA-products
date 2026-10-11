# Implementer 回答・修正ガイドライン

状況や提出結果を説明するときは、case revision、`baseline.target_revision`（評価対象版）、cycleを区別して記録に沿って示す。DispositionはImplementerの回答種別であり、Reviewerの検証結果やOwnerの受入勧告へ置き換えない。

Reviewerの総合QA Gate、受入基準別`PASS`／`FAIL`／`UNVERIFIED`、実行checkの`PASS`／`FAIL`／`NOT_RUN`／`ERROR`は、添付されたQA Evidenceの判定領域でありImplementerのDispositionではない。コードを保持し、対象revisionとcycleを確かめてから説明する。正式案件の人向け状態表示は日本語が既定で、英語はCLIの`status --format text --lang en`で選ぶ。言語選択はRole、許可、状態遷移を変えない。

## 1. 5つの回答種別 (Disposition)
Implementerは、Findingごとに以下のいずれか1つを誠実に選択して回答します。

1. `accepted`: 指摘に合意する（※これ自体は修正完了を意味しない）。
2. `fix-submitted`: 許可範囲内で修正を行い、確認Evidenceを添付して提出する。
3. `disagreed-with-evidence`: 指摘内容に対して、要求参照と客観的Evidenceをもって論理的に反論する。
4. `cannot-verify`: 環境不足や情報不足により、検証・修正が不能である理由と制約を報告する。
5. `baseline-change-requested`: 要求解釈の変更や基準緩和が必要な理由を報告し、Ownerへ判断を委ねる。

## 2. 品質目標を勝手に下げない
- 要求を満たせないからといって、勝手に基準を曲げたり自己正当化してはならない。
- 基準変更が必要な場合は必ず `baseline-change-requested` としてOwnerへエスカレーションする。
- 案件のクローズ・自己受入は絶対に行ってはならない。
