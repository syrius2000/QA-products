# QA機能完全互換性とLegacy互換性の検証提案

created: 2026-08-27 00:02 (JST)
update: 2026-08-27 01:44 (JST)
author: Codex (GPT-5)

## なぜ必要か（Why）

ReviewerとAuthorの各Skillは、ライフサイクル、提出権限、Evidence境界、semantic/content digest分離を個別Changeで実装し、QA-0006とQA-0007で受入済みまたは残余リスク付き受入となった。しかし、これまでの検証は各Changeの契約・拒否動作が中心であり、旧130ファイルに存在した公開・実行可能機能が、現在のステージング版で欠落なく利用できることを一つの正本で証明できていない。

そのため、外部Skill環境への配備を行う前に、旧版を明確に隔離したうえで、Legacy、Contract v1.2候補、コンパクト版の三版を同一条件で比較する。静的テストの合格、`valid: true`、単一モデルの動的回答を互換性の証明と混同せず、観測済み・未検証・意図的差分を分離した受入判断を可能にする。

## 変更内容（What Changes）

- 旧版Reviewer／Authorを明示的なLegacy Bundleとして隔離し、候補版・コンパクト版とパス、Manifest、digestを分離して固定する。
- 旧130ファイルから公開または実行可能な43機能IDを抽出し、機能名、入口、引数、終了コード、JSON必須項目、状態変化、副作用、対応版、Evidenceを記録する機能台帳を作成する。
- 同一のgolden、negative、cross-skill、Legacy互換、サイズ計測fixtureを三版へ適用し、ReviewerとAuthor双方のCLIおよびSkill入口を比較する。
- 旧CLI引数、終了コード、構造化出力、契約フィールド、既存QAケースの読み取り互換性を検証し、差分を機械的に報告する。
- 差分レポートを「未実装・欠落」「仕様上の意図的非互換」「診断文・表示形式のみの差分」に分離し、説明のない欠落を合格扱いにしない。
- 版ごとの適用可能性を`observed`、`not-applicable`、`evidence-gap`で記録し、`not-applicable`をLegacy完全互換や安全契約合格へ昇格させない。
- Reviewerの独立性、Authorの自己クローズ拒否、未知Finding拒否、stale digest拒否、Evidence境界、Workspace境界を三版比較の安全性指標として再確認する。
- 実行ログ、入力Prompt、出力、終了コード、所要時間、Token情報、Manifest、digestをAgent単位・Run単位のEvidenceへ保存する。取得できないLLM実測値は`unverified`または`evidence-gap`として記録する。
- 合計サイズの目標値は、テスト・仕様・最小完全fixture・安全境界を削らずに1,760行以下を目安とし、サイズ削減だけで互換性を主張しない。
- 独立QAと人間裁定が完了するまで、外部Skill配置、旧版削除、commit、push、既存正本の無断更新を行わない。

## Capability（能力）

### 新規Capability（New Capabilities）

- `spec-driven-qa-capability-parity`: Reviewer／Authorの公開・実行可能機能台帳、Legacy・候補版・コンパクト版の三版比較、互換性判定、差分分類、再現可能なEvidenceを定義する。

### 変更する既存Capability（Modified Capabilities）

- なし。既存の`spec-driven-qa`、`reviewer-verification-integrity`、semantic/content digestの契約を緩和または置換せず、既存契約を満たす実装が旧公開機能を保持しているかを新しい検証Capabilityとして追加する。

## 影響範囲（Impact）

- `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/`配下の仕様、設計、タスク、三版Bundle、機能台帳、fixture、比較ハーネス、Evidence。
- アーカイブ済みの`compact-spec-driven-qa-skills`、`improve-spec-driven-qa-contract-v1-2`、`reviewer-verification-integrity-hardening`、`separate-semantic-content-digests`が確定した契約・残余リスクの参照元となる。
- Reviewer Changeのライフサイクル／CLI互換と、Author Changeの提出／検証／依存欠落フォールバックを回帰対象とする。QA-0006はdigest分離により`accepted-with-residual-risk`でクローズされ、QA-0007は67テストと5独立プローブを根拠に同状態で受入された事実をEvidence基線として扱う。
- 実行時依存は標準ライブラリ中心とし、pytestや外部LLM環境の有無を結果へ明記する。外部AIによる正答率、Latency、Token量は実測時だけObservedとして扱い、理論推定値でTask完了や本番配備を判定しない。
- 配備先の`~/.gemini/config/skills/`等の外部環境は対象外であり、三版互換性の独立QAと後続の配備Changeを分離する。
