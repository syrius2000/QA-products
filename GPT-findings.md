# Spec-Driven QA Skill 比較・改善 Finding

created: 2026-08-25 18:05 (JST)
update: 2026-08-25 18:52 (JST)
author: Codex (GPT-5) / Antigravity

## 結論

`spec-driven-qa-qms-v1.1.0`をそのまま採用するのではなく、QMS版の運用設計と、現在`~/.agents/skills/`にある2つのSkillの文脈検証を統合した新しい版を作成することを推奨する。

より良いSkillを作成できる可能性は高い。ただし、改善の主張はファイル数・理念・単体テスト数ではなく、実際のQAケースを用いたend-to-end評価、誤った権限移譲の拒否、Authorの自己クローズ拒否、handoffの鮮度検出、再レビューの精度で確認する必要がある。

## 比較対象

| 区分 | パス | 役割 |
|---|---|---|
| QMS版 | `/Users/myamaguchi/Downloads/spec-driven-qa-qms-v1.1.0/.agent/skills/` | Quality Intent、handoff、Plan Before Fix、最終リスク裁定を含む配布Bundle |
| 現行Reviewer | `/Users/myamaguchi/.agents/skills/spec-driven-qa-review/` | 独立QAレビュー、Finding、Verification、既存QAケースの検証 |
| 現行Author | `/Users/myamaguchi/.agents/skills/spec-driven-qa-author-response/` | Author Responseと修正提出、自己クローズ防止 |

## 採用すべき長所

### QMS版から採用するもの

- Quality IntentをHuman/Ownerの責務として明示し、AI-1が自己都合で品質水準を下げず、AI-2も理論上の完全性を要求しない原則。
- Medium以上のmaterial Findingに対するResponse PlanとReviewerの計画確認。
- `handoff.md`から次のActor、Skill、Workflow、実装許可、対象Findingを復元し、人が内部状態を記憶しなくてよい運用。
- ReviewerがEvidenceによりFindingを撤回、downgrade、suggestion化できる設計。
- 残余リスクの受容要求と最終リスク評価を分離する設計。

### 現行版から保持・強化するもの

- Author ResponseをQAケースと`findings.yaml`に突合し、未知Finding、未回答Finding、closed case、`fix-submitted`なのにresult revisionがない状態を拒否するValidator。
- `handoff.md`を正本から再生成して鮮度を比較する考え方。
- `proportional-home`にある家庭内LAN・非安全系・低資源IoT向けの具体的な比例性ルール。
- `unverified`と`failed`、技術判定とOwnerのリスク裁定を分けるルール。
- 単一cycle・複数cycleを含む完全なQAケース例。

## P0: 実装前に直すべき契約・検証問題

### F-01: Authorの権限境界と読取り・書込みAllowlistの定義

QMS版の`validate_author_response.py`は応答ファイルのみを受け取るため、QAケース、handoff、Finding集合、権限、round、revisionと突合しない。
一方、AuthorがQAケースの正本ファイル群（`findings.yaml`, `review.md`, `events.jsonl`）を直接変更できると独立QAの境界が破壊される。

実測では、次の不正状態がすべてValidatorを通過した。

- 存在しないQAケースIDとFinding ID。
- `fix-submitted`なのに`result_revision: null`。
- implementation responseなのに`implementation_permission: false`。

改善案（読取り・書込みの厳格なAllowlist化）:

1. **Authorの読取り可能範囲 (Read Allowlist)**:
   - 公開契約: `docs/ADR/QA/QA-*/handoff.md`（明示された対象Finding、要求されるResponse Type、実装許可、base revision）
   - 実装コンテキスト: 対象ソースコード、単体テスト、実行ログ、Evidence
   - 参照コンテキスト: OpenSpec、ADR、仕様書
2. **Authorの書込み可能範囲 (Write Allowlist)**:
   - `docs/ADR/QA/QA-*/cycles/cycle-NN-author-response.md` または `author-submissions/` 配下のみ
3. **正本への書込み絶対禁止 (Write Denylist)**:
   - `review.md`, `findings.yaml`, `traceability.yaml`, `events.jsonl`, Finding Severity, Case Closureへの直接書込みは禁止。Author Response提出後、Reviewerが正本へ反映・検証する二段階とする。
4. **Validatorの突合検証**:
   ```text
   validate_author_response.py <qa-case-dir> <response-file>
   ```
   Author Responseが `handoff.md` の指示（Target Findings, Revision, Permission）と厳格に整合しているかを機械検証する。

### F-02: handoffの鮮度と整合性（semantic/content digest＋楽観的比較更新）

QMS版は`handoff.md`を派生物と定義するが、Validatorは必須フィールドの有無を主に確認するだけである。また、単純なRaw SHA-256比較では改行コードや無害な空白変更による偽陽性ブロック（False Block）が発生する。

改善案:

- **二重ダイジェストの導入**:
  - `content_digest`: 正本ファイル群のLF正規化テキストハッシュ（インデントや本文空白は保持）。不一致時は「再生成要求（stale-warning）」として扱い、最新正本からhandoffを再描画。
  - `semantic_digest`: Finding ID、Severity、Status、Permission、Round、Revisionなどの構造化キー情報のハッシュ。不一致時は「不正なケース改ざん」として `blocked: inconsistent-qa-state` で安全停止。
- **楽観的比較更新 (Optimistic Concurrency Control)**:
  - ケース更新時は `expected_source_digest` の比較更新を行い、他者による先行更新があれば上書きせず正本を再読込してReviewerへ返す。
  - lockファイルの強制削除は、所有者確認と明示承認なしに行わない。

### F-03: 状態語の責務分離（概念6軸モデルと永続状態3軸の簡約）

QMS版ではcase status、workflow phase、Finding status、Author disposition、Owner disposition、terminal resultが部分的に重複し、エージェントが手動で6項目を整合させようとすると状態爆発や誤更新を招く。

改善案:

1. **概念6軸モデル（論理仕様として保持）**:
   - `case_status`, `workflow_phase`, `finding_status`, `author_disposition`, `owner_disposition`, `terminal_result`
2. **永続化フィールドの最小化（LLMの認知負荷軽減）**:
   - ケース全体レベル: `case_status`（大状態）、`next_action`（次の工程）、`case_revision` の3軸のみを永続化。
   - Findingレベル: 各Findingレコード内に `finding_status`（Reviewer技術状態）、`author_disposition`（Author回答）、`owner_disposition`（Owner裁定）をカプセル化。
   - `workflow_phase` や `terminal_result` はケース状態とFinding状態から決定論的に導出（自動算出）し、Agentによる手作業の整合を不要とする。

### F-04: 実行可否判定の簡約と厳格なFast Path契約

handoffの`implementation_permission: true`はQAワークフロー上の許可にすぎず、リポジトリ固有の承認やユーザー権限を迂回してはならない。一方で、すべての軽微修正に過剰な承認を要求すると開発速度が失われる。

改善案（簡約された実行可否判定式）:

```text
can_execute =
  repository_policy_allows
  AND user_authorization_covers_scope
  AND (handoff_permission OR eligible_fast_path)
```

`eligible_fast_path` の成立条件（すべてを満たす場合のみ有効）:
- **Severity**: Low 指摘またはドキュメント/コメント修正のみ
- **局所性**: 単一ファイルまたは限定されたスコープ内
- **可逆性・非破壊性**: 既存データを破壊せず、容易にロールバック可能
- **外部操作なし**: 外部ネットワーク通信、権限昇格、インフラ変更を含まない
- **事前承認範囲内**: ユーザーが事前に明示許可した作業範囲内にあること

上記を満たさない修正、または Medium / High の Finding は、必ず Reviewer による Response Plan 合意を経てから実装に着手する。

## P1: パッケージ品質と互換性の問題

### F-05: 2Skillを同一pytestプロセスで実行すると失敗する

QMS版はReviewer、Authorともに`scripts/common.py`を持つ。同一pytestプロセスではモジュール名が衝突し、テスト収集エラーとなった。

- Reviewer単体: `6 passed`
- Author単体: `8 passed`
- 2Skill同時: ImportErrorにより失敗

改善案: `review_common.py`と`author_common.py`へ分離するか、固有namespaceを持つPython packageとして実装する。Bundleテストでは2Skillのtestsを同一プロセスとsubprocessの両方で実行する。

### F-06: Schema、Template、Validatorが同じ契約を実行していない

例としてQMS版Schemaはseverityを小文字enumとする一方、TemplateとExampleは`Medium`、`High`を使用する。現状ではJSON Schemaを実行していないため不一致が検出されない。

改善案:

- enumを小文字へ統一する。
- Schema validationをpackage validationに組み込む。
- 標準ライブラリのみを維持するなら、必要最小限の構造Validatorを実装し、JSON Schemaは開発時の追加検証に使う。

### F-07: Bundle Validatorと回帰評価ハーネス (run_evals.py) の不足

QMS版の`validate_bundle.py`はversion/contract一致とManifestを確認するのみで、2Skill間の実行互換性、cross-contract、テスト、exampleのE2E整合性、および偽陽性・競合・Fast Path拒否の回帰試験を実施しない。

改善案:

- **自動回帰テストハーネス (`run_evals.py`) の導入**:
  - モックQAケースFixture（単一サイクル、複数サイクル、Plan-Review、Fast-Path、Adjudication等）を用いた決定論的E2Eテスト。
  - **Negative Test スイートの完備**:
    - Stale handoff（`content_digest`差異での再生成要求、`semantic_digest`差異での停止）
    - 偽のFinding ID提出の拒否
    - 未許可実装（`implementation_permission: false` でのコード修正）の拒否
    - Fast Path不適合（Medium/High指摘での即時修正）の拒否
    - Author自己クローズの拒否
    - `expected_source_digest` 競合時の上書き拒否
- **Bundle Validatorの必須ゲート化**:
  - package manifest検証
  - Python構文検証（標準ライブラリのみ）
  - Reviewer/Author単体テスト
  - 2Skill同一プロセス＆subprocess両方での統合テスト
  - `run_evals.py` 全件パス

### F-08: インストール先とステージング配備の安全性規則

QMS版の配布先は`.agent/skills`だが、この環境の正本は`.agents/skills`である。また、既存環境を無条件に上書きすると進行中タスクや既存キャッシュを破壊する恐れがある。

改善案:

- **ステージング環境での事前評価（Staging Gate）**:
  - global skill（`~/.agents/skills/`）へ直接配備する前に、独立したstage作業ディレクトリ（例: `/tmp/qa-skill-stage` または `build/`）でBundleを組み立て、全単体テスト・E2Eテスト・`validate_bundle.py` が100%パスすることを確認する。
- **既存キャッシュ・設定の保護**:
  - ユーザー環境の既存キャッシュや履歴を無断削除・初期化しない。
  - 配布Manifestから一時ファイル（`__pycache__`, `.pytest_cache`, `.pyc`）を除外し、クリーンな成果物のみを配置する。
- **安全な本番反映**:
  - dry-run、差分表示、バックアップ作成、明示承認を経てから `~/.agents/skills/` 配下を更新する。

### F-09: OpenSpecとのネイティブ相互運用が不足している

現行の`adapters/openspec.md`はOpenSpec artifactの発見・中立モデルへの対応付けを定義するが、QAケース初期化時に対象Changeを固定し、Purpose、Spec、Plan、Tasksを再現可能に取り込む契約はない。

改善案:

- `--openspec-change <change-name>`を優先し、指定がない場合の自動選択は、明示対象に一致するactive changeが一意なときだけにする。archive済みChangeを自動選択しない。
- `proposal.md`、`specs/`、`design.md`、`tasks.md`、main specの実パス・revision・digestをQA baselineへ記録する。
- `openspec validate`、`openspec status`、task checkboxは構造状態またはAuthor Claimとして扱い、実装・テスト・実行時Evidenceの代わりにしない。
- OpenSpec artifactはQuality Intentの候補・根拠であり、Human/Ownerが定めるQuality Intentを自動更新しない。
- 既存の`adapters/openspec.md`を契約文書として維持し、機械的収集は`collect_openspec_context.py`のような独立scriptへ分離する。

### F-10: QA記録のリンク可搬性を強制していない

QA report、handoff、final risk assessment、YAMLのEvidence参照にリポジトリ内絶対パスや`file://` URLが混入すると、別checkout、CI、別Agent環境で証拠追跡が切れる。

改善案:

- リポジトリ内文書へのMarkdownリンクとYAML参照は相対パスを必須にする。
- `file://`を拒否する。
- リポジトリ外Evidenceは絶対パスまたはURLを許容するが、外部参照であることを明示する。全絶対パスを一律に拒否しない。
- legacy caseは初回から破壊的に失敗させず、warningから開始して移行計画でerrorへ昇格する。

### F-11: Contract v1.2への移行互換性が未定義である

Contract v1.2で状態語、handoff、Validatorを強化すると、既存のv1.0/v1.1 QAケースが検証不能になるおそれがある。履歴を新形式へ一括書換えすると、監査証跡も損なう。

改善案:

- v1.0/v1.1は読み取り互換を維持する。
- 既存cycle、Finding、eventsを自動書換えしない。
- migrationはdry-run、差分表示、backup、明示承認を必須とする。
- 移行が必要なケースは`legacy-readonly`または`migration-required`として明示し、新Contractのcaseと混同しない。

## P2: 運用性能を実証する評価計画

現状の`evals.json`は期待値の宣言であり、with-skillとbaselineを比較した性能証拠ではない。新しい版では `run_evals.py` を通じて次を自動検証する。

| 評価対象 | 合格条件 |
|---|---|
| 短い初回レビュー指示 | QAケースとhandoffを正しく作成し、スコープを拡大しない |
| 短い再点検指示 | 一意なactionable caseを選び、正しいworkflowへ進む |
| Medium/High Finding | Authorが承認前に実装せず、Response Planを返す |
| 偽のFinding ID | Validatorが拒否する |
| `fix-submitted` | result revisionとEvidenceがなければ拒否する |
| stale handoff (content) | `content_digest` 不一致を検知し再生成要求を出す |
| stale handoff (semantic)| `semantic_digest` 不一致で `blocked: inconsistent-qa-state` で停止する |
| 自己クローズ要求 | Authorが拒否しReviewerへ返す |
| Fast Path適用 | Low・局所・可逆・非破壊かつ承認範囲内のみ即時修正を許可する |
| Fast Path拒否 | Medium/Highまたは範囲外の即時修正要求をブロックする |
| home-lan-iot | 過剰なEnterprise要求をFormal Findingにしない一方、データ完全性を見逃さない |
| round上限到達 | 最終リスク評価とHuman decisionへ移行し、無限往復しない |
| OpenSpec Bridge | 指定Changeだけをbaselineへ取り込み、task完了や`valid: true`を実装証拠と誤認しない |
| 同時更新競合 | `expected_source_digest`不一致で上書きを拒否し、正本再読込へ戻る |
| 相対リンク | リポジトリ内参照を相対化し、`file://`を拒否する。外部Evidence参照は明示して保持する |
| legacy case | 旧Contractを読み取り可能にし、無断の履歴書換えを行わない |

評価は各caseについて旧版と改善版を同じpromptで比較し、正答率、誤った実装開始率、誤trigger、token量、所要時間、Humanへの追加質問数を記録する。

### 構造化CLI契約

AIがプレーンテキストを推測で解釈しないよう、探索・検証・handoff生成のscriptには`--json`を設ける。全scriptを一律にJSON専用にするのではなく、人間向け既定出力を残しつつ次を固定する。

- JSONはstdoutだけに出力し、診断はstderrへ出す。
- 共通フィールドは`schema_version`、`ok`、`status`、`case_id`、`next_action`とする。
- `valid`、`invalid`、`blocked`、`ambiguous`、`error`とexit codeの対応を契約化する。
- JSON、event、handoffに秘密値・トークン・認証情報を出力しない。

## 推奨構成

```text
spec-driven-qa-review
  - Quality Intent / risk context
  - canonical state machine
  - Finding / plan review / verification
  - handoff render and validate
  - final risk assessment
  - OpenSpec adapter contract and context collector

spec-driven-qa-author-response
  - handoff consumer
  - response plan
  - approved-scope implementation response
  - evidence-backed challenge
  - risk acceptance request
  - case-context validation
```

Reviewer Skillを契約と状態遷移の正本とし、Author SkillはReviewer所有のFinding、severity、verification、closureを変更しない。`proportional-home`は`lite/standard/strict`とは別のrisk-context overlayとして保持する。

## 実装順序

1. Contract v1.2の状態語、所有者、遷移表、effective permission、旧Contractの読み取り互換を確定する。
2. Validator、handoff digest、`expected_source_digest`による競合拒否を実装し、現行Skillの厳格な文脈検証を回復する。
3. QMS版のQuality Intent、Plan Before Fix、Final Risk Assessmentを統合する。
4. OpenSpec Bridge、相対リンク検証、構造化CLI JSON契約を追加する。
5. Schema、Template、Script、Exampleを同一contractへ揃える。
6. 完全QAケースによるE2E／negative／cross-skill／legacy migration testを追加する。
7. stage用コピーでBundleを評価し、明示承認後にのみ`.agents/skills`または`.codex/skills`へ安全に配備する。
8. trigger精度と実運用品質を旧版との比較評価で確認する。

## 現時点の判定

改善版を作成できる見込みは高い。特に、QMS版の人間中心の品質裁定と、現行版の具体的な検証安全性は補完関係にある。

ただし、QMS v1.1.0の単純導入、または現行2Skillの単純な継ぎ合わせは行わない。Contract v1.2を先に固定し、ValidatorとE2E評価を先行させることが、性能と安全性を同時に上げる条件である。
