# spec-driven-qa 2 Skillコンパクト化設計

## Context

対象は、外部配置先にある`spec-driven-qa-review`と`spec-driven-qa-author-response`、および本リポジトリで検証するステージングBundleである。現状は共通処理、契約検証、参照文書、Schema、Template、Fixtureが複数ファイルへ分散している。先行ChangeのContract v1.2候補は参照可能だが、旧版比較、rollback、残余リスク記録が未完了であるため、本設計では受入済み正本とみなさない。

実行時依存はPython標準ライブラリのみとし、既存のCLI入口、終了コード、JSON出力、QAケースの読み取り互換を維持する。外部配置先は承認境界の外にあるため、設計・実装・検証はリポジトリ内のステージング領域で完結させる。

## Goals / Non-Goals

**Goals:**

- ReviewerとAuthorの役割をSkill名・入口・実行時権限の三層で分離する。
- 共通処理を一元化し、契約と安全境界の重複実装・ドリフトを減らす。
- 旧版、Contract v1.2候補、圧縮版を同じ機能台帳とfixtureで比較できるようにする。
- `SKILL.md`の常駐規則と詳細仕様を分離し、エージェントが次の行動を判断しやすくする。
- ステージング、差分表示、backup、rollback、明示承認を配備経路へ組み込む。
- テスト、完全サンプル、安全境界を削らず、1,760行以下を測定可能な第一目標にする。

**Non-Goals:**

- Contract v1.2候補の未検証部分を本Changeで受入済みに変更しない。
- QA契約の意味、証拠基準、Finding分類、Reviewer/Authorの責務を緩和しない。
- 既存QA履歴の一括変換や、外部Skill配置先の直接置換を行わない。
- OS権限、常駐lockサービス、Git hook、外部データベースを新規導入しない。
- 行数目標だけを理由にテストや必須Fixtureを削除しない。

## Decisions

### 1. 配布単位は「共有コア＋2つのSkill入口」とする

ReviewerとAuthorを単一Skillへ統合せず、役割別の`SKILL.md`を維持する。ステージングBundleは次の論理構成とする。

```text
staging/spec-driven-qa-bundle/
├── shared_core/                 # 契約・検証・安全境界の共通実装
├── spec-driven-qa-review/       # Reviewer入口とReviewer固有処理
├── spec-driven-qa-author-response/ # Author入口とAuthor固有処理
├── schemas/                     # 契約の正本
├── templates/                   # 最小完全テンプレート
├── fixtures/                    # golden / negative / cross-skill
└── evals/                       # 差分・サイズ・役割逸脱評価
```

Skill単位で配布できない環境では、Bundle Validatorが共有コア不足を検出して配備を拒否する。各入口のLauncherは自身の実ファイル位置からBundleルートを決定し、期待する`shared_core/`、Manifest、共有コアの内容digestを検証してから、そのBundleルートだけを限定的にimport解決対象へ追加する。`PYTHONPATH`、cwd、環境変数、未検証のシンボリックリンクには依存しない。期待配置またはdigestが一致しない場合はfail-closedとする。共有コアを各Skillへ無管理に複製する方式は、二重更新と契約ドリフトを生むため採用しない。

### 2. 共通コアは責務別モジュールとし、単一CLIモノリスを避ける

共有コアは、契約・digest、状態遷移、Evidence・秘密情報、リンク、入出力・終了コード、役割認可の責務別モジュールに分け、CLIは薄いFacadeとする。小さな既存Scriptを機械的に連結せず、公開契約と権限境界を横断する処理だけを共通化する。

Reviewer入口は独立レビュー、ケース作成、handoff、Reviewer検証、closeを公開し、Author入口はhandoff読取、response、submission、実行ポリシーを公開する。共有コアは入口から渡された役割を再検証し、役割外操作を拒否する。

### 3. 正本と派生物を分離する

契約フィールド、状態、Finding、Evidence、digest対象はSchemaを正本とする。Template、handoff、CLI JSON、MANIFESTはSchemaから参照または検証される派生物として扱う。詳細な分類、証拠階層、状態遷移、安全規則は`SPEC.md`へ集約し、2つの`SKILL.md`には役割別の行動規則、禁止事項、参照先だけを置く。

SchemaをPython型へ置換する場合は、Schemaで受理・拒否されたfixtureをすべて差分実行し、互換性を確認できた場合に限る。置換が圧縮目標を改善しない場合はJSON Schemaを残す。

### 4. 互換性はgolden fixtureと機能台帳で判定する

Phase 0で、現行Review/Authorの公開入口ごとに機能ID、引数、終了コード、stdout/stderr、JSON必須フィールド、ファイル副作用、役割、拒否条件を固定する。fixtureは次の層に分ける。

- golden: 既存の正常系と最小完全サイクル
- negative: stale digest、revision競合、秘密情報、未許可操作、自己クローズ、未知major
- cross-skill: Reviewer生成handoffをAuthorが読み、Author提出をReviewer統合Validatorが受ける経路
- legacy: v1.0/v1.1読み取り互換
- size: ファイル、行数、バイト数、常駐読み込み量

比較結果は単なるテキスト一致ではなく、終了コード、契約上のJSONフィールド、状態変化、正本・提出物・イベントの副作用を正規化して比較する。判定の正本は、当該ChangeのOpenSpec `spec.md`（および配布Bundle内の詳細`SPEC.md`が存在する場合は、`spec.md`から生成・digest固定された派生仕様）とする。`design.md`、`tasks.md`、旧版挙動、未検証のContract v1.2候補挙動は、正本を上書きしない。候補版または圧縮版が正本仕様に違反する場合は、挙動が一致していても不適合として記録し、旧版との差異は互換性情報として別に記録する。診断文の差異は、契約差異と区別して記録する。

### 5. 役割FirewallをCLIとファイル境界の両方に置く

入口のプロンプト規則だけに依存せず、共有コアの認可表と書込み許可対象で二重に制御する。Authorの許可対象はhandoff、submission、実装・Evidence参照に限定し、Reviewer正本、Reviewerイベント、検証結果、closureへの直接書込みを許可しない。ReviewerもAuthor提出の新規作成と、許可された統合処理を区別する。

認可失敗は非ゼロ終了コードと構造化診断を返すが、秘密値、未許可パスの内容、内部Tokenは出力しない。

### 6. 配備は原子的なstaging移行とrollbackを前提とする

新Bundleを一時領域へ生成し、Manifest、構文、Schema、fixture、eval、行数、差分表示、backupを順に検証する。検証失敗時は外部配置先に触れない。配備を実施する場合も、明示された対象だけをbackupし、manifestにないパスを変更しない。配備後の読み取り・handoff・submission・rollback確認が終わるまで受入済みと報告しない。

### 7. サイズ目標は能力維持ゲートと同時に判定する

行数1,760以下を第一目標とするが、合格条件は行数単独ではなく、機能ID欠落0、重要回帰0、役割逸脱0、Schema/Manifest整合、負のfixture合格、rollback再現可能性を含む。目標未達時は、削除した機能ではなく重複除去量、常駐token削減量、保守対象削減量を報告し、能力維持を優先する。

### 8. 代替案と不採用理由

- **単一Skillへ統合**: 入口の役割認識が曖昧になり、AuthorがReviewer操作を行う誤作動を防ぎにくいため不採用。
- **全Scriptを単一`qa_tool.py`へ連結**: ファイル数は減るが、責務混在と障害波及が増えるため、薄いFacade＋責務別共有モジュールへ変更。
- **JSON Schemaを全面的にPython型へ置換**: 実装量は減る可能性があるが、外部検証・契約可視性・互換性を失うため、fixture検証後の条件付き採用とする。
- **テスト・サンプルを大幅削減**: 見かけの圧縮は得られるが、能力維持を証明できないため不採用。

## Risks / Trade-offs

- [Risk] 共有コアの変更がReviewerとAuthorへ同時波及する → 役割別入口、認可表、cross-skillとnegative fixtureで影響を分離して検証する。
- [Risk] Skill単位配布で共有コアが欠落する → Bundle Validatorで構成を検査し、共有コア不足時はfail-closedとする。
- [Risk] 文書蒸留で重要な判断規則が失われる → 先に不変条件台帳とevalを固定し、`SKILL.md`削減後に行動シナリオを再評価する。
- [Risk] 旧CLIとの互換性が診断文の差異に隠れる → 終了コード、構造化出力、状態、副作用を正規化して比較する。
- [Risk] 1,760行目標が安全性を押し下げる → サイズは第一目標に留め、機能・安全・rollbackゲートを優先する。
- [Risk] Contract v1.2候補の未検証状態を誤って受入扱いする → Change間の状態を明示し、圧縮ChangeのEvidenceに「基準候補」と記録する。

## 移行計画

1. 現行2 SkillとContract v1.2候補を読み取り専用で基準化し、機能台帳とfixtureを作成する。併せてManifest対象を決定論的に集計する`measure_size.py`を作成し、空行・コメント・テスト・サンプル・Schemaの含否を出力へ明記する。
2. リポジトリ内のstaging Bundleへ共有コア、Reviewer入口、Author入口、正本Schema、最小完全Templateを作成する。
3. 旧入口から共有コアを呼び出す互換層を追加し、旧版と圧縮版を同一fixtureで比較する。
4. 文書、examples、Manifest、README、INSTALL、evalを新しい正本・派生物関係に合わせる。
5. Bundle Validator、単体・統合・negative・cross-skill・legacy・size evalを実行する。
6. dry-run、全差分表示、backup、限定rollbackを確認し、結果と残余リスクをChange Evidenceへ記録する。
7. 明示承認後に限り、外部Skill配置先へ対象を限定して配備する。配備後の読み取り・提出・統合・rollback確認が終わるまで旧版削除を行わない。

## Open Questions

- なし。共有コアのBundle配置、2入口の役割境界、差分fixture、サイズ目標、配備境界は本設計で確定した。実装時に得られる測定値は、設計変更ではなくEvidenceとして記録する。
