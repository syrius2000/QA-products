# 実装計画書 統合アーカイブ要約 (001〜004)

- **作成日時**: 2026-08-25 23:20 (JST)
- **更新日時**: 2026-08-25 23:20 (JST)
- **対象期間**: 2026-08-24 〜 2026-08-25
- **アーカイブ元ファイル**:
  - `implementation_plan_001_0824.md` (Spec-Driven QA引き継ぎ拡張および作成者回答Skill実装計画)
  - `implementation_plan_002_0825.md` (spec-driven-qa-review比例的QAゲート改善実装計画)
  - `implementation_plan_003_0825.md` (旧QAスキル退避および開発版スキルのグローバル配置計画)
  - `implementation_plan_004_0825.md` (Cursor会話関連ファイルの安全クリーンアップ計画)

---

## 1. エグゼクティブサマリー

本ドキュメントは、2026年8月24日から25日にかけて策定・実施された実装計画書（Plan 001〜004）の成果、決定事項、技術的要点を集約・統合したアーカイブ記録である。

期間中、主に以下の4つの主要マイルストーンが達成された：
1. **QA引き継ぎ成果物（`handoff.md`）の標準化と、作成者回答専用スキル（`spec-driven-qa-author-response`）の新設**（Plan 001）
2. **家庭内LAN・非安全系・廉価IoT機器を対象とした「比例的QAゲート」の導入と、過剰ブロッカー化の防止**（Plan 002）
3. **旧QAスキルの安全なzip退避と、新開発版スキルのグローバル環境への検証付き配置手順の確立**（Plan 003）
4. **直近30日超の旧Cursor会話関連ファイルの安全なクリーンアップと設定破壊防止ガードレールの適用**（Plan 004）

---

## 2. 各計画書の要約と決定事項

### 2.1 Plan 001: Spec-Driven QA引き継ぎ拡張および作成者回答Skill実装計画
- **作成日時**: 2026-08-24 22:02 (JST)
- **目的**: 
  - `spec-driven-qa-review` で作成されたQA記録を別AI（AI-1/実装者）に引き継ぐ際の認知負荷を下げ、誤解なく復元可能にする。
  - 実装者側AIが統制された形式で回答するための専用スキル `spec-driven-qa-author-response` を新設し、自己検証・自己クローズを防止する職務分離を確立する。
- **主要な決定事項・成果**:
  - **公開契約 `handoff.md` の導入**: 既存正本（`review.md`, `findings.yaml`, `traceability.yaml`, `events.jsonl`）から機械生成される引き継ぎビューを標準化。
  - **Author Disposition 体系の策定**: `accepted`, `rejected-with-evidence`, `fix-submitted`, `deferred`, `risk-accepted`, `not-applicable` を定義。`fix-submitted` は修正提出に過ぎず、Reviewerの検証（`fixed-and-verified`）までクローズ不可とする統制を確立。
  - **多重サイクル管理**: `cycles/cycle-NN-author-response.md` による履歴保存。

### 2.2 Plan 002: spec-driven-qa-review 比例的QAゲート改善実装計画
- **作成日時**: 2026-08-25 00:54 (JST)
- **目的**: 
  - 家庭内LAN・非安全系・非リアルタイムの廉価IoT機器等において、仕様外の要求を無暗にCritical/Highブロッカーへ拡張しない比例的品質保証（Proportional QA Gates）を実現する。
- **主要な決定事項・成果**:
  - **リスクプロファイルの初期確認**: レビュー開始時に配置範囲、安全系/SLAの有無、許容データ損失、ハードウェア制約、運用形態を記録。
  - **比例的ゲート判定の導入**: 
    - Critical/High は「仕様・目的・不変条件の明白な違反」に限定。
    - 外部非公開・非安全系における多層防御・HA・監視などは、明示要求がない限り Medium/Low/Suggestion または Risk Profile 適合として処理。
  - **`proportional-qa-gates` 仕様の昇格**: OpenSpec変更を通じて `openspec/specs/proportional-qa-gates/spec.md` へ反映。

### 2.3 Plan 003: 旧QAスキル退避および開発版スキルのグローバル配置計画
- **作成日時**: 2026-08-25 22:00 (JST)
- **目的**: 
  - グローバル環境（`~/.agents/skills/`）の旧版QAスキルを本リポジトリ内へzipバックアップし、新版（Contract v1.2対応版）を安全にグローバル配置する。
- **主要な決定事項・成果**:
  - **旧版の退避完了**: `archives/skills/legacy-qa-skills_20260825.zip` を作成し、ハッシュと展開検証を実施。
  - **安全配備プロセスの定義**: 直接上書きを禁止し、作業一時ディレクトリでのMANIFEST検証、Pythonテスト、秘密情報チェックをパスした後にのみグローバルへ配置する手順を策定。

### 2.4 Plan 004: Cursor会話関連ファイルの安全クリーンアップ計画
- **作成日時**: 2026-08-25 22:37 (JST)
- **目的**: 
  - UI上で直近30日分を残して削除済みの会話に関連する孤児ファイル（`~/.cursor/chats`, `agent-transcripts`, `acp-sessions`, `conversation-search.db`）を安全に整理する。
- **主要な決定事項・成果**:
  - **不変境界の死守**: `meta.json` に残るアクティブ会話（3件）や、設定ファイル（`mcp.json`, `settings.json`, `keybindings.json`）、DB本体（`state.vscdb`）への不可触ルールを徹底。
  - **段階的クリーンアップ**: 孤児トランスクリプト・30日超セッションの安全な除去手順を確定。

---

## 3. 現行フェーズへの接続

Plan 001〜004の後に続いたOpenSpec移行期（Plan 005〜010）は、[統合アーカイブ要約 (002)](archived_summary_002_0828.md) に集約した。人間中心Quality Loopの実装履歴は[統合アーカイブ要約 (003)](archived_summary_003_0831.md)を、最終QAは[QA受入サマリー](qa_acceptance_summary_001_0831.md)を参照する。
