# Legacy非互換分類と互換性判定の実装計画

created: 2026-08-27 01:25 (JST)
update: 2026-08-27 01:25 (JST)
author: Codex (GPT-5)

## 1. 目的

Legacyアーカイブを改造せず、旧版に存在しないReviewer・Author連鎖契約を「未実装」と誤判定しない比較方式を実装する。同時に、Candidateおよびcompactの差分を、互換・意図的非互換・表示差分・未検証へ機械的に分類し、未説明の欠落を全体合格へ集約しない。

## 2. 対象範囲

- `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/stage/`配下の比較ハーネス、差分分類器、回帰fixture、Evidence。
- 同Changeの`tasks.md`における3.3のEvidence判定補足、および4.1〜4.4の実装。
- Candidate、compactの既存安全契約と、QA-0006／QA-0007で確認されたdigest・提出境界の回帰確認。
- 複数Agent／RunのEvidenceを混同しない集計と、秘密値を保存しない検査。
- Bundle別のサイズ・ファイル数・行数・バイト数の決定論的な計測。

## 3. 対象外と安全境界

- アーカイブ済みLegacy ZIP、Candidateアーカイブ、既存QA正本の改変。
- `~/.gemini/config/skills/`等への配置、旧版削除、commit、push。
- Legacyに存在しない連鎖APIを、互換性の証明目的でアダプターにより偽装すること。
- 外部LLMの正答率・Token・Latencyが取得できない場合の推定値による完了判定。
- 独立QA、人間裁定、最終配備可否の自己判定。

## 4. 実装方針

### 4.1 Legacy欠落の明示

cross-skill Evidenceへ、Legacyの`submission`・`semantic/content digest`・`revision`が旧契約に存在しないことを、`intentional-noncompatibility`または`evidence-gap`として明記する。三版全体を互換合格にはしない。compactの連鎖API実装とCandidateの既存提出検証はObservedとして別管理する。

### 4.2 機能差分分類器

機能台帳、三版Run、仕様上の許可差分を入力として、機能ID単位の比較レポートを生成する。分類は次の4種類に限定する。

- `compatible`: 期待終了コード、必須出力、契約境界を満たす。
- `intentional-noncompatibility`: 正本仕様に理由と代替動作があり、Legacy完全互換件数へ含めない。
- `presentation-only`: 診断文や表示形式のみの差分。
- `missing-or-unverified`: 入口・出力・Evidenceが欠落、または検証不能。

未分類差分、説明のない欠落、Evidence欠落が1件でもある場合は、レポート全体を非合格候補または`evidence-gap`とする。

### 4.3 回帰とEvidence

Candidate／compactについて、自己クローズ、Reviewer正本書込み、未知Finding、Workspace外パス、stale digest、旧同値digest、未知digest version、秘密値の拒否を回帰fixtureで確認する。各Runは入力、出力、終了コード、Bundle digest、Agent／Run識別子を保持し、秘密値検出時は保存・集計を拒否する。

### 4.4 サイズ計測

Legacy、Candidate、compactを同一計測方式で比較し、ファイル数・行数・バイト数と、テスト・仕様・安全実装の存在を同一レポートへ出力する。1,760行以下は参考目標とし、削減だけを理由に安全機能や完全fixtureを除外しない。

## 5. 実装順序

1. 差分分類の正本データとJSONスキーマを追加する。
2. `diff_classifier.py`とnegative／positiveテストを追加する。
3. cross-skill結果を分類器へ渡し、Legacy欠落を意図的非互換または未検証として出力する。
4. Candidate／compactの安全境界・digest境界・秘密値検出を回帰実行する。
5. Agent／Run集計とサイズ計測を決定論的に実行する。
6. `tasks.md`は実装とEvidenceが揃った項目だけ更新する。3.3はLegacy側の契約不在を理由に未完了を維持する。

## 6. 検証と完了条件

- 標準ライブラリのみで新規テストが再現可能である。
- 差分分類レポートがCandidate／compactのObserved結果とLegacyの契約欠落を分離している。
- 未説明差分を含むfixtureが全体合格へ集約されない。
- 安全境界、digest境界、秘密値防御、Evidence隔離の回帰テストが成功する。
- サイズ計測とManifest検証が成功する。
- OpenSpec validationが`valid`である。
- 独立QA・人間裁定・外部配備は完了扱いにしない。

