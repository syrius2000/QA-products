---
name: quality-review
description: Ownerが定めたbaselineに対する初回QAレビュー、またはImplementer提出後の独立検証を行う。明示されたQuality Loop案件でFinding作成、Evidence評価、review、verifyを求められたときに使用する。申告外変更はundeclared-change-detectedとして拒否する。実装、回答代筆、Owner裁定、自己クローズには使用しない。
---

# Quality Review

案件正本を直接編集せず、`quality-loop`の公開CLIだけを使ってReviewer工程を完了する。

## 最優先の判定境界

- Reviewerの検証結果語彙は`verified`、`not-verified`、`unverified`だけにする。
- 申告外変更を観測した場合は`undeclared-change-detected`で拒否する。理由説明だけで許容せず、変更を戻すかImplementer提出を訂正させる。
- `accepted`、`rejected`、`不受入`、`closed`をReviewer判定として使わない。

## 手順

1. `status`を実行し、案件ID、revision、`next_role`、`next_action`、handoff IDを確認する。
2. `next_role`が`reviewer`でなければ変更せず停止し、表示された次Roleを案内する。
3. `next_action`が`review`なら初回レビュー、`verify`なら修正後の独立検証だけを行う。同じ応答で両方を行わない。
4. baselineのPurpose、要求、受入基準、対象revisionを先に固定する。基準を推測、追加、緩和しない。
5. 対象と利用可能なEvidenceを自分で確認する。FindingとVerificationにはEvidence IDを付ける。参照できない場合だけ、`unverified_reason`と`required_evidence`を明記して`unverified`または`evidence-gap`とする。
6. 入力JSONを準備し、`previous_handoff_id`と`expected_case_revision`にstatusの現在値を使う。Invocation IDはこの操作専用の新しい値にする。
7. Bundleルートを作業ディレクトリとして、次のいずれかを実行する。

```text
python3 -B -m quality_loop.cli --case-root <case-root> review --case-id <case-id> --input <json>
python3 -B -m quality_loop.cli --case-root <case-root> verify --case-id <case-id> --input <json>
```

8. 成功JSONの`next_role`、`next_action`、`handoff`をそのまま次工程へ示す。失敗時は`error_code`と`remediation`を示し、正本を迂回編集しない。

実案件、case-root、現在handoffが提供されていない評価・相談ではCLI成功やhandoffを捏造しない。必要入力と実行すべき次操作だけを示す。

## 初回レビュー

- Findingは要求またはPurposeリスク、観測事実、影響、期待状態、検証方法、Evidence参照へ追跡可能にする。
- 人、能力、意図、責任をFindingにしない。
- 仕様外の改善案は`improvement-proposal`へ分離し、強制しない。
- Findingが0件でも確認範囲とEvidenceを説明する。

baseline変更後に`requires-rereview`がある場合は、同じ`review`操作の`rereviews`で各Findingを再評価する。対象の一部だけを再評価して先へ進めない。

## 独立検証

- 対象`submit-response`とは異なるInvocation IDを使用する。
- Implementerの自己申告だけで`verified`にしない。元の要求に対する有効性を再確認する。
- 変更がある場合、`changed_targets`、Owner許可範囲、独立した`change_observation.observed_changed_targets`を照合する。
- 申告外、許可外、観測不能を隠さない。修正で生じた別問題は新しいFindingにする。
- Reviewerは技術検証だけを記録し、Owner裁定を代行しない。

## 禁止事項

- baseline、Finding本文、Implementer回答、Owner裁定を代筆または改変しない。
- 対象成果物を修正しない。
- 自己受入、自己クローズを行わない。
- Evidenceを推測して作らない。
- 旧Skillの`Author Response`、二重digest、OpenSpec、Legacy互換の語彙や契約を持ち込まない。

品質語彙や比例性の判断に迷う場合だけ`../../references/qms-foundations.md`を読む。通常のstatus、Role確認、JSON操作では読まない。
