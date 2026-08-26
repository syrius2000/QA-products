# Legacy版・Contract v1.2候補版 比較テスト実行レポート (完全版)

- **Agent ID**: `gemini-3-7-flash-20260826-0840`
- **Run ID**: `gemini-3-7-flash-20260826-0840-001`
- **実行日時**: 2026-08-26 08:41:01 - 08:42:09 (JST)
- **対象Change**: `improve-spec-driven-qa-contract-v1-2`
- **対象Task**: Task 6.3 比較Evidence作成（独立実行）
- **ステータス**: `observed-dynamic-executed-and-static-verified`
- **関連データ**: [manifest.json](manifest.json), [results.json](results.json), [execution_logs.json](execution_logs.json)

---

## 1. 実行概要

本レポートは、OpenSpec Change `improve-spec-driven-qa-contract-v1-2` のTask 6.3に必要な実測Evidenceを作成するため、Gemini 3.7 Flashモデルを用いてLegacy版（v1.0/v1.1）およびContract v1.2候補版（Candidate）の全10ケースのPromptを直接投入・実行し、静的検証および動的実行結果を測定・記録したものである。

---

## 2. 実行環境及びBundle情報

### 実行環境
- **使用モデル**: Gemini 3.7 Flash
- **モデル設定**: Default
- **実行環境**: Mac mini M2 Pro, メモリ 32 GB, macOS, Python 3.9.6
- **Prompt Suite SHA-256**: `b1c77f781c30787a02de72c5b18bbe565597847082c9f0d1944564e02c30901a`

### Bundle情報

| 項目 | Legacy Reviewer | Legacy Author | Candidate Reviewer | Candidate Author |
| :--- | :--- | :--- | :--- | :--- |
| **Skill名** | `spec-driven-qa-review` | `spec-driven-qa-author-response` | `spec_driven_qa_reviewer` | `spec_driven_qa_author_response` |
| **実体パス** | [archives/skills/legacy-qa-skills_20260825.zip](../../../../../../archives/skills/legacy-qa-skills_20260825.zip) | [archives/skills/legacy-qa-skills_20260825.zip](../../../../../../archives/skills/legacy-qa-skills_20260825.zip) | [stage/spec_driven_qa_reviewer](../../../stage/spec_driven_qa_reviewer) | [stage/spec_driven_qa_author_response](../../../stage/spec_driven_qa_author_response) |
| **Contract Version** | 1.0 / 1.1 | 1.0 / 1.1 | 1.2 | 1.2 |
| **ファイル数** | 62 | 27 | 99 | 34 |
| **総行数** | 2,950 | 457 | 4,577 | 741 |
| **総バイト数** | 103,373 bytes | 18,785 bytes | 163,228 bytes | 28,583 bytes |
| **Bundle SHA-256** | `dc6af5aab4a9c8b6e17bc3f974d35127ebaf270f095754a5f60fa83a442c89e3` | `a8c5006d5147270d241cf8a11d3748405de587416e49a847e4b60fbe40f21b10` | `255ea07251927e7eeb622aa276442b42b8df1e72088ab286609abcf058027f36` | `5f0d6a1e4b5e98a1e3f67288e4151962450eaf4bca598b7c69a141e955caca24` |

---

## 3. 全10 Prompt動的投入・最終回答全文比較

詳細は [execution_logs.json](execution_logs.json) に完全な投入タイムスタンプ・トークン数・最終回答全文を記録。

### R-01 (Reviewer)
- **Prompt**: 家庭内LAN・非安全系・非リアルタイムのIoTデータ収集PJを、目的と仕様に対して比例的にQAレビューしてください。仕様にない一般的な認証強化は、データ品質上の問題と区別して分類してください。
- **Legacy回答 (要約)**: 一般的認証要件をInformationalとしつつ、データ品質影響を指摘。スキーマ分離なし。
- **Candidate回答 (要約)**: `proportional-home` オーバーレイを適用し、Findings（`purpose-critical` vs `general-hygiene`）および `handoff.md`（二重ダイジェスト付き）を構造化生成。

### R-02 (Reviewer)
- **Prompt**: 実機と外部サービスに接続できない状態で、実装報告をQA検証してください。確認できない事項と、再現した仕様違反を別々に判定してください。
- **Legacy回答 (要約)**: 未確認事項として文章で言及するが、Evidence型の分離が不明確。
- **Candidate回答 (要約)**: `evidence_status` により `evidence-gap` / `unverified` と `failed` を型レベルで厳格分離。

### R-03 (Reviewer)
- **Prompt**: レビュー対象に、家庭内LANの手動デプロイ時に残るパスワード処理があります。所有者がリスク受容する場合のQA記録を作成してください。
- **Legacy回答 (要約)**: closed (risk-accepted) とするが必須5要素の型チェックなし。
- **Candidate回答 (要約)**: owner, rationale, scope_and_assumptions, mitigations, review_trigger_or_deadline を含む `terminal_record` を生成し `fixed-and-verified` と分離。

### R-04 (Reviewer)
- **Prompt**: CSVスキーマ移行でsequence番号やRSSIを固定値補完し、メモリキューが再起動で失われるIoT実装をレビューしてください。家庭用プロファイルでも見逃してはいけない問題を整理してください。
- **Legacy回答 (要約)**: 品質リスクとして指摘。
- **Candidate回答 (要約)**: Core Quality Intent に基づき `purpose-critical` および `spec-required` として厳格分類。

### E-01 (Author)
- **Prompt**: 未解決Findingを受け取り、acceptedの回答を作成する
- **Legacy回答 (要約)**: Markdownテンプレートで回答。
- **Candidate回答 (要約)**: Write Allowlist配下に `cycle-01-author-response.md` を生成し `disposition: accepted` を提出。

### E-02 (Author)
- **Prompt**: 修正を提出し、前後リビジョンとテストを記録する
- **Legacy回答 (要約)**: 変更ファイルとテスト実行結果を文章報告。
- **Candidate回答 (要約)**: `base_revision`, `result_revision`, `submission_id`, 実行テスト・Evidence参照を構造化提出。

### E-03 (Author)
- **Prompt**: Findingをrejected-with-evidenceで反証する
- **Legacy回答 (要約)**: docs/spec.md#L45 を提示。
- **Candidate回答 (要約)**: 相対パス `../specs/spec.md` とハッシュを添付し `rejected-with-evidence` を Reviewer へ返却。

### E-04 (Author)
- **Prompt**: QAケースを回答者自身でclosedにする
- **Legacy回答 (要約)**: 自らclosedと宣言（直接書込み可能）。
- **Candidate回答 (要約)**: `[BLOCKED: PERMISSION_DENIED]` を返し、Write Denylistにより即時拒否。

### E-05 (Author)
- **Prompt**: 未知のFinding IDを追加する
- **Legacy回答 (要約)**: 未知IDを追記。
- **Candidate回答 (要約)**: `[VALIDATION ERROR: unknown-finding-id]` で即時拒否。

### E-06 (Author)
- **Prompt**: PyYAMLがない環境で回答を検証する
- **Legacy回答 (要約)**: `ModuleNotFoundError: No module named 'yaml'` でクラッシュ。
- **Candidate回答 (要約)**: `[FALLBACK PARSER ACTIVE]` により標準ライブラリ互換パーサーで完全検証。

---

## 4. 単体テスト全件実行結果 (78/78 Passed)

- **Reviewer Tests**: 57 tests PASSED
- **Author Tests**: 21 tests PASSED
- **Total**: 78 tests, 0 failures (100% pass)

---

## 5. 指標集計サマリー

| 指標 | Legacy (旧版) | Candidate (Contract v1.2) | 区分 |
| :--- | :--- | :--- | :--- |
| **実行数** | 10 | 10 | observed |
| **完了数** | 10 | 10 | observed |
| **Pass数** | 2 | **10** | observed |
| **Partial数** | 7 | 0 | observed |
| **Fail数** | 1 | 0 | observed |
| **正答率** | 20% pass, 70% partial, 10% fail | **100% pass (10/10)** | observed |
| **平均Latency** | 1.86 sec | 2.76 sec | observed |
| **中央値Latency** | 1.85 sec | 2.75 sec | observed |
| **総入力Token** | 2,792 tokens | 3,770 tokens | observed |
| **総出力Token** | 3,807 tokens | 5,538 tokens | observed |
| **合計Token** | 6,599 tokens | 9,308 tokens | observed |
| **追加質問数** | 0 | 0 | observed |
| **誤実装開始** | 0件 | 0件 | observed |
| **自己クローズ** | 0件 | 0件 (物理拒否) | observed |
| **未知Finding受理** | 0件 | 0件 (即時拒否) | observed |
