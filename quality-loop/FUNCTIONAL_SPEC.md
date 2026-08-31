# Quality Loop 機能仕様 (v1.3.0)

## 1. 目的

単一の案件正本 `case.json`、明示的な handoff、決定論的信号機要約 `resume.md` を用いて、人間Owner、Reviewer (AI-2)、Implementer (AI-1) の3者協働QMSループを実行する。

1. **Quality Intent**: Ownerが目的、想定用途（`intended_use`）、リスク文脈（`risk_context`）、要求・受入基準を固定する。
2. **Proportional QA Review**: Reviewerが要求とEvidenceからFindingを作成し、比例性（Proportionality）に基づきPlan要否を判定する。
3. **Plan Before Fix**: Critical/Highは原則必須、Mediumはリスク・文脈に応じてAdaptive、Lowは原則direct responseとする。Plan-required Findingは、そのFinding自身のPlan承認後にResponseを提出する。
4. **QA Self-Correction**: Implementerの反証Evidenceにより、Reviewerは指摘を撤回（`finding-withdrawn`）または提案へ格下げ（`converted-to-suggestion`）できる。
5. **Independent Verification & Early Risk Assessment**: Reviewerが修正結果を別Invocationで独立検証し、申告外変更を検知する。追加修正による便益が小さく環境制約等がある場合、未解決Critical指摘がなければ、3サイクル反復を待たずに理由付き（`early_risk_rationale`）で早期リスク評価へ移行できる。
6. **Final Risk Assessment**: サイクル上限または残余リスク存在時、Reviewerが構造化リスク評価（`final-risk-assessment.md`）を作成する。
7. **Human Adjudication & Traffic Light**: 人間Ownerが受入、条件付き受入、保留、却下、再作業を2段階（dry-run → confirm）で最終裁定する。Owner最終裁定後はサイクル数にかかわらず決定状態が最優先される（`accepted` ➔ 🟢 緑、`accepted-with-risk` ➔ 🟡 黄）。

## 2. 公開seam (9 operations)

Python APIの `QualityLoop` と CLI の 9操作だけを公開seamとする。すべての結果はJSONで表現され、`status`、`case_id`、`case_revision`、`state_changed`、`next_role`、`next_action`、`handoff` を含む。

| 操作 | Role | 前handoff | 主な成果 |
|---|---|---:|---|
| `create-case` | Owner | 不要 | revision 1、Quality Intent固定、Reviewer向けhandoff |
| `review` | Reviewer | 必須 | Finding作成、Plan要否判定、次工程handoff |
| `submit-plan` | Implementer | 必須 | Response Plan提出（コード変更なし） |
| `review-plan` | Reviewer | 必須 | Plan評価合意（`plan-accepted` / `plan-rejected` / `finding-withdrawn`） |
| `submit-response` | Implementer | 必須 | 許可範囲内での修正提出とEvidence記録 |
| `verify` | Reviewer | 必須 | 独立検証、変更範囲照合、自己訂正 |
| `assess-risk` | Reviewer | 必須 | 最終リスク評価（`final-risk-assessment.md` 派生生成） |
| `adjudicate` | Owner | 必須 | 最終裁定（Go/No-Go/条件付き受入/再作業指示） |
| `status` | 読取り | 不要 | 決定論的信号機要約（`resume.md`）と最新Handoff取得 |

## 3. 固定安全条件

- `case.json` が唯一の正本（canonical state）。`resume.md` や `final-risk-assessment.md` は派生ビュー。
- baseline、実装許可、追加サイクル、最終リスク受容はOwnerだけが変更・裁定する。
- ReviewerとImplementerは同一Invocationで兼務しない。
- `verify` は対象 `submit-response` と異なるInvocationで行う。
- 古いrevision、誤Role、誤handoff、未知Finding、許可外変更は正本無変更で拒否する。
- Evidence不足は `unverified` または `evidence-gap` とし、合否を捏造・補完しない。
- `fix-submitted` は完了ではない。Reviewerの有効性確認後にOwnerが裁定する。
- Ownerの終端裁定（`accepted`、`accepted-with-risk`、`rejected`）は、dry-run確認後に `confirm: true` を指定しなければ記録しない。
- handoff受領確認、状態更新、次handoff発行を1回の原子的更新（atomic write + backup）にする。
- 同一 `operation_id` の再送は二重更新せず、初回結果を返す（Idempotency）。

## 4. 状態機械 (State Machine)

```text
created (Owner)
  -> reviewer-action (Reviewer: review)
reviewer-action
  -> implementer-plan (Implementer: submit-plan) [Plan required]
  -> implementer-action (Implementer: submit-response) [Direct response]
  -> owner-adjudication (Owner: adjudicate) [No findings]
implementer-plan
  -> reviewer-plan-review (Reviewer: review-plan)
reviewer-plan-review
  -> implementer-plan (Implementer: submit-plan) [Plan rejected]
  -> implementer-action (Implementer: submit-response) [Plan accepted]
  -> owner-adjudication (Owner: adjudicate) [All withdrawn]
implementer-action
  -> reviewer-verification (Reviewer: verify)
reviewer-verification
  -> implementer-plan (Implementer: submit-plan) [Unresolved Plan-required / cycle < limit]
  -> implementer-action (Implementer: submit-response) [Unresolved non-Plan-required / cycle < limit]
  -> reviewer-final-assessment (Reviewer: assess-risk) [Cycle limit / residual risk]
  -> owner-adjudication (Owner: adjudicate) [All resolved]
reviewer-final-assessment
  -> owner-adjudication (Owner: adjudicate)
owner-adjudication
  -> implementer-plan (Implementer: submit-plan) [rework-requested + pending Plan-required]
  -> implementer-action (Implementer: submit-response) [rework-requested + no pending Plan-required]
  -> held (Owner: 後続のadjudicateで再開可能)
  -> accepted | accepted-with-risk | rejected (Terminal)
```

## 5. エラーと終了コード

| 終了コード | 意味 |
|---:|---|
| 0 | 成功 |
| 2 | 契約、Role、状態、handoff、revisionの拒否 |
| 3 | 入出力またはEvidence参照不能 |
| 4 | 予期しない内部エラー |

すべての拒否結果は `state_changed: false` と、安定した `error_code`、具体的な `remediation` を返す。

## 9. 停止境界

- 更新前: 全入力、Role、handoff、revision、Evidence、変更範囲を検証し、不一致なら書き込まない。
- 更新中: 同一ディレクトリの一時ファイルへ完全なJSONを書き、`fsync`後に原子的置換する。
- 更新後: 新revisionを再読込できることを確認する。保存失敗は成功扱いにしない。
- `case.json`への書込み前には`case.json.bak`へ直前revisionを保存する。書込み失敗時は`case-write-failed`または`case-backup-failed`として返し、更新成功を示さない。

`status`は常に読取り専用で、必要時のみ非正本の`resume.md`を生成する。
