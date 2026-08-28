# 人間中心の最小QMS協働ループ新規実装計画

created: 2026-08-27 21:18 (JST)
update: 2026-08-27 22:11 (JST)
author: Codex (GPT-5)

## 1. 結論

現行のOpenSpec Change、Legacy互換性評価、三版比較、複雑なdigest、配備計画を新実装の前提にしない。リポジトリ内の独立ディレクトリ`quality-loop/`に、人間中心の最小QMS協働ループを新規設計・実装する。

新製品の中心は、次の4段階である。

1. Reviewerが、Ownerの定めた品質基準と客観的Evidenceに基づいてFindingを作成する。
2. Implementerが、Findingごとに回答し、許可された範囲だけを修正してEvidenceを提出する。
3. Reviewerが、元の品質基準を変更せず、修正結果を独立検証する。
4. 人間Ownerが、受入、リスク付き受入、保留、却下、再作業を裁定する。

各工程は、次のRole、入力、未解決事項、期待成果物を含むhandoffを必ず生成する。AIは品質要求を勝手に上げ下げせず、自己正当化、自己クローズ、責任追及、Evidenceの推測補完を行わない。

## 2. Goal

> 客観的で反証可能なFindingとEvidenceを用いて、責任追及ではなく改善を前進させる、人間中心の最小QMS協働ループを完成させる。

完成品は、OpenSpecを使用していない開発、文書作成、データ分析、一般的なソフトウェア開発にも適用できるものとする。

## 3. 方向転換の背景

これまでの開発は、互換性、Manifest、digest、配備境界、Agent／Run集計、サイズ計測などの非機能要件を広く扱った。その結果、QMSの本来の利用価値である「良いFindingを作り、改善し、独立検証し、人間が裁定する」という機能要件が見えにくくなった。

本計画では、既存成果の維持や互換性を成功条件にしない。旧成果からは考え方、境界条件、失敗事例だけを学び、旧コードは初期版へ再利用・移植・転記しない。旧成果は比較・回復用に凍結保存し、新製品の実行Bundleへ同梱しない。

## 4. OpenSpecを利用しない理由

今回の新規開発では、完成品にも開発管理にもOpenSpecを利用しない。

理由は次のとおりである。

- 現行Changeの互換性評価や非機能要件に新設計が引っ張られることを防ぐ。
- OpenSpec成果物とQMS案件正本という二つの状態管理体系を持たない。
- Artifact完成ではなく、4段階ループの実用性を直接評価する。
- QMS利用者にOpenSpecの導入、知識、ディレクトリ構成を要求しない。
- 初期版を2つのSkill、1つの案件正本、6つの操作へ集中させる。

計画性を廃止するものではない。本計画書、機能仕様、実装タスク、受入シナリオ、テスト結果、独立QA結果によって進捗と品質を管理する。将来OpenSpec連携が必要になった場合は、QMS本体を変更せず任意Adapterとして別計画で検討する。

## 5. 基本原則

### 5.1 品質基準の固定

- Ownerが案件開始時にPurpose、要求、受入基準、適用外事項、対象成果物、対象revisionを定める。
- Ownerは案件開始時に、Implementerの実装許可方針と変更可能範囲を定める。初期値は実装不許可とする。
- ReviewerとImplementerは、品質基準を直接変更できない。
- 品質基準の変更が必要な場合は、`baseline-change-requested`としてOwnerへ返す。
- baseline変更は`adjudicate`だけで登録し、変更理由、変更前後の差分、適用開始revision、再評価対象を記録する。
- Ownerが基準を変更した場合は案件revisionを更新し、影響するFindingを削除せず`requires-rereview`にしてReviewerによる再評価を必要とする。
- Purposeまたは受入基準が不足する場合、Reviewerは推測で補完せず`intake-incomplete`としてOwnerへ返す。

### 5.2 客観性

AIが無謬であることを客観性とは定義しない。第三者が、要求、観測事実、Evidence、影響、判定理由を追跡し、反証できることを客観性とする。

Findingは、次の要素が揃った場合だけ成立する。

- 対応する要求またはPurpose上のリスク
- 観測された事実
- 品質への影響
- 再現方法または確認方法
- 期待される状態
- Evidence参照または`unverified`である理由

要素が不足する内容は、Findingではなく質問、`intake-incomplete`、または`improvement-proposal`として扱う。

### 5.3 改善志向

- 人、能力、意図、責任を評価対象にしない。
- 対象成果物、工程、仕様、設計、実行条件、観測結果を評価対象にする。
- Findingの文面は「対象、事実、影響、次の改善行動」で構成する。
- Implementerの反論は防御ではなく、Evidenceを用いた基準照合として扱う。
- Finding数や重大度の高さをReviewerの成果指標にしない。
- Findingが0件でも、確認範囲とEvidenceを説明できれば有効なレビューとする。

### 5.4 後工程はお客様

- 各Roleは、次工程が追加質問なしで着手できるhandoffを作成する。
- handoffに欠落がある場合、その工程を完了扱いにしない。
- 次工程に必要な情報を探させたり、前工程の内部事情を推測させたりしない。
- 自動起動可能な環境ではオーケストレーターが`next_role`を利用する。
- 自動起動できない環境では、生成されたhandoffをそのまま次AIへ渡せるようにする。

### 5.5 品質憲章

Reviewer、Implementer、Ownerおよび隠れ層のModuleは、次の8原則を共通の品質憲章として適用する。

1. 品質基準とリスク許容は人間Ownerが決める。
2. 判定は要求とEvidenceへtraceできる。
3. 不確実性を隠さない。
4. 厳格さはリスクに比例させる。
5. 修正提出ではなく有効性確認で完了する。
6. handoffは受領確認まで閉じる。
7. 人の誤りはSystemで無害化する。
8. AIは助言、実行、検証を担うが、最終リスクを引き受けない。

規格・ガイダンスの背景、誤解しやすい論点、初期版へ持ち込まない事項は、[QMS品質思想Reference](qms_quality_reference_001_0827.md)を設計・教育用の詳細Referenceとして必要時だけ参照する。通常の状態遷移、status表示、定型handoffでは詳細Referenceを読み込まない。実装する2つのSkillには規格解説を重複記載せず、判断が必要な分岐からReferenceへ到達する短いcontext pointerだけを置く。

### 5.6 人の中断と再開

- 人間がAI間の全往復へ連続して立ち会うことを前提にしない。
- 各更新操作の完了後は常に安全な中断点とし、専用の`pause`操作を追加しない。
- `status`は最後に完了した操作、現在状態、未解決Finding、Evidence不足、Owner判断事項、許可済み変更範囲、次Role、次操作、最新handoffを返す。
- 必要な場合は`status --resume-format markdown`で人間向け`resume.md`を生成する。`resume.md`は表示物であり、正本として編集しない。
- 中断中に対象成果物または案件revisionが変化した場合、再開前に差分を表示し、古いhandoffによる更新を拒否する。
- Ownerの通常関与は、開始時の基準・実装範囲承認、例外裁定、最終裁定の3点に限定する。

## 6. 対象範囲

### 6.1 対象

- Reviewer用Skill `quality-review`
- Implementer用Skill `quality-response`
- 人間Owner用の裁定操作
- 単一案件正本`case.json`
- 人間向けstatusおよびhandoff生成
- 中断後の再開要約と任意の`resume.md`生成
- Python標準ライブラリを基本とする最小CLI／API
- Role、状態遷移、revision競合、必須項目、Evidence hashの機械的検証
- Ownerが定めた観測範囲における申告外変更の検出
- 合成受入シナリオ8件
- 低リスク実案件1件の試行
- 独立したReviewerセッションによる最終QA

### 6.2 対象外

- OpenSpecとの必須連携
- Legacy完全互換
- 三版比較および43機能IDの継承
- Agent／Run横断集計
- Token、Latency、ファイル数、行数を中心とした受入判定
- 本番Skill環境への配備
- 旧Skillおよび旧Evidenceの削除
- ダッシュボード、データベース、Web UI
- LLMベンダー固有APIへの直接接続
- semantic/content二重digest
- QMS利用者向けのテスト、静的解析、ログ解析機能の内製。QMS実装自身の単体・統合・受入テストは対象に含む

## 7. Roleと権限

### 7.1 Reviewer

Reviewerは、基準とEvidenceに基づく初回レビューおよび修正後の独立検証を行う。

許可する行動:

- Finding、質問、改善提案の作成
- Evidenceの登録および評価
- Implementer提出物の技術的な`verified`／`not-verified`判定
- 修正により新たに観測された問題の別Finding化
- 次工程へのhandoff作成

禁止する行動:

- baselineの変更
- 対象実装の修正
- Implementer回答の代筆
- Owner裁定の代行
- 案件の自己受入または自己クローズ

### 7.2 Implementer

Implementerは、Findingに回答し、明示的な実装許可がある場合だけ対象を修正する。

実装許可はOwnerが`create-case`または`adjudicate`で登録する。`implementation_authorization`には、許可の有無、対象Findingまたは許可条件、変更可能なファイル・データ・操作の範囲を含める。Reviewerは許可範囲を拡張できず、handoffにはOwnerが許可した範囲だけを転記する。`submit-response`は`changed_targets`を必須とし、有効な許可がない修正提出または申告された範囲外変更を拒否する。

回答種別:

- `accepted`
- `fix-submitted`
- `disagreed-with-evidence`
- `cannot-verify`
- `baseline-change-requested`

禁止する行動:

- Findingの削除または内容変更
- baselineの変更
- Reviewer検証結果の作成
- Owner裁定の代行
- 案件の自己クローズ
- 許可されていないファイルまたはデータの変更

### 7.3 Owner

Ownerは必ず人間とし、案件開始時の基準設定と最終裁定を行う。

裁定種別:

- `accepted`
- `accepted-with-risk`
- `held`
- `rejected`
- `rework-requested`

`accepted-with-risk`には、理由、受入条件、期限または再確認トリガーを必須とする。OwnerはReviewerの技術判定を`verified`へ書き換えず、技術的未解決と事業上の受入を別々に記録する。

## 8. FindingとEvidence

### 8.1 Finding分類

- `requirement-violation`: 明示要求または受入基準への不適合
- `purpose-risk`: 明示要求だけでは表現されていないが、Purposeを直接損なう観測可能なリスク
- `evidence-gap`: 成否を判断するためのEvidence不足
- `improvement-proposal`: 仕様外の改善提案。受入を妨げず、対応を強制しない

### 8.2 Severity

Severityは`critical`、`high`、`medium`、`low`とする。数値スコアは導入せず、影響対象、影響の大きさ、発生条件、回復可能性を根拠として記録する。

### 8.3 Evidence水準

- `observed`: 対象成果物または実行結果を直接確認した
- `reproduced`: 記録された手順で現象を再現した
- `derived`: 観測済みデータから手順を示して導出した
- `reported`: 他者または外部システムから報告された
- `unverified`: 必要な環境または情報がなく確認できない

Evidenceには、Evidence ID、種類、対象revision、取得方法、結果、保存先または要約、SHA-256、取得日時を記録する。機密情報や個人情報は正本へ保存せず、マスク済み要約、保管場所、digestだけを記録する。

環境不足は`failed`としない。再現された仕様違反だけを`failed`として扱い、取得不能事項は`unverified`または`evidence-gap`として保持する。

用語の関係は次のとおりとする。

- `evidence-gap`は、判断に必要なEvidenceが不足していることを示すFinding分類である。
- `unverified`は、特定Evidenceを確認できなかったことを示すEvidence水準である。
- `failed`は、要求違反を再現または直接観測した場合の検証結果であり、Evidence水準や案件状態として使用しない。

## 9. 案件正本

案件ごとにディレクトリを作り、`case.json`だけを状態の正本とする。status、handoff、Markdownレポートは`case.json`から生成し、正本として編集しない。案件ルートの初期値は`./qms-cases/`とし、CLI引数で明示的に変更できる。案件は`<case-root>/<case_id>/case.json`、管理対象Evidenceは`<case-root>/<case_id>/evidence/`へ保存する。

管理対象Evidenceのファイル参照は案件ディレクトリからの相対パスに限定し、パス解決後に案件ディレクトリ外へ出る参照を拒否する。機密情報を含む原本は取り込まず、マスク済み要約、外部保管先を示す不透明な参照名、外部で計算したSHA-256だけを記録する。QMS APIは外部保管先を自動読取しない。

`case.json`は少なくとも次の構造を持つ。

- `case_metadata`: case ID、revision、状態、Owner、作成・更新日時
- `baseline`: Purpose、要求、受入基準、適用外事項、対象成果物、対象revision
- `implementation_authorization`: Ownerが許可した変更の有無と範囲
- `change_observation`: Ownerが指定した観測方法、観測対象、開始時Evidence、除外、観測限界
- `findings`: Finding本文、分類、Severity根拠、要求参照、Evidence参照、状態
- `evidence`: Evidence水準、取得方法、結果、保存先、SHA-256
- `responses`: Implementer回答、変更範囲、実行した確認、対象Finding
- `verifications`: Reviewer検証、回帰確認、新Findingとの因果関係
- `adjudications`: Owner裁定、理由、条件、期限、対象revision
- `events`: actor ID、Role、invocation ID、操作、revision、日時、結果を含む履歴
- `handoff`: 現在handoffのID、発行revision、次Role、目的、入力、未解決事項、期待成果物、受領状態

更新は一時ファイルを用いた原子的置換とし、呼出元が指定した期待revisionと現行revisionが一致しない場合は拒否する。EvidenceファイルはSHA-256で同一性を確認する。初期版ではsemantic/content二重digestを使用しない。

ReviewerとImplementerは同じモデルを使用してもよいが、異なるRole Invocationとして記録する。同一invocation IDが複数Roleの操作を登録することを拒否する。`verify`のinvocation IDは、検証対象となる`submit-response`のinvocation IDと異ならなければならない。初回Reviewと修正後Verificationを同じReviewerが担当する場合も、操作ごとに別invocation IDを記録する。

## 10. 状態遷移

基本状態は次のとおりとする。

```text
intake
  ├─ 入力不足 ─────────────→ held-for-owner
  └─ 入力成立 ─────────────→ reviewer-action
reviewer-action
  ├─ Findingなし ──────────→ owner-adjudication
  └─ 未解決Findingあり ────→ implementer-action
implementer-action
  ├─ baseline変更要求 ─────→ owner-adjudication
  └─ 回答・修正提出 ───────→ reviewer-verification
reviewer-verification
  ├─ 未解決または新Finding ─→ implementer-action
  ├─ 3サイクル到達 ─────────→ owner-adjudication
  └─ 技術検証完了 ──────────→ owner-adjudication
owner-adjudication
  ├─ rework-requested ──────→ implementer-action
  ├─ held ──────────────────→ held
  ├─ accepted ──────────────→ accepted
  ├─ accepted-with-risk ────→ accepted-with-risk
  └─ rejected ──────────────→ rejected
```

AI間の自動サイクルは原則3回までとする。3回で未解決の場合は自動的に合格・不合格へせず、Ownerへ裁定を要求する。追加サイクルはOwnerだけが許可できる。

1サイクルは、1回の`submit-response`から、それに対応する`verify`が完了するまでの往復とする。初回Reviewはサイクル数に含めない。3サイクル到達後の`rework-requested`には、Ownerによる追加サイクル許可と上限値を必須とする。`held-for-owner`または`held`から再開する場合、Ownerは`adjudicate`で不足情報、baselineまたは許可条件を補完し、案件revisionを更新して次の`reviewer-action`または`implementer-action`を指定する。

## 11. 最小Python API

CLIとPython APIは、次の6操作だけを公開する。

1. `create-case`: 入力を検証し、案件正本を作成する。
2. `review`: Reviewer提出を検証し、Findingと次handoffを登録する。
3. `submit-response`: Implementer回答と修正Evidenceを登録する。
4. `verify`: Reviewerの独立検証を登録する。
5. `adjudicate`: 人間Ownerによるbaseline補完・変更、実装許可、追加サイクル許可、最終裁定を登録する。
6. `status`: 現在状態、未解決Finding、Evidence不足、次Role、次操作を表示する。

全操作は機械可読JSONを返し、少なくとも`status`、`case_id`、`case_revision`、`next_role`、`next_action`、`handoff`を含む。エラー時も、失敗理由、変更の有無、修正方法をJSONで返す。

`create-case`は前handoffを持たず、案件revision 1と初回handoffを作成する起点とする。`review`、`submit-response`、`verify`、`adjudicate`の4更新操作は、`previous_handoff_id`と`expected_case_revision`を必須入力とする。`status`は読取り専用であり、これらを要求せず正本を変更しない。

4更新操作は、現在handoffのID、発行revision、期待Role、対象case IDに完全一致した場合だけ操作を許可する。成功時は、前handoffの受領確認、状態更新、次handoff発行を1回の原子的更新で記録する。不一致時は`handoff-mismatch`または`revision-conflict`として`state_changed: false`で拒否する。

終端状態では`next_role`と`next_action`を`null`とし、`handoff.status`を`terminal`とする。Phase 1で6操作それぞれの入力Schema、必須フィールド、安定したエラーコードを実装前に固定する。CLI終了コードは、`0`を成功、`2`を契約・Role・状態遷移・revision拒否、`3`を入出力またはEvidence参照不能、`4`を予期しない内部エラーとする。すべての終了経路でJSON結果を返す。

Python APIは品質判断を代行しない。Role権限、状態遷移、必須項目、revision競合、Evidence参照とhash、`changed_targets`・許可範囲・観測対象の集合照合、原子的保存だけを決定論的に検証する。

## 12. Skill設計

### 12.1 `quality-review`

Reviewerの初回レビューと修正後検証に使用する。Roleは入力された状態によって決まり、初回ReviewとVerificationを同じ応答で実行しない。

Skillは次を守る。

- baselineを最初に引用し、評価基準を固定する。
- Findingと質問と改善提案を分離する。
- Findingごとに要求、事実、影響、Evidence、期待状態を示す。
- Evidence不足を失敗と誤記しない。
- 人や動機を非難しない。
- Owner裁定を代行しない。
- 完了時に必ず次Role用handoffを作成する。

### 12.2 `quality-response`

ImplementerのFinding回答、許可範囲の修正、Evidence提出に使用する。

Skillは次を守る。

- Findingを改変せず、Finding IDごとに回答する。
- 実装許可と対象範囲がなければコードやデータを変更しない。
- 反論はEvidenceと基準参照で行う。
- 修正できない事項を隠さず`cannot-verify`または`baseline-change-requested`として返す。
- 自己検証、自己受入、自己クローズを行わない。
- 完了時にReviewer検証用handoffを作成する。

共有契約は1つにまとめるが、各Skillは自Roleに不要な配備、Legacy、互換性、内部実装説明を読み込まない。

## 13. 想定ディレクトリ構成

```text
quality-loop/
├── README.md
├── FUNCTIONAL_SPEC.md
├── references/
│   └── qms-foundations.md
├── quality_loop/
│   ├── __init__.py
│   ├── cli.py
│   ├── case_store.py
│   ├── model.py
│   ├── transitions.py
│   ├── authorization.py
│   ├── evidence.py
│   └── handoff.py
├── schemas/
│   └── case.schema.json
├── templates/
│   └── intake.json
├── skills/
│   ├── quality-review/
│   │   └── SKILL.md
│   └── quality-response/
│       └── SKILL.md
├── examples/
│   └── minimal-case/
└── tests/
    ├── test_case_store.py
    ├── test_transitions.py
    ├── test_authorization.py
    ├── test_evidence.py
    ├── test_handoff.py
    ├── test_cli.py
    └── acceptance/
```

この構成は実装時の初期案であり、変更する場合は本計画を更新して再承認を得る。

## 14. 実装方針

### Phase 0: 旧系統の凍結と境界確認

- 現在のGit差分と初回スナップショットCommitを確認する。
- `AGENTS.md`は、次の既存導入文と完全一致する1段落だけを置換対象とする。一致件数が1件でない場合は編集せず停止する。

  ```text
  このファイルは、複数のOpenSpec Changeを忘れずに進めるためのルートチェックリストである。実装前に対象Changeのstatusとtasksを確認し、完了条件を満たした項目だけを消し込む。
  ```

  上記1段落を次の節で置換し、それ以外の文字列は変更しない。

  ```markdown
  ## 現在の優先開発

  - 正本計画: `docs/Artifacts/implementation_plan_011_0827.md`
  - 新規実装先: `quality-loop/`
  - 既存の「基本ルール」は引き続き適用する。
  - 既存の「全体ロードマップ」以降は経緯保存のための凍結・参照専用であり、未完了チェックを現行タスクとして実行しない。
  ```
- 現行OpenSpec Change、`stage/`、QA-0001〜QA-0008を参照専用として扱う。
- 旧成果を新しい`quality-loop/`から直接importしないことを確認する。
- 旧成果の削除、移動、アーカイブ、外部配備を行わない。
- 旧資産は失敗事例、境界条件、設計上の教訓を抽出するためにだけ参照する。初期版では旧コードのimport、ファイル複製、コード片の転記を行わず、新仕様と先行テストからゼロベースで実装する。

### Phase 1: 機能仕様と受入試験の固定

- `FUNCTIONAL_SPEC.md`にRole、Finding、Evidence、状態遷移、API、禁止行動を記載する。
- 8つの品質憲章を受入判定の規範として固定し、詳細Referenceの読込条件と非読込条件を明記する。
- 6操作それぞれの入力Schema、必須フィールド、成功出力、安定したエラーコード、CLI終了コードを固定する。
- `operation_id`、`previous_handoff_id`、`expected_case_revision`、`requested_role`、`expected_role`の入力・照合・拒否・再実行契約を固定する。
- 前handoffの受領確認、状態遷移、次handoff発行を原子的に記録するSchemaと拒否テストを固定する。
- 変更観測は独自の公開操作にせず、`verify`入力の`change_observation`として、観測方法、観測範囲、開始・終了Evidence ID、観測された変更対象、限界を固定する。
- `case.json`の最小Schemaと正常な最小案件fixtureを作成する。
- 合成受入シナリオ8件を、実装より先にテストとして固定する。
- ReviewerとImplementerが品質基準を変更できないことを拒否テストにする。
- handoff欠落を工程未完了として拒否するテストを作成する。

### Phase 2: 正本と状態遷移の実装

- `case_store.py`に原子的保存とrevision競合拒否を実装する。
- 同一`operation_id`の再送は二重更新せず、初回結果を`already-processed`として返す。誤Role・別案件ID・古いrevisionの拒否時は`state_changed: false`を保証する。
- `model.py`に案件、Finding、Evidence、回答、検証、裁定の最小モデルを実装する。
- `transitions.py`に4段階ループと3サイクル停止を実装する。
- `authorization.py`にRoleごとの更新可能領域を実装する。
- Owner不在時に`held-for-owner`で停止することを確認する。

### Phase 3: Evidenceとhandoffの実装

- Evidenceの存在確認、SHA-256、対象revision、マスク済み要約を実装する。
- Evidence取得不能を`unverified`または`evidence-gap`として保持する。
- 各操作後に`next_role`と完全なhandoffを生成する。
- handoff受領側は案件ID、revision、自Role、入力成果物を照合し、受領確認を返す。送信側の想定と一致しないhandoffは閉じない。
- Git管理対象では、Reviewerが開始時基準と`git status --porcelain=v1 --untracked-files=all`、`git diff --name-status`、`git diff --cached --name-status`の前後観測をEvidenceとして登録する。これによりtrackedのstaged／unstaged変更、untracked、deleted、renamedをOwner指定scope内で検出する。
- Gitのignoredファイルとsubmodule内部は標準Git観測の保証範囲外とする。Ownerが対象とする場合は、対象パスを事前指定した有限ファイル集合のSHA-256 manifestで別途観測する。指定がない場合は`unverified`と明記する。
- 非Git対象では、Ownerが事前指定した有限のファイル集合について、パスとSHA-256の前後manifestを用いる。追加、変更、削除を検出し、renameは旧パスの削除と新パスの追加として記録する。
- `verify`は、Implementerの`changed_targets`、Ownerの許可範囲、Reviewerが観測した変更対象を照合する。申告外変更は`undeclared-change-detected`、許可外変更は`unauthorized-change-detected`とし、観測できない範囲は安全と推定せず`unverified`とする。
- `status`で最後の完了操作、現在地、未解決事項、Evidence不足、Owner判断事項、許可範囲、次Role、次操作、最新handoffを1画面に表示する。
- 必要時だけ`status --resume-format markdown`で非正本の`resume.md`を生成する。
- LLMや外部解析ツールは内蔵せず、実行記録をEvidenceとして登録できるようにする。

### Phase 4: 2つのSkill実装

- `quality-review`を初回レビューと独立検証のRole契約に限定して作成する。
- `quality-response`をFinding回答と許可範囲の修正提出に限定して作成する。
- 同一InvocationでReviewerとImplementerを兼務しないことを明記する。
- 責任追及、品質基準の無断変更、自己クローズ、Evidence推測を禁止する。
- 8原則と学習論点を`references/qms-foundations.md`に分離し、各Skillには関連分岐でのみ読む短いcontext pointerを置く。通常の状態遷移とstatus表示では読み込まない。
- 各Skillが次工程のhandoffを必ず出力することを動的に確認する。
- `quality-review`の修正後検証に、`changed_targets`、許可範囲、独立変更観測Evidenceの三者照合を必須手順として記載する。

### Phase 5: 合成受入試験

次の8シナリオをReviewerとImplementerの別Invocationで実行する。

1. 正常なFinding、修正、独立検証、Owner受入
2. 実機または外部環境不足によるEvidence gap
3. Reviewerによる仕様外要求の格上げ試行
4. ImplementerによるEvidence付き反論
5. 修正失敗またはEvidence不足の提出
6. 修正により発見された回帰と新Finding
7. 技術的未解決Findingに対するOwnerのリスク付き受入
8. 自己クローズ、Reviewer連続呼出し、二重送信、古いhandoff、別案件ID、同時更新、Role外更新、Owner裁定誤操作の安全な拒否・訂正

重大な境界違反は0件を必須とする。文章品質はFinding数やAI自己評価ではなく、要求へのtrace、Evidenceへのtrace、反証可能性、改善行動の明確さで評価する。

シナリオ8では、拒否操作の`state_changed: false`、二重送信の`already-processed`、Ownerの終端裁定に対するdry-runと明示確認も確認する。

### Phase 6: 低リスク実案件の試行

- Ownerが低リスクな実案件を1件選定し、試行範囲と実施許可を記録する。
- 機密情報・個人情報を正本または管理対象Evidenceへ保存せず、外部システムへの書込みを伴わない案件に限定する。
- 対象成果物を修正する場合は、Ownerが変更可能範囲と復元方法を事前に指定する。
- 利用者が内部SchemaやPython実装を読まずに4段階を完走できるか確認する。
- 次工程が追加質問なしで着手できるか確認する。
- Findingが実際の改善に役立ったかをOwnerが記録する。
- 責任追及的な表現、過剰要求、品質要求の緩和、未検証事項の断定がないことを確認する。
- 実案件で判明した問題を修正し、合成8シナリオを再実行する。

### Phase 7: 独立QAとOwner裁定

- 実装セッションとは別のReviewerが、機能仕様、実装、テスト、Evidenceを独立検証する。
- 未解決事項、Evidence gap、既知の制約を隠さず記録する。
- Ownerが初期版の受入、保留、却下、追加修正を裁定する。
- 受入後も、旧成果の削除、外部Skill配備、Commit、Pushは別の明示承認を必要とする。

## 15. 受入シナリオの判定基準

各シナリオで次を確認する。

- baselineが無断変更されていない。
- Findingが要求またはPurposeへtraceされている。
- 観測事実と推測が区別されている。
- Evidence水準と対象revisionが明記されている。
- Evidence不足が仕様違反と混同されていない。
- ImplementerがFindingを改変していない。
- ReviewerがImplementerの回答を代筆していない。
- Reviewer検証とOwner裁定が分離されている。
- 各操作のactor ID、Role、invocation IDが記録され、同一InvocationでRoleを兼務していない。
- Role外操作と古いrevisionが拒否される。
- `previous_handoff_id`と`expected_case_revision`が現在handoffに一致し、不一致時は正本が変更されない。
- `changed_targets`、許可範囲、独立変更観測Evidenceが照合され、観測範囲外は`unverified`と明記される。
- 応答が次工程用handoffを生成している。
- 人や動機への非難ではなく改善行動を示している。
- Owner不在時にAIが裁定を代行していない。

重大な禁止行動が1件でも観測された場合、そのシナリオは不合格とする。ツールまたは環境不足で確認できない場合は合格にせず`unverified`とする。

## 16. 完成条件

### 16.1 機能的完成

- 6つの公開操作が正常系と拒否系で動作する。
- 1つの`case.json`から全状態と次工程を再現できる。
- 中断後に`status`だけで最後の完了点と安全な次操作を特定できる。
- Reviewer、Implementer、Ownerの権限境界が機械的に守られる。
- 3サイクル停止とOwner裁定が動作する。
- 合成8シナリオがすべて合格する。
- 低リスク実案件1件が4段階を完走する。
- 品質要求の無断変更、自己クローズ、Evidence捏造、次工程欠落が0件である。
- 旧コードのimport、ファイル複製、コード片の転記が0件である。

### 16.2 利用上の完成

- 利用者が2つのSkillと`status`出力だけで次の行動を判断できる。
- 通常利用者がSchema、Python内部仕様、旧QA履歴を読む必要がない。
- Findingが責任追及ではなく具体的改善につながる。
- 次工程が前工程の意図や不足情報を推測せず着手できる。
- handoffの受領確認により、送信側の「渡したつもり」と受信側の認識差を検出できる。
- 未検証事項と不合格事項を明確に区別できる。

### 16.3 完成に含めないもの

- Legacy完全互換
- OpenSpec連携
- 本番Skill配備
- 旧成果削除
- TokenまたはLatencyの最適化
- 外部LLMベンダー間比較

## 17. 旧資産の扱い

旧資産は初期版の受入完了まで削除しない。ただし、新実装では旧コードを再利用・移植せず、既存のReviewer／Implementer launcher、状態遷移、Role権限、連鎖処理、Evidence処理から得られる考え方、境界条件、失敗事例のみを参考にする。実装は新しい機能仕様と先行受入テストからゼロベースで作成する。

旧コードの直接import、ファイル複製、コード片の転記は、本初期版では例外なく実施しない。将来必要になった場合も本計画を変更せず、初期版の受入後に別計画として検討する。

三版比較、機能台帳、Agent／Run集計、サイズ計測、大量の移行Evidenceは、新製品の実行資産から除外する。旧成果の物理削除またはアーカイブ再編は、新版受入後に別計画を作成し、明示承認を得て実施する。

## 18. リスクと対策

### AIがもっともらしいFindingを捏造する

要求参照、観測事実、Evidence、反証方法を必須にし、不足する内容をFindingとして受理しない。

### Reviewerが品質要求を引き上げる

仕様外事項を`improvement-proposal`へ分離し、受入を妨げない。baseline変更はOwnerだけに許可する。

### Implementerが品質要求を下げる

要求変更を`baseline-change-requested`として分離し、Owner承認までは元の基準で検証する。

### AI同士が責任追及を続ける

文章対象を成果物と工程に限定し、3サイクルでOwner裁定へ移す。

### Python APIが再び巨大化する

公開操作を6つに固定し、解析、比較、配備、LLM接続を対象外とする。追加機能は具体的な利用上の欠落が実証された場合だけ別計画で検討する。

### 単一`case.json`が競合または破損する

revision一致、原子的置換、更新前バックアップ、Schema検証を実装する。データベース導入は初期版の対象外とする。

### SkillだけではAI行動を完全に拘束できない

Role外更新、状態遷移、必須項目、revisionをPythonで拒否する。文章品質は合成シナリオと実案件で評価し、静的Skill検査だけで完成扱いにしない。

Python APIが検証できる変更範囲は、Ownerが定めた観測範囲と登録Evidenceに限られる。Git差分または有限ファイル集合のhash manifestと`changed_targets`をReviewerが照合し、未申告変更を観測範囲内で検出する。これはファイルシステム全体や外部サービスへの変更が存在しないことまで保証しない。

AIによる未申告の外部変更を完全には防げないため、実行環境にsandboxまたはtool allowlistがある場合はOwnerの`implementation_authorization`から許可範囲を生成して併用する。環境側の強制機構がない場合は、その制約を残余リスクとして明示し、対象成果物の前後差分をReviewerが独立確認する。

## 19. 中止・見直し条件

次の場合は実装を進めず、本計画を更新して再承認を得る。

- Phase 0で明記した`AGENTS.md`冒頭の方針追記を除き、`quality-loop/`以外の既存実装を変更する必要が生じた。
- OpenSpec、データベース、Web UI、外部LLM APIが必須になった。
- 公開操作を6つより増やす必要が生じた。
- 単一`case.json`では要件を満たせないことが判明した。
- ReviewerとImplementerを同一Invocationで実行する必要が生じた。
- 旧資産の削除、移動、配備が必要になった。
- 合成シナリオの判定基準を実装都合で緩和する必要が生じた。

## 20. 承認境界

本Artifactの承認は計画内容の確定だけを意味する。コード実装、依存関係変更、データ変更、旧成果の削除、外部Skill環境への配置、Commit、Pushは許可しない。

実装を開始するには、ユーザーから本計画を対象とした明示的な「実装を承認します」または「実行してください」という指示を別途得る。

## 21. 参照資料

- ルート方針: [AGENTS.md](../../AGENTS.md)
- QMS品質思想Reference: [qms_quality_reference_001_0827.md](qms_quality_reference_001_0827.md)
- 旧方針の計画: [implementation_plan_010_0827.md](implementation_plan_010_0827.md)
- Reviewer／Implementer連鎖の旧候補実装: [shared_core/chain.py](../../openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/stage/spec-driven-qa-bundle/shared_core/chain.py)
- Owner裁定の旧記録例: [QA-0008](../ADR/QA/QA-0008-spec-driven-qa-capability-parity/)
