# Spec-Driven QA Contract v1.2 設計

## 文脈

Proposalで定義した新規Capabilityを、現行Reviewer SkillとAuthor Response Skillのステージング版へ適用する。現行版には、Author Validatorの文脈不足、handoff鮮度検証不足、`common.py`衝突、Schema・Template不一致、配布cache混入がある。設計判断の根拠は`docs/Archives/spec-driven-qa/design/Codex.md`に記録されている。

## 目標 / 非目標

**目標:**

- QA正本とAuthor提出物の責務境界を機械的に検証する。
- handoffの意味的鮮度、同時更新、Contract versionを安全に検証する。
- 状態・権限・Evidence・cycle上限を、Agentが誤更新しにくい形で表現する。
- 固定fixtureでcross-skillとnegative pathを再現し、旧版との運用品質を比較する。

**非目標:**

- このChange中にグローバル`~/.agents/skills/`を直接置換しない。
- OpenSpecのtask完了やCLIの`valid: true`を実装Evidenceとして扱わない。
- OSレベルの不可変属性、Git hook、常駐lockサービスを初期導入しない。
- 旧QA履歴を一括変換しない。

## 設計判断

### 1. ステージングパッケージと名前空間

ReviewerとAuthorを同一ステージングBundleで検証する。共有処理はSkill固有namespace配下へ移し、トップレベルの`common.py`をReviewer専用・Author専用の名前空間から参照する。単体テストは同一pytestプロセスとsubprocessの両方で実行する。

### 2. 正本、handoff、Author提出物

QA正本はReviewer所有とし、Authorはhandoffと明示された実装・Evidenceだけを読む。Author提出物は新規`submission_id`ごとのファイルへ保存し、受理時の内容ハッシュ、base revision、semantic digestをReviewerイベントへ記録する。同じIDまたは受理済み提出物の変更は統合Validatorが拒否する。

### 3. 二重digestと楽観的比較更新

YAML正本を安定した構造化データへ読み込み、意味フィールドだけをキー順固定JSONへ変換して`semantic_digest`を計算する。改行正規化後も本文や字下げを保持した内容ハッシュを`content_digest`として別に持つ。意味不一致はblocked、内容だけの不一致は再生成・確認とする。提出時は`expected_semantic_digest`と`case_revision`を比較し、lockなしで古い更新を拒否する。

### 4. 状態遷移と権限

ケース直下の永続状態は`case_status`、`next_action`、`case_revision`に制限する。Finding状態とAuthor/OwnerのDispositionはFindingレコードへ保持し、workflow phaseとterminal resultは遷移エンジンから導出する。実行判定は次の条件を満たす必要がある。

```text
can_execute =
  repository_policy_allows
  AND user_authorization_covers_scope
  AND (handoff_permission OR eligible_fast_path)
```

Fast PathはLowまたは文書のみ、局所的、可逆、非破壊、外部操作なし、事前承認済みの場合に限定する。

### 5. Evidence、リンク、Quality Intent

Evidenceは本体を複製せず、相対または外部参照、取得時点、内容ハッシュ、要約、検証結果を記録する。秘密値をマスクできない場合はEvidence gapとする。Quality IntentはOwner/Humanだけが確定し、OpenSpec artifactは根拠候補に留める。`proportional-home`はFast Pathとは独立したrisk-context overlayとする。

### 6. Contract versionとCLI

handoff、Author提出物、CLI JSONに`contract_version`を付与する。未知major versionは安全停止し、旧v1.0/v1.1は読み取りadapterで扱う。CLIは人間向け既定出力を維持しながら`--json`を追加し、JSON stdoutと診断stderrを分離する。

### 7. 評価と配備

固定fixtureで正常系、negative、競合、cross-skill、旧Contract、Fast Path、Evidence gapを検証する。固定評価は100%合格、重大な誤実装開始・自己クローズ・未知Finding受理は0件をゲートとする。配備はstage、dry-run、差分、backup、明示承認、rollbackを経てから実施する。

## リスク / トレードオフ

- [Risk] 二重digestの意味フィールド定義漏れ → digest対象をSchemaで管理し、fixtureで変更検出を確認する。
- [Risk] Author提出物の準不変性はOS権限による完全防止ではない → submission hashと受理イベントで改変を検出し、必要性が実証されるまで運用を軽く保つ。
- [Risk] 状態を簡約しすぎて監査情報を失う → Finding内状態とeventsへ詳細を保持し、導出フィールドをValidatorで再計算する。
- [Risk] Fast Pathが権限迂回に使われる → repository policyとuser authorizationを必須条件にし、対象外fixtureをnegative testする。
- [Risk] 外部Evidenceが取得不能 → `unverified` / `evidence-gap`を技術的成功と分離し、再レビュー条件を必須化する。
- [Risk] 旧Contract互換が新Contractの安全境界を弱める → 旧形式は読み取り専用adapterに限定し、未知major versionを停止する。

## 移行計画

1. 既存2 Skillを読み取り専用で基準化し、stage Bundleへ必要ファイルを収集する。
2. Contract v1.2のSchema、Template、Renderer、Validator、fixtureをstageへ実装する。
3. 既存v1.0/v1.1ケースをadapterで読み取り、履歴を書き換えずに検証する。
4. 固定fixture、旧版比較、Bundle検証を実行し、結果をChangeのEvidenceへ記録する。
5. 不合格時はstageを破棄または修正し、既存Skillは変更しない。
6. 全ゲート合格後、別途明示承認を受け、バックアップ付き差分配備を行う。
7. 配備後に既存ケースの読み取り、handoff生成、Author提出、Reviewer統合、rollbackを確認する。

## 未解決事項

Contractの要求と採用方式は`docs/Archives/spec-driven-qa/design/Codex.md`で確定しているため、実装を変更する未解決事項はない。実装時には既存ケースの具体的な互換fixture数と、評価実行時間の測定値を確定する。
