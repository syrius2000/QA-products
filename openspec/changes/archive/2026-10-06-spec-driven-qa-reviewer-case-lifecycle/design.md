## Context

動機と範囲は [proposal.md](proposal.md) を参照する。要求は [specs/spec-driven-qa-reviewer-case-lifecycle/spec.md](specs/spec-driven-qa-reviewer-case-lifecycle/spec.md) を正とする。

現在の実装状態:

- 共有基盤Change（`archive/2026-08-26-compact-spec-driven-qa-skills`）は `shared_core`（契約・digest・Firewall・状態遷移・CLI Facade）と Reviewer/Author Launcher を持つが、Reviewer入口は薄い。ケース作成から close までの業務ライフサイクル本体は未完成のまま後続Changeへ引き継がれている。
- Contract v1.2 候補（`archive/2026-08-26-improve-spec-driven-qa-contract-v1-2/stage/spec_driven_qa_reviewer`）には `create_review_case`、`render_handoff`、`close_review_case`、`cycle_limit`、各種 validator など Reviewer 向けスクリプト群があるが、グローバルSkill受入済み正本ではない。
- 共有 `authorization.REVIEWER_OPERATIONS` は現状 `{review, handoff, verify, close}`。Author は `{respond, submit}`。Schema・digest・revision 契約は本Changeから変更しない。

制約:

- 実装・検証は本Change配下のステージング領域に限定する。外部Skill配置、旧版削除、commit、push は行わない。
- 実行時依存は Python 標準ライブラリのみ。
- Author 提出作成・Author Changeの責務は本設計の対象外（並行可能な別Change）。

## Goals / Non-Goals

**Goals:**

- Reviewer ライフサイクルを、共有Firewallの上で「公開操作 → 正本更新 → イベント追記 → 拒否」まで一貫して実行可能にする。
- 正本（`review.md` / `findings.yaml` / `traceability.yaml` / `events.jsonl` / closure）への書込み権限を Reviewer のみに固定する。
- Contract v1.2 候補の Reviewer スクリプトを再利用可能な単位へ整理し、共有コア契約を壊さずにステージングBundleへ統合する。
- 旧Reviewer CLI と終了コード・JSON必須フィールドの互換面を、本Changeの公開機能ID単位で測定可能にする。

**Non-Goals:**

- Author Response / submission 生成の実装（別Change）。
- 共有 Schema・digest アルゴリズム・revision 意味の変更。
- 43機能ID全体のレガシー3版比較（後続の parity Change）。
- 外部配備・dry-run・rollback（後続の deployment Change）。
- OS権限や常駐ロックによる強制。防御は Bundle 内 Firewall とファイル境界に限定する。

## Decisions

### 1. 実装ホームは本Changeの `stage/` とし、共有コアは読取再利用する

```text
openspec/changes/spec-driven-qa-reviewer-case-lifecycle/stage/
├── shared_core/                 # 共有基盤から複製または同期（契約変更なし）
├── spec-driven-qa-review/       # Reviewer入口・ライフサイクル実装
├── schemas/                     # 共有契約の参照コピー（digest固定）
├── templates/                   # ケース初期化テンプレート
├── fixtures/                    # Reviewer golden / negative
└── tests/
```

- 共有コアの契約ファイルを本Changeの都合で改変しない。必要なのは Reviewer 固有モジュールの追加と、操作名のマッピングである。
- Contract v1.2 候補の Reviewer スクリプトを移植起点とするが、入口は compact Bundle の Launcher + `shared_core.cli` 経由に統一する。
- 代替案「v1.2 stage をそのまま本番候補にする」は、共有Firewall・Manifest・2入口構成と乖離するため不採用。

### 2. 正本書込み権限は Reviewer 専用 allowlist で強制する

| 対象 | Reviewer | Author（本Changeでは実装しないが境界として固定） |
|---|---|---|
| `review.md`（状態・要約） | 書込可 | 拒否 |
| `findings.yaml`（Finding正本） | 書込可 | `author_response` 以外は拒否（Author Change側） |
| `traceability.yaml` | 書込可 | 拒否 |
| `events.jsonl`（append-only） | 追記可 | 拒否 |
| `handoff.md`（派生物） | 生成可 | 読取のみ |
| `cycles/cycle-*-independent-review.md` / `*-verification.md` | 書込可 | 拒否 |
| `cycles/cycle-*-author-response.md` / submission | 検証時読取 | 作成は Author |
| terminal / closure 記録 | Reviewerのみ | 拒否 |

- 入口プロンプトだけでなく、`shared_core.authorization` と Reviewer 側 path allowlist の二重検査とする（共有基盤 Decision 5 の延長）。
- Author が `closed` / `fixed-and-verified` を直接設定した提出は、verify 経路で契約違反として拒否する（spec の拒否シナリオ）。
- 代替案「ファイル権限をOSに任せる」は環境差とテスト不能性のため不採用。

### 3. 公開操作は共有操作集合へ写像し、`init` は `review` の下位アクションとする

| CLI / 機能 | 共有 operation | 主な副作用 |
|---|---|---|
| ケース初期化 | `review` (`action=init`) | ケースDIR作成、初期イベント |
| 独立レビュー / Finding記録 | `review` | findings / traceability / cycle review |
| handoff生成 | `handoff` | `handoff.md` 再生成（正本からの派生物） |
| Author提出検証 | `verify` | verification cycle、正本更新候補の適用 |
| close | `close` | terminal status、closure event |

- 共有 `REVIEWER_OPERATIONS` を増やして Schema 互換表を揺らさない。初期化は `review` に内包する。
- cycle制限チェックは `verify` と `handoff` の前後ゲートとして `cycle_limit` モジュールを呼び、超過時は `adjudication-required` へ遷移して自動サイクルを止める。
- 代替案「`init` を共有 operation に追加」は Author/評価台帳・認可fixtureの更新範囲が共有基盤へ広がるため、本Changeでは採らない。

### 4. Finding・handoff・close は「検証してから書く」パイプラインにする

1. 入力を Schema / 必須フィールドで検証（classification・evidence・purpose classification 欠落は reject、既存状態を保持）。
2. digest / revision / open Finding ID 集合を共有コアで計算・照合。
3. 成功時のみ正本を更新し、`events.jsonl` へ append-only で記録。
4. handoff は正本の投影のみ。手編集を正本扱いにしない。

close は REQUIRED marker 解消、Critical の verified、High の verified または 5要素揃いの `risk-accepted` を満たす場合のみ terminal（`accepted` / `accepted-with-residual-risk` 等）へ進める。

### 5. 互換性の扱い（本Changeの境界）

- Reviewer 公開機能IDの対応表を本Change Evidence に起稿し、欠落0を目指す。
- 終了コード・JSON必須フィールド・拒否コードは旧版と同一fixtureで比較可能な形に揃える。
- 43機能全体の3版比較と未説明差分0は後続 `capability-parity` Change の完了条件とし、本Changeでは Reviewer 範囲の回帰防止に留める。

### 6. 独立QAゲート

本Changeを完了扱いにする前に、少なくとも次を Evidence 化する。

- 正常系: init → review → handoff →（fixture提出）→ verify → close
- 拒否系: 対象欠落の init、evidence/classification 欠落 Finding、自己クローズ提出、未知 Finding ID、cycle超過、REQUIRED残存での close
- role firewall: Author 役割での正本/events/close 書込みが拒否されること
- 履歴不変性: 過去 cycle / events の改ざんではなく追記のみであること

`openspec` の構造 `valid: true` だけでは完了としない。

## Risks / Trade-offs

- [Risk] v1.2 候補スクリプトと共有コアの重複・ドリフト → 契約・digest・認可は共有コアへ寄せ、Reviewer固有I/Oだけを入口側に残す。重複検知テストを置く。
- [Risk] `init` を `review` に内包したことで機能ID対応が曖昧になる → 公開機能台帳に `action` 付きで記載し、CLIヘルプとfixture名を一致させる。
- [Risk] Author Changeと並行したときの handoff 契約齟齬 → handoff フィールドは共有 Schema を唯一の正とし、本Changeで Schema を変えない。
- [Risk] ステージングへの共有コア複製が古くなる → Manifest に共有コア内容 digest を記録し、基盤アーカイブ版との差分を検証タスクに含める。
- [Risk] 部分実装を受入済みと誤記する → 未検証項目は `unverified` / `evidence-gap` のまま tasks に残す。

## Migration Plan

1. 本Change `stage/` を作成し、共有基盤 Bundle から `shared_core` / schemas / Reviewer Launcher 骨格を取り込む（契約改変なし）。
2. v1.2 候補の Reviewer スクリプトを責務単位で移植し、共有 operation 写像と allowlist を接続する。
3. fixtures（golden / negative / firewall）と pytest を追加し、独立QA Evidence を本Change配下へ保存する。
4. 外部配置・旧版削除は行わない。ロールバックは `stage/` の破棄または git 復元で足りる（本Changeに本番配備なし）。

## Open Questions

なし。正本書込み境界、`init`→`review` 写像、共有契約非変更、Author/配備の除外は本設計で確定する。公開機能IDの最終件数は実装時の台帳起こしで Evidence 化し、設計変更条件にはしない。
