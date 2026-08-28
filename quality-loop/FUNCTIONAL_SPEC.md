# Quality Loop 機能仕様

## 1. 目的

次の4段階を、単一の案件正本`case.json`と明示的なhandoffで実行する。

1. Reviewerが要求とEvidenceからFindingを作る。
2. ImplementerがFindingへ回答し、許可範囲だけを修正する。
3. Reviewerが修正結果を別Invocationで独立検証する。
4. 人間Ownerが受入、リスク付き受入、保留、却下、再作業を裁定する。

## 2. 公開seam

Python APIの`QualityLoop`とCLIの6操作だけを公開seamとする。すべての結果はJSONで表現でき、少なくとも`status`、`case_id`、`case_revision`、`state_changed`、`next_role`、`next_action`、`handoff`を含む。

| 操作 | Role | 前handoff | 主な成果 |
|---|---|---:|---|
| `create-case` | Owner | 不要 | revision 1とReviewer向けhandoff |
| `review` | Reviewer | 必須 | FindingまたはOwner裁定要求 |
| `submit-response` | Implementer | 必須 | Finding別回答と変更Evidence |
| `verify` | Reviewer | 必須 | 独立検証と変更範囲照合 |
| `adjudicate` | Owner | 必須 | 最終裁定または再作業指示 |
| `status` | 読取り | 不要 | 現在地と再開情報 |

更新操作は`operation_id`、`actor_id`、`role`、`invocation_id`を要求する。`review`、`submit-response`、`verify`、`adjudicate`はさらに`previous_handoff_id`と`expected_case_revision`を要求する。`create-case`では`actor_id`と`owner`を一致させ、`adjudicate`では`actor_id`と案件に登録済みのOwnerを一致させる。payload上のRole名だけでOwner権限を得ることはできない。

## 3. 固定安全条件

- baseline、実装許可、追加サイクル、最終リスクはOwnerだけが変更・裁定する。
- ReviewerとImplementerは同一Invocationで兼務しない。
- `verify`は対象`submit-response`と異なるInvocationで行う。
- 古いrevision、誤Role、誤handoff、未知Finding、許可外変更は正本無変更で拒否する。
- Evidence不足は`unverified`または`evidence-gap`とし、`failed`や合格へ補完しない。FindingとVerificationは空でない`evidence_refs`を原則とし、参照できない場合は`unverified_reason`と`required_evidence`を必須にする。
- `fix-submitted`は完了ではない。Reviewerの有効性確認後にOwnerが裁定する。
- Ownerの終端裁定（`accepted`、`accepted-with-risk`、`rejected`）は、dry-run確認後に`confirm: true`を指定しなければ記録しない。
- handoff受領確認、状態更新、次handoff発行を1回の原子的更新にする。
- 同一`operation_id`の再送は二重更新せず、初回結果を返す。
- 初期版は旧コードを再利用、import、複製、転記しない。

## 4. baseline

`create-case`は次を必須とする。

- `purpose`: 対象の目的
- `requirements`: ID付き要求の配列
- `acceptance_criteria`: 受入基準の配列
- `targets`: 対象成果物の相対パスまたは不透明な識別子
- `target_revision`: 評価対象revision

不足時は案件を作らず`invalid-input`で拒否する。baseline変更は`adjudicate`だけが登録でき、変更後は影響するFindingを`requires-rereview`とする。Reviewerは次の`review`で、全対象Findingについて`rereviews`へ再評価結果、根拠、Evidenceを記録し、`verified`、`open`、`unverified`へ遷移させる。再評価が未完了のまま次工程へ進めない。

## 5. FindingとEvidence

Findingには、`finding_id`、`classification`、`severity`、`requirement_ref`、`observed_fact`、`impact`、`expected_state`、`verification_method`、`evidence_refs`を要求する。

分類は次の4つとする。

- `requirement-violation`
- `purpose-risk`
- `evidence-gap`
- `improvement-proposal`

Evidenceには`evidence_id`、`level`、`target_revision`、`method`、`result`、`path`または`summary`、必要な場合は`sha256`を記録する。管理対象ファイルは案件ディレクトリ内だけを許可する。

## 6. 変更範囲の照合

Ownerは`implementation_authorization.allowed_targets`を指定する。Implementerは`changed_targets`を申告する。Reviewerは`verify.change_observation.observed_changed_targets`を独立Evidenceから登録する。

- 観測対象にある申告外変更: `undeclared-change-detected`
- Owner許可外の変更: `unauthorized-change-detected`
- 申告したが観測できない変更: `unverified`
- 観測範囲外: 安全と推測せず`unverified`

Git観測はtrackedのstaged／unstaged、untracked、deleted、renamedを対象とする。ignoredとsubmodule内部はOwnerが別途有限manifestへ含めない限り保証範囲外とする。非Git案件はOwner指定の有限ファイル集合の前後SHA-256 manifestを使用する。

## 7. 状態遷移

```text
reviewer-action
  -> implementer-action | owner-adjudication
implementer-action
  -> reviewer-verification | owner-adjudication
reviewer-verification
  -> implementer-action | owner-adjudication
owner-adjudication
  -> implementer-action | held | accepted | accepted-with-risk | rejected
```

自動サイクルは`submit-response`から`verify`までを1回とし、3回でOwner裁定へ移す。未解決Findingに対する実装許可がない場合は、Reviewer検証後に3回を待たずOwner裁定へ移す。3回到達後に`rework-requested`を行う場合、Ownerは正の`additional_cycles`を明示して追加上限を設定する。`held`は終端状態ではなく、Ownerが後続の`adjudicate`で再開できる。

`accepted-with-risk`には、非空の`residual_risks`、`conditions`、期限または再確認トリガーを表す`review_trigger`を必須とする。

## 8. エラーと終了コード

| 終了コード | 意味 |
|---:|---|
| 0 | 成功 |
| 2 | 契約、Role、状態、handoff、revisionの拒否 |
| 3 | 入出力またはEvidence参照不能 |
| 4 | 予期しない内部エラー |

拒否結果は`state_changed: false`と、安定した`error_code`、修正方法を返す。

## 9. 停止境界

- 更新前: 全入力、Role、handoff、revision、Evidence、変更範囲を検証し、不一致なら書き込まない。
- 更新中: 同一ディレクトリの一時ファイルへ完全なJSONを書き、`fsync`後に原子的置換する。
- 更新後: 新revisionを再読込できることを確認する。保存失敗は成功扱いにしない。
- `case.json`への書込み前には`case.json.bak`へ直前revisionを保存する。書込み失敗時は`case-write-failed`または`case-backup-failed`として返し、更新成功を示さない。

`status`は常に読取り専用で、存在しないcase-rootやcaseを作成しない。必要時のみ既存案件ディレクトリ内に非正本の`resume.md`を生成する。
