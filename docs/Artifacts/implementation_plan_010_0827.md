# Legacy非互換ポリシー確定と安全契約回帰の完了計画

created: 2026-08-27 01:41 (JST)
update: 2026-08-27 01:41 (JST)
author: Codex (GPT-5)

## 1. 結論

OpenSpecを継続利用する。新しい独立Changeは作成せず、既存の`spec-driven-qa-capability-parity-and-legacy-compat` Changeの仕様、設計、タスクを補正し、そのまま完了まで進める。

理由は、今回の作業が同じ目的である「Legacy・Candidate・compactの比較と安全な移行判定」の範囲内にあり、既に機能台帳、比較ハーネス、連鎖API、差分分類器、Evidenceが同じChangeへ集約されているためである。Changeを分割すると、Legacy欠落の判断、互換性判定、残余リスクが複数の正本へ分散する。

## 2. OpenSpecを継続する範囲

### 継続する対象

- 現Changeの`proposal.md`、`specs/`、`design.md`、`tasks.md`。
- 既存のLegacy ZIP、Candidateアーカイブ、compactステージングBundleを入力基準として扱う。
- `stage/evidence/compatibility-report.json`、`safety-regression.json`およびAgent／Run単位のEvidence。
- 5.1〜5.3、6.1〜6.4、7.1〜7.2の回帰、集計、サイズ、総合判定。
- 7.3〜7.5の独立QA、人間裁定、配備禁止境界の確認。

### OpenSpec上の補正

1. Legacyに存在しないsubmission、digest、revisionは、未実装と断定せず`intentional-noncompatibility`または`evidence-gap`として記録する。
2. `not-applicable`は互換合格を意味しない。Legacy完全互換件数から除外する。
3. Candidate・compactに存在する安全契約は、Legacyが許容していても緩和しない。
4. `tasks.md`は、Candidate／compactでObserved、または対象版に存在しないことを証明できた項目だけ完了扱いにする。
5. 外部LLMの正答率、Token、Latencyは取得不能なら`unverified`のまま保持する。

## 3. 推奨しない分岐

次の作業を行う場合だけ、別OpenSpec Changeへ分岐する。

- アーカイブ済みLegacyまたはCandidate BundleへAPIを追加する。
- Candidate旧版を別仕様へ置換し、比較基準そのものを変更する。
- `~/.gemini/config/skills/`等への本番配置、旧版削除、commit、pushを行う。
- 新しいContract v1.3を設計し、v1.2との互換性を変更する。

これらは現在の互換性検証とは異なる目的とリスクを持つため、別Changeに分ける。

## 4. 実装段階

### 段階A：仕様と判定モデルの確定

- `tasks.md`の3.3、5.1、5.2について、三版それぞれの`observed`、`not-applicable`、`evidence-gap`の扱いを明記する。
- Legacy連鎖契約欠落を意図的非互換として参照できる仕様・理由・Evidenceリンクを固定する。
- 全体判定が`legacy_full_compatibility=false`になることを維持する。

### 段階B：安全契約回帰

- Candidate・compactへ自己クローズ、Reviewer正本書込み、未知Finding、Evidence欠落、Workspace外パスを投入する。
- 両版で実装されていない制御は、合格ではなく`evidence-gap`または`not-applicable`として記録する。
- stale semantic/content digest、旧同値digest、未知digest version、秘密値を検証する。
- QA-0006とQA-0007の提出境界・digest分離プローブを回帰fixtureへ追加する。

### 段階C：Evidence集計とサイズ計測

- 各Agent／RunのManifest、Prompt、出力、条件、実行数、Bundle digestを検証する。
- 複数AIのRunを混同せず集計する。外部AIが提供しない数値は推定しない。
- Legacy、Candidate、compactのファイル数、行数、バイト数を同一方式で計測する。
- サイズ削減と安全機能・テスト・仕様の保持を同じレポートへ出力する。

### 段階D：受入ゲート

- G0〜G2の自動Evidenceを総合レポートへ統合する。
- Reviewer役とは別のAIまたは別セッションで7.3の独立QAを実施する。
- 未解決Finding、`unverified`、`evidence-gap`、意図的非互換、残余リスクをhandoffへ記録する。
- Ownerが`accepted-with-residual-risk`、保留、追加修正のいずれかを裁定するまで配備しない。

## 5. 完了条件

### 技術的完了

- 現ChangeのOpenSpec validationが`valid`である。
- 自動テストと標準ライブラリ回帰が再現可能である。
- Candidate・compactの安全境界Evidenceが揃っている。
- Legacy欠落が未説明の欠落として残っていない。
- 総合レポートがLegacy完全互換を誤って宣言しない。

### 受入完了

- 独立QAが完了している。
- Ownerの人間裁定が記録されている。
- 残余リスクと配備可否が明示されている。
- 外部配置は別の配備Changeとして切り離されている。

## 6. 今回の終了点

今回のChangeの終了点は「安全契約を維持したcompact版への移行判定を、人間裁定可能なEvidenceとして完成すること」である。「Legacy完全互換」や「本番配備成功」までを同じChangeの完了条件にしない。これにより、互換性の限界を隠さず、検証作業が無期限に続くことを防ぐ。

