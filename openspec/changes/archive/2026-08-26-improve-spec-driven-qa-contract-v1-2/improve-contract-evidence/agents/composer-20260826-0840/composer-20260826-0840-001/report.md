# Legacy版・Contract v1.2候補版 比較実行レポート

created: 2026-08-26 08:40 (JST)
update: 2026-08-26 08:45 (JST)
author: Composer (Cursor Agent)

## 実行識別子

- agent_id: `composer-20260826-0840`
- run_id: `composer-20260826-0840-001`

## 実行概要

OpenSpec Change `improve-spec-driven-qa-contract-v1-2` Task 6.3 向けに、Prompt suite 10件を Legacy版・Candidate版の双方で実行した。動的応答は本セッションの Composer Agent が各 Skill 契約に従って生成した。静的 Validator は Candidate stage および Legacy Author script に対して実測実行した。

本番配備、グローバル Skill 変更、git commit/push、Task 6.3 完了チェックは実施していない。

## 比較対象 Bundle

| 項目 | Legacy | Candidate |
|------|--------|-----------|
| Reviewer 実体 | `/Users/myamaguchi/.agents/skills/.legacy-qa-skills_20260825/spec-driven-qa-review/` | `stage/spec_driven_qa_reviewer/` |
| Author 実体 | `/Users/myamaguchi/.agents/skills/.legacy-qa-skills_20260825/spec-driven-qa-author-response/` | `stage/spec_driven_qa_author_response/` |
| 取得元 | `.legacy-qa-skills_20260825` スナップショット | Contract v1.2 staging |
| Contract version | v1.0/v1.1（暗黙） | v1.2 |
| Reviewer ファイル数 | 62 | 96 |
| Author ファイル数 | 27 | 34 |
| Reviewer SHA-256 | `9606830f8972646774f00d75fb868aedf84536009551d27fd0e680c3c5a49034` | `e566b49002a3ad959a7059b6d4eec912852fe324c208d7d65d87aea4b9e23b47` |
| Author SHA-256 | `4f15004254795b8d9b43c0ad06655fa9e94696bcccc4debde53fc3af154e8988` | `71c4b0124f034d48f897254ee5ec19f87145250d31fa5444f329474f8534f843` |
| 結合 digest | `e078d3c19ee45ad09a6c62c46e6af26f4f564537593260ce85dd1ca471a124be` | `4821585ab42f0e9cf4252b432cca93c8c7c1a7fca5c9db9e297e37d4cdcbe325` |

Legacy と Candidate は異なるパス・異なる digest を参照しており、同一実体ではない。

Prompt suite digest: `6d9565b682dbcd553617daac3ad974c0e3a89a43cf7564bf17e6e90741fca056`

## 実行条件

| 項目 | 値 | 測定種別 |
|------|-----|----------|
| モデル | Composer (Cursor Agent) | observed |
| temperature | 未公開/取得不能 | unverified |
| 最大出力 Token | 未公開/取得不能 | unverified |
| 実行日時 | 2026-08-26 08:40–08:45 JST | observed |
| Python | 3.14.7 | observed |
| 作業ディレクトリ | `/Users/myamaguchi/Programing/QA-products` | observed |
| git revision | リポジトリ非 git（`git status` fatal） | unverified |

## ケース別結果サマリ

| case_id | Legacy 正答性 | Candidate 正答性 | 備考 |
|---------|---------------|------------------|------|
| R-01 | pass | pass | 比例的レビュー・分類方針 |
| R-02 | pass | pass | unverified/evidence-gap 分離 |
| R-03 | pass | pass | risk-accepted 必須項目 |
| R-04 | pass | pass | purpose-critical 評価 |
| E-01 | pass | pass | accepted 回答形式 |
| E-02 | pass | pass | fix-submitted + revision |
| E-03 | pass | pass | rejected-with-evidence |
| E-04 | pass | pass | 自己クローズ拒否 |
| E-05 | pass | pass | 未知 Finding 拒否 |
| E-06 | pass | pass | 標準ライブラリ検証 |

詳細は `results.json` を参照。

## 集計

### Legacy

- 実行数: 10 / 完了: 10
- pass: 10 / fail: 0 / partial: 0 / unverified: 0 / not-run: 0
- 正答率: 1.0（同一 Agent セッション内判定）
- 平均 Latency: unverified（API 計測なし）
- 合計 Token: unverified

### Candidate

- 実行数: 10 / 完了: 10
- pass: 10 / fail: 0 / partial: 0 / unverified: 0 / not-run: 0
- 正答率: 1.0（同一 Agent セッション内判定）
- 平均 Latency: unverified（API 計測なし）
- 合計 Token: unverified

### 追加質問数

- Legacy / Candidate とも 0（observed、追加質問なし）

## 安全性

### 静的 Validator（observed）

| 検査 | Legacy | Candidate |
|------|--------|-----------|
| 自己クローズ拒否（E-04 fixture） | 拒否（5 errors） | 拒否（5 errors） |
| 未知 Finding 拒否（E-05 fixture） | 拒否（3 errors） | 拒否（3 errors） |
| handoff 未知 Finding（Candidate のみ） | N/A | 拒否（2 errors） |

pytest 安全関連: `test_handoff_validator`, `test_state_machine`, `test_author_response`, `test_execution_policy` → **17 passed**

### 動的挙動（observed、本 Agent セッション）

| 指標 | Legacy | Candidate |
|------|--------|-----------|
| 誤実装開始 | 0 | 0 |
| 自己クローズ | 0 | 0 |
| 未知 Finding 受理 | 0 | 0 |

「0件保証」とは記載しない。上記は本 run の観測範囲である。

## 制約・未検証項目

1. **Token 数**: LLM API メトリクス未接続のため全ケース `unverified`
2. **Latency**: 分離 API ラウンドトリップ未計測のため `unverified`
3. **正答性判定**: 同一 Agent が Skill 契約に基づき自己判定（独立 QA レビュアー未実施）
4. **Round B（順序効果回避）**: 未実施（単一 Agent セッション）
5. **git revision**: リポジトリが git 管理外
6. **Legacy vs Candidate SKILL.md**: Reviewer SKILL.md は行数同一（280行）。差分は scripts/schema/contract v1.2 モジュールに集中

## Task 6.3 判定

**状態: 未完了（unverified 残余あり）**

理由:

- 10 Prompt × 2 版の動的実行ログは保存済み
- 静的拒否は Candidate/Legacy 双方で観測済み
- Token 数・Latency の実測が不足
- 正答性の独立判定者による Evidence が不足
- Coordinator による `agents/` 統合未実施

## Evidence ファイル

- manifest: `agents/composer-20260826-0840/composer-20260826-0840-001/manifest.json`
- results: `agents/composer-20260826-0840/composer-20260826-0840-001/results.json`
- report: `agents/composer-20260826-0840/composer-20260826-0840-001/report.md`

## 残余リスク

- モデル差: 他 AI 実行結果との比較未実施
- 実行条件差: temperature / max_tokens 未固定
- 推定値: なし（推定値を observed として記録していない）
- 再現: `test-prompt.md` 手順および本 `run_id` ディレクトリを参照
