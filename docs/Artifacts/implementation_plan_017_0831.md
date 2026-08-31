# Quality Loop資料アーカイブ・README整合化計画

created: 2026-08-31 13:11 (JST)
update: 2026-08-31 13:11 (JST)
author: Codex (GPT-5)

## 1. 目的

Quality Loopの開発履歴と独立QA結果を、後から追跡しやすい資料構成へ整理する。実装を追加する計画ではなく、完了済みArtifactの統合、QA結果の明示的な分離、現行READMEとロードマップの説明整合を行う。

## 2. ユーザー依頼と添付資料の区別

ユーザー依頼は、資料をアーカイブし、READMEと関連文書の相関を分かりやすく整備することである。過去に添付された各バージョンの計画書・QA用ZIPは、今回の編集対象を定義する原本ではなく、既に保存された履歴・参照資料として扱う。

最終QAについては、ユーザーが提示した次の結果を独立QA記録として明示する。

- 判定: `ACCEPT / READY FOR OWNER ADJUDICATION`
- Critical / High / Medium / Low: すべて0件
- v1.4.0 Core: architecture FIX候補としてOwner最終裁定へ送付

これは実装者のローカル検証結果、独立QAの推奨、Ownerの正式裁定、commit/pushを同一視しない。

## 3. 対象範囲

### 3.1 統合アーカイブする完了済みQuality Loop資料

次の完了済みArtifactを、実装履歴の統合要約へまとめる。

- `implementation_plan_011_0827.md`〜`implementation_plan_016_0831.md`
- `implementation_report_001_0828.md`
- `independent_qa_report_001_0828.md`
- `initial_release_adjudication_001_0828.md`

### 3.2 QA結果を別資料として保存

最終v1.4.0独立QAを、実装履歴とは別のQAサマリーとして保存する。対象QAパッケージ、提示された判定、Finding件数、実装者側の検証値、Owner裁定待ちの境界を記録し、QA結果が一覧から見落とされないファイル名と見出しにする。

### 3.3 現行資料の整合化

- ルート`README.md`の現在状態、参照先、Quality Loopの開発・QA・Owner裁定の関係を更新する。
- `AGENTS.md`の古い「Plan 012の独立QA待ち」という現行優先事項を、v1.4.0最終QA後の状態へ更新する。
- 移動後に残るArtifact、Archive、Quality Loop READMEの相対リンクを検査し、壊れた参照を修正する。
- 初期版や旧OpenSpec移行期の記述は、履歴として残すものと現行状態を示すものを区別する。

## 4. アーカイブ方針

`docs/Archives/`に、次の2資料だけを新規作成する。

1. 実装履歴の統合要約（Plan 011〜016、初期報告・初期QA・初期Owner裁定）
2. 最終v1.4.0独立QA受入サマリー（QA結果を明示）

統合内容とSHA-256・原本ZIPの保管場所を記録する。原本計画ZIP、QA用ZIP、tarballは既存の`archives/quality-loop/`から移動・削除しない。統合要約の検証とリンク確認が完了した後、上記の個別完了資料だけを`docs/Artifacts/`から削除する。現行仕様、QMS Reference、別プロジェクトのQAレビュー、Activeな移行ロードマップは対象外として保持する。

## 5. 安全境界

- コード、Schema、Skill、案件正本、依存関係は変更しない。
- 既存のユーザー変更、未追跡ファイル、削除済みArtifactを復元・上書き・追加削除しない。
- `quality-loop/`外部配置、旧Skill削除、commit、push、デプロイを行わない。
- 編集ラウンド開始前と終了時に`git diff`および対象ファイル一覧を確認する。
- 個別資料を削除する場合は、統合先の存在、内容、リンク、ハッシュを先に確認する。

## 6. 受入条件

- 実装履歴と最終QA結果が別ファイルで明確に識別できる。
- 最終QAサマリーに、判定、Severity別件数、対象v1.4.0、Owner裁定待ちの境界が記載される。
- READMEとAGENTSが、v1.4.0のローカル検証済み、独立QA ACCEPT、Owner最終裁定待ち、未commit/未pushという状態を矛盾なく説明する。
- `docs/Artifacts/`から統合対象の個別完了資料が除かれ、現行計画・参照資料は残る。
- リポジトリ内のリンク検査で、今回の移動に起因するリンク切れがない。
- 変更は資料整理に限定され、Quality Loopの動作、安全境界、テスト実装に差分がない。

## 7. 実施順序

1. 編集前のGit差分、対象ファイル一覧、原本アーカイブを記録する。
2. 2つの`docs/Archives/`要約を作成し、相互参照と原本参照を追加する。
3. README、AGENTS、必要最小限の関連文書を更新する。
4. リンク、Markdown構造、アーカイブ対象と残置対象、Git差分を検証する。
5. 検証後に個別完了資料を`docs/Artifacts/`から削除し、最終検証結果を報告する。

本計画の承認前は、計画書作成と読み取り専用調査に留め、アーカイブ移動・削除・README編集は開始しない。

## 8. 実施・検証完了記録

2026-08-31にユーザー承認を受け、次を実施した。

- 実装履歴を`docs/Archives/archived_summary_003_0831.md`へ統合した。
- 最終v1.4.0独立QAを`docs/Archives/qa_acceptance_summary_001_0831.md`へ分離記録した。
- `README.md`、`AGENTS.md`、既存の`archived_summary_001_0825.md`と`archived_summary_002_0828.md`の参照関係を更新した。
- 統合対象の完了済み個別Artifactを`docs/Artifacts/`から整理した。現行仕様、QMS Reference、別プロジェクトQA、Activeロードマップは残した。
- 原本ZIP・tarball・QA用ZIPは`archives/quality-loop/`に保持し、削除・移動していない。

検証結果:

- `git diff --check`成功。
- 新規Archive 2件、実装履歴とQA結果の分離を確認。
- 削除対象Artifactが残っていないこと、現行・Archive資料の旧参照を確認。
- コード、Schema、Skill、案件正本、依存関係、外部配置、commit、pushは変更・実施していない。

なお、既存の未追跡`NEXT_SESSION_MEMO.md`には旧Plan 012への参照が残っているが、作業開始前から存在するユーザー資料であり、本計画では編集していない。
