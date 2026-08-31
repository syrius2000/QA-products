# 標準修正の例

ReviewerはEvidence付きFindingを作成し、handoffでImplementerへ渡す。Implementerは許可済み`changed_targets`、修正Evidence、Finding別の`fix-submitted`を提出する。別InvocationのReviewerが観測結果と有効性をverifyし、Ownerが裁定する。

## 次の担当

Reviewerのverify完了後はOwnerが`adjudicate`する。Implementerは完了を宣言せず、正本を直接編集しない。
