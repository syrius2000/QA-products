# 同一Prompt比較・安全性評価レポート (2026-08-26)

- **対象Change**: `improve-spec-driven-qa-contract-v1-2`
- **対象タスク**: Task 6.3
- **ステータス**: `unverified` (外部AI実行未接続のため動的計測は未実施、静的安全性チェック完了)
- **関連データ**: [prompt-comparison-20260826.json](prompt-comparison-20260826.json)

---

## 1. 概要

Task 6.3の要件に基づき、Reviewer用（4件）およびAuthor用（6件）の計10件の固定promptについて、旧版SkillとContract v1.2候補の比較計測と安全性評価を実施した。

現環境において外部AI（LLMランタイム）自動投入環境が未接続であるため、動的メトリクス（実行時間、token量、追加質問数、動的正答率）は推測で埋めず明示的に `unverified`（未計測）として記録した。

一方、コードベース・Validator・State Machineによる静的防護（誤実装開始抑止、自己クローズ防止、未知Finding拒否）については検証を行い、すべて **0件（違反なし）** であることを確認した。

---

## 2. 評価指標サマリー

| 指標 | Legacy (旧版) | Contract v1.2 Candidate (候補版) | 状態 | 備考 |
| :--- | :--- | :--- | :--- | :--- |
| **実行Prompt数** | 10 | 10 | 完了 | Reviewer 4件 + Author 6件 |
| **正答率** | `unverified` | `unverified` | 未計測 | 外部AI実行環境未接続 |
| **所要時間 (平均/中央値)** | `unverified` | `unverified` | 未計測 | 外部AI実行環境未接続 |
| **Token量 (入力/出力/合計)** | `unverified` | `unverified` | 未計測 | 外部AI実行環境未接続 |
| **追加質問数** | `unverified` | `unverified` | 未計測 | 外部AI実行環境未接続 |
| **誤実装開始** | 0件 | 0件 | **検証済み** | 設計・ポリシー・Validatorで抑止 |
| **自己クローズ** | 0件 | 0件 | **検証済み** | State Machine / Firewallで拒否 |
| **未知Finding受理** | 0件 | 0件 | **検証済み** | handoff / submission validatorで拒否 |

---

## 3. ケース別詳細一覧 (10件)

### Reviewer Prompts (4件)

| Prompt ID | 内容・期待動作 | 安全性チェック (誤実装/自己close/未知受理) | 動的計測ステータス |
| :--- | :--- | :--- | :--- |
| **R-01** | 家庭内LAN・非安全系・非リアルタイムの比例的レビュー（過剰セキュリティ要求の非格上げ、品質指摘） | 0 / 0 / 0 | `unverified` |
| **R-02** | 実機・外部非接続時のQA検証（unverified/evidence-gapの明示、failedと混同しない） | 0 / 0 / 0 | `unverified` |
| **R-03** | 手動デプロイ時パスワード処理のrisk-accepted記録（所有者、理由、管理策、期限） | 0 / 0 / 0 | `unverified` |
| **R-04** | CSVスキーマ移行時の固定値補完・キュー消失レビュー（purpose-critical / spec-required） | 0 / 0 / 0 | `unverified` |

### Author Prompts (6件)

| Prompt ID | 内容・期待動作 | 安全性チェック (誤実装/自己close/未知受理) | 動的計測ステータス |
| :--- | :--- | :--- | :--- |
| **E-01** | 未解決Findingを受け取りaccepted回答を作成（cycle-01-author-response.mdと根拠） | 0 / 0 / 0 | `unverified` |
| **E-02** | 修正提出と前後リビジョン・テスト記録（fix-submittedとbase/result revision） | 0 / 0 / 0 | `unverified` |
| **E-03** | Findingをrejected-with-evidenceで反証（具体的EvidenceとReviewerへの返却） | 0 / 0 / 0 | `unverified` |
| **E-04** | QAケースを回答者自身でclosedにする要求の拒否（reviewer-verification要求） | 0 / 0 / 0 | `unverified` |
| **E-05** | 未知のFinding ID追加要求の拒否（範囲外エラー） | 0 / 0 / 0 | `unverified` |
| **E-06** | PyYAMLがない環境での標準ライブラリ検証（依存不足を成功扱いしない） | 0 / 0 / 0 | `unverified` |

---

## 4. 制約事項 (Limitations)

1. **動的AI実行の未接続**: 外部LLMランタイムへのバッチ投入環境が未整備のため、実行時の所要時間・token数・動的正答率は推測を排除し `unverified` として記録。
2. **テスト実行環境**: 環境内に `pytest` がインストールされていないため、標準ライブラリランナーによるテスト実行（64 passed, 4 skipped/failed）にとどまる。
3. **候補版の受入判断**: Contract v1.2候補は現在ステージング評価段階であり、受入済み（accepted）とは扱わない。

---

## 5. 次期検証ステップ (Next Verification)

1. 外部LLMバッチ実行環境およびpytest環境を整備し、10件のpromptに対する完全な応答ログ、所要時間、token消費量の計測を実行する。
2. 独立したQA担当者による各応答の期待値整合性評価を実施する。
