---
name: quality-response
description: 明示されたQuality Loop案件のFindingにImplementerとして回答し、Ownerが許可した範囲だけを修正してEvidenceを提出する。next_role=implementerかつnext_action=submit-responseの案件に使用する。closed変更は情報の有無にかかわらずRole外として拒否する。レビュー、独立検証、Owner裁定、自己クローズには使用しない。
---

# Quality Response

Findingを改変せず、許可境界内で改善を前進させ、Reviewerが追加質問なしで独立検証できる提出を作る。
案件正本`case.json`は直接編集せず、公開CLIの`submit-response`だけで回答を記録する。

## 最優先のRole境界

- `closed`、受入、却下、Reviewer検証を求められても、案件情報の有無にかかわらずRole外操作として拒否する。
- 「情報が揃えばImplementerがクローズできる」と案内しない。クローズ可否は常にOwnerへ戻す。
- Evidence付き反論は`disagreed-with-evidence`として提出し、次工程をReviewerの`verify`にする。

## 手順

1. `status`を実行し、案件ID、revision、`next_role`、`next_action`、handoff ID、実装許可を確認する。
2. `next_role`が`implementer`または`next_action`が`submit-response`でなければ変更せず停止し、表示された次Roleを案内する。
3. handoffに列挙された既知Findingを読み、Finding IDごとに次のDispositionを1つ選ぶ。
   - `accepted`
   - `fix-submitted`
   - `disagreed-with-evidence`
   - `cannot-verify`
   - `baseline-change-requested`
4. 実装許可がない場合はコード、文書、データを変更しない。許可がある場合も`allowed_targets`内だけを変更し、実際の変更を`changed_targets`へ漏れなく記録する。
5. Evidenceは対象revision、方法、結果、相対パスまたは要約を記録する。ファイルEvidenceは案件内`evidence/`へ保存しSHA-256を付ける。未確認を成功に補完しない。
6. 入力JSONを準備し、`previous_handoff_id`と`expected_case_revision`にstatusの現在値を使う。Invocation IDはこの操作専用の新しい値にする。
7. Bundleルートを作業ディレクトリとして実行する。

```text
python3 -B -m quality_loop.cli --case-root <case-root> submit-response --case-id <case-id> --input <json>
```

8. 成功JSONのReviewer向け`next_role`、`next_action`、`handoff`をそのまま提示する。拒否時は対象を追加変更せず、`error_code`と`remediation`に従う。

実案件、Finding本文、case-root、現在handoffが提供されていない評価・相談では、反証内容、CLI成功、handoffを捏造しない。必要入力と予定するDispositionだけを示す。

## 回答の品質

- `accepted`は指摘への合意であり、修正完了を意味しない。
- `fix-submitted`は修正と確認Evidenceを提出した事実であり、有効性確認や受入を意味しない。
- `disagreed-with-evidence`は要求参照と反証Evidenceを示す。感想や自己評価だけで反論しない。
- 環境不足や再現不能は`cannot-verify`として制約と必要な次条件を示す。
- baselineの解釈変更が必要なら自分で変更せず`baseline-change-requested`でOwnerへ返す。

## 禁止事項

- Finding本文、status、baseline、Reviewer検証、Owner裁定を直接変更しない。
- 許可外対象を修正しない。
- 自己検証、自己受入、自己クローズを行わない。
- 人やReviewerの意図を非難しない。事実、要求、Evidence、改善行動を書く。
- 旧Skillの`Author Response`、二重digest、OpenSpec、Legacy互換の語彙や契約を持ち込まない。

品質語彙、反論Evidence、基準変更の境界に迷う場合だけ`../../references/qms-foundations.md`を読む。通常のstatus、Role確認、JSON操作では読まない。
