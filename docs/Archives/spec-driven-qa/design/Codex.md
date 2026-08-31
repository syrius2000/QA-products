# Contract v1.2 設計グリル記録（ドラフト）

created: 2026-08-25 19:50 (JST)
update: 2026-08-25 20:53 (JST)
author: Codex (GPT-5)

## 文書の位置付け

本書は、`GPT-findings.md` を対象とする設計グリルで確定した判断を記録するドラフトである。実装承認、既存Skillの置換、グローバルSkillディレクトリへの配備を意味しない。

## 確定した設計判断（第1ラウンド）

### D-01: Author Validator と Reviewer 正本の信頼境界

Author側Validatorは、公開契約である`handoff.md`、そこから参照される実装対象、テスト、Evidenceを検証対象とする。Reviewer正本（`review.md`、`findings.yaml`、`traceability.yaml`、Reviewerの`events.jsonl`）はAuthorの読取り・書込み対象にしない。

Authorは許可リスト内の追記専用提出先（例: `author-submissions/cycle-NNN-author-response.md`）へResponseを記録する。Reviewer側の統合Validatorが提出物とQAケース正本を突合し、正本への反映を担当する。Authorはseverity、Finding状態、verification、case closureを変更できない。

### D-02: handoff の鮮度検証

二種類のダイジェストを用いる。

- `semantic_digest`: Finding ID、severity、技術状態、対象範囲、実装許可、対象revision、Quality Intent、Evidence要件など、判断・実装可否を変える構造化フィールドの安定直列化ハッシュ。
- `content_digest`: 正本ファイル群の内容変化を検出するハッシュ。改行はLFに正規化するが、YAMLの字下げやMarkdown本文の空白を一律に除去しない。

`semantic_digest`の不一致は`blocked: inconsistent-qa-state`として停止する。`content_digest`のみの不一致はhandoff再生成と人間確認を要求する警告とする。競合更新は`expected_semantic_digest`と単調増加する`case_revision`の比較で検出し、古い提出による上書きを拒否する。

### D-03: 状態モデルの最小化

論理仕様では、`case_status`、`workflow_phase`、`finding_status`、`author_disposition`、`owner_disposition`、`terminal_result`を区別する。

ただしケース直下へ永続化する状態は、`case_status`、`next_action`、`case_revision`に限定する。Finding固有の技術状態・Author回答・Owner裁定は各Findingにカプセル化し、`workflow_phase`と`terminal_result`は状態遷移規則から導出する。LLMが六つの状態を手作業で同時更新する運用は採らない。

### D-04: Fast Path の承認境界

Fast Pathは実装承認を代替しない。リポジトリ規則とユーザーの明示承認済みスコープを満たす場合に限り、Reviewerの追加Plan Reviewを省略できる。

```text
can_execute =
  repository_policy_allows
  AND user_authorization_covers_scope
  AND (handoff_permission OR eligible_fast_path)
```

`eligible_fast_path`は、Lowまたは文書のみ、局所的、可逆、非破壊、外部操作なし、かつ事前承認範囲内という全条件を満たす場合だけtrueとする。Medium/High、範囲外、または判断が曖昧な変更は通常のResponse Planと承認経路へ戻す。

### D-05: 新版の作成・配備方式

既存の`spec-driven-qa-review`と`spec-driven-qa-author-response`は直接置換しない。ステージング用パッケージでContract、Validator、E2E評価を固め、明示承認後にのみ既存Skillへ差分配備する。配備前にはdry-run、差分表示、バックアップ、固定fixtureの`run_evals.py`を必須とする。

## 用語

| 用語            | 定義                                                                                      |
| --------------- | ----------------------------------------------------------------------------------------- |
| QA正本          | Reviewerが所有し、Finding・状態・検証・クローズの根拠となる記録群。                       |
| 公開契約        | Authorに渡す`handoff.md`。対象Finding、要求する回答、権限、revision、ダイジェストを含む。 |
| Author提出物    | Authorが許可リスト内に追記するResponseまたは修正提出。QA正本ではない。                    |
| 統合Validator   | Reviewer側でAuthor提出物とQA正本を突合し、正本への反映可否を判定するValidator。           |
| semantic_digest | 意思決定を左右する構造化状態の整合性を確認するダイジェスト。                              |
| content_digest  | ファイル内容の変化を検出し、再生成・確認の契機にするダイジェスト。                        |
| Fast Path       | 明示承認済みの軽微作業について、追加Plan Reviewだけを省略する経路。                       |

## 確定した設計判断（第2ラウンド）

### D-06: `semantic_digest`の対象と安定直列化

`semantic_digest`には、`schema_version`、`case_id`、`case_revision`、Quality Intent、対象スコープ、対象FindingのID・severity・技術状態・要求Evidence・実装許可・base revisionを含める。キー順を固定したJSONとして直列化してからハッシュ化する。

時刻、表示順、説明文、イベント履歴は`semantic_digest`から除外する。これらの変化は`content_digest`で検出し、再生成・確認の対象とする。

### D-07: Author提出物の準不変性

Authorは新しい`submission_id`ごとの提出ファイルだけを作成する。Reviewerが受理した時点で提出物の内容ハッシュをイベントへ記録し、受理済み提出物の変更または同じIDでの再提出はValidatorが拒否する。

OSレベルの不可変属性、Git hook、常駐サービスは、改ざんリスクまたは運用需要が実証されるまで導入しない。ここでいう追記専用は、まずContractとValidatorで保証する準不変性である。

### D-08: QA正本への統合主体

Reviewer Skillだけが`accept_author_submission`相当の統合処理を実行する。統合処理は、提出物の検証結果と正本に適用する変更候補を生成し、Reviewer AgentがEvidenceを評価してから正本へ反映する。

Authorが正本へ自動マージする経路は作らない。

### D-09: 技術未解決ケースの終了と再開

`closed`は技術的な修正完了ではなく、QAワークフローが終了したことを意味する。終了時には`terminal_result`を必須とし、値は`fixed-and-verified`、`risk-accepted`、`evidence-gap`、`deferred`、`not-reproducible`とする。

`risk-accepted`、`evidence-gap`、`deferred`には、Owner、根拠、対象範囲・前提、補償策、再レビュー条件を記録する。これらは技術的な完了として扱わない。

### D-10: `proportional-home`とFast Pathの独立

`proportional-home`はFinding分類と要求Evidenceを調整するrisk-context overlayである。Fast Pathの適格性は別に判定し、`proportional-home`であることだけからFast Pathを許可しない。

家庭内LAN・非安全系であっても、データ意味、スキーマ完全性、重複・欠損、秘密情報、破壊的操作、目的上重要な失敗は軽減対象にしない。

### D-11: 旧Contractケースの互換と移行

v1.0/v1.1のケースは読み取り専用adapterで扱い、履歴を自動書換えしない。次に意図的な再レビューを開始するときだけ、新Contractの新規cycleを追加して移行する。

移行時は旧記録を保存し、dry-run、差分表示、バックアップ、明示承認を必須とする。

## 用語の追加

| 用語                 | 定義                                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------------- |
| 準不変性             | OS機能に依存せず、提出ID・受理時ハッシュ・Validatorにより、受理済み提出物の変更を検出・拒否する性質。 |
| 統合処理             | ReviewerのみがAuthor提出物を検証し、変更候補を作成してQA正本へ反映する処理。                          |
| 終了結果             | QAワークフロー終了時の技術的・運用的な結論。`closed`とは別に記録する。                                |
| risk-context overlay | 対象環境のリスクに応じて分類・証拠要求を調整する規則。実装承認やFast Pathを自動付与しない。           |

## 確定した設計判断（第3ラウンド）

### D-12: Quality Intentの所有者

Quality Intentを確定・変更できるのはOwner/Humanだけとする。Reviewerは候補、解釈、必要Evidenceを提示できる。OpenSpecは根拠として取り込めるが、Quality Intentを自動更新する権限を持たない。

### D-13: Evidenceの最小契約

各Findingには、要求Evidence、実際のEvidence、検証者、取得時点、検証結果を構造化して記録する。静的確認、単体テスト、結合テスト、実行時証跡を区別する。

取得不能または再現不能な証跡は、成功として補完しない。`unverified`または`evidence-gap`として扱い、終了結果・再レビュー条件へ反映する。

### D-14: review cycle上限とエスカレーション

review cycleの標準上限は2、`strict`は3、`lite`は1とする。上限到達時は自動クローズせず、最終リスク評価とHuman/Owner判断へ移行する。

### D-15: 同時更新の処理

v1.2では`expected_semantic_digest`と`case_revision`による楽観的比較更新だけを採用し、lockは導入しない。競合時は古い提出による上書きを拒否し、最新正本の再読込・再提出を要求する。

競合再試行が実測で運用問題になった場合だけ、所有者・期限・強制解除の監査を備えた任意lock機能を追加検討する。

### D-16: 構造化CLI契約

`--json`出力は、`schema_version`、`ok`、`status`、`case_id`、`next_action`、`errors`を共通必須フィールドとする。JSONはstdout、診断はstderrへ出力し、人間向け既定出力は維持する。statusとexit codeの対応はContractで固定する。

### D-17: 評価の合格基準

固定fixtureによる契約・回帰・negative・cross-skill評価は100%合格を必須とする。旧版との同一prompt比較では、重大な誤実装開始、自己クローズ、未知Finding受理を0件とする。

再レビュー正答率、所要時間、token量、Humanへの追加質問数も記録し、性能主張はこれらの実測値で判断する。

## 用語の追加

| 用語             | 定義                                                                                     |
| ---------------- | ---------------------------------------------------------------------------------------- |
| Quality Intent   | Owner/Humanが定める、対象の目的・品質水準・許容リスクの基準。                            |
| 要求Evidence     | Findingを検証、撤回、修正済み判定するために事前定義する証拠の種類と条件。                |
| 楽観的比較更新   | 提出時に期待したrevision・ダイジェストが最新状態と一致する場合だけ更新を受け入れる方式。 |
| 重大な誤実装開始 | 承認または適格条件を満たさないのに、Authorがコード・設定・外部状態を変更すること。       |

## 確定した設計判断（第4ラウンド）

### D-18: 保存形式とダイジェスト直列化

QA正本とAuthor提出物は、人間による確認容易性のためYAMLを維持する。`semantic_digest`の入力だけはContractで定義したJSONへ変換し、キー順を固定して直列化する。

YAML解析器は明示的な依存関係として固定する。標準ライブラリだけで不完全な独自YAMLパーサーを実装しない。

### D-19: handoffの生成責任

`handoff.md`はRendererだけが生成・更新する派生物とする。人間による補足はQA正本の所定フィールドへ記録し、handoffを再生成する。生成済みhandoffの直接編集はValidatorが拒否する。

### D-20: Contract versionの互換交渉

handoff、Author提出物、CLI JSONには`contract_version`を必須とする。互換adapterが明示的に対応するversion組合せだけを読み取り可能とする。

未知のmajor versionは`blocked: unsupported-contract-version`として停止し、暗黙の推測変換を行わない。

### D-21: Evidenceの秘匿情報と参照可搬性

Evidence本体はQA記録へ複製せず、参照、取得時点、内容ハッシュ、要約を記録する。リポジトリ内Evidenceは相対パス、リポジトリ外Evidenceは外部参照であることを明示した絶対パスまたはURLとする。

秘密値は検出・マスクする。マスク不能な秘密値を含むEvidenceは参照を拒否し、`evidence-gap`として記録する。

## 設計グリルの完了

第1から第4ラウンドで、信頼境界、状態、権限、鮮度、競合、Evidence、互換性、評価、配備の分岐を確定した。残る作業は設計判断ではなく、Contract v1.2の仕様化、実装計画、実装、評価、承認済み配備である。

本ドラフトは次の計画作成の入力とする。実装開始には、対象・方式・影響範囲を定めた`implementation_plan`と、ユーザーの明示承認を別途必要とする。
