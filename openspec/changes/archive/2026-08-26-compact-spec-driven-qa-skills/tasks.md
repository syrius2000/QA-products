## 1. 基準化と作業境界

- [x] 1.1 現行Review SkillとAuthor Skillの対象ファイル、Manifest、公開CLI、入口、依存関係を読み取り専用で収集し、作業開始時のハッシュ・行数・バイト数を記録する
- [x] 1.2 130ファイルの機能ID、引数、終了コード、stdout/stderr、JSON必須フィールド、副作用、拒否条件、役割分類を台帳化し、Review固有・Author固有・共通の分類を検査する
- [x] 1.3 Contract v1.2候補を未検証状態のまま基準候補として固定し、旧版・候補版・圧縮版を混同しない比較メタデータを作成する
- [x] 1.4 ステージング作業領域、対象Manifest、backup先、rollback対象を定義し、外部Skill配置先を変更しないことをdry-runで確認する
- [x] 1.5 Manifest対象を決定論的に集計する標準ライブラリのみの`measure_size.py`をPhase 0成果物として作成し、空行・コメント・テスト・サンプル・Schemaの含否、行数・バイト数・常駐対象をJSONで出力することをfixtureで確認する

## 2. 基準fixtureと比較ハーネス

- [x] 2.1 既存正常系と最小完全サイクルをgolden fixtureとして収集し、旧版の終了コード、構造化出力、状態、副作用を保存する
- [x] 2.2 stale digest、revision競合、秘密情報、未許可操作、自己検証、自己クローズ、未知majorをnegative fixtureとして作成し、旧版の拒否結果を記録する
- [x] 2.3 Reviewer生成handoffからAuthor提出、Reviewer統合までのcross-skill fixtureを作成し、各段階の入力・出力・書込み境界を確認する
- [x] 2.4 v1.0/v1.1読み取り互換fixtureと、ファイル・行数・バイト数・常駐読み込み量を測るsize fixtureを作成する
- [x] 2.5 3版の結果を終了コード、必須JSONフィールド、状態、副作用で正規化して比較するハーネスを作成し、OpenSpec `spec.md`を判定正本、Bundle内のdigest固定された`SPEC.md`をその派生仕様、旧版・未検証候補版の挙動を比較Evidenceとして扱う優先順位を明記した差分レポートを代表fixtureで再現する

## 3. 共有コアとBundle構成

- [x] 3.1 `shared_core`、Reviewer入口、Author入口、Schema、Template、fixture、evalのステージングBundleを作成し、Bundle Validatorが期待構成を検出することを確認する
- [x] 3.2 契約フィールド、状態、Finding、Evidence、digest対象の正本Schemaを整理し、既存の受理・拒否fixtureがSchema検証を通過することを確認する
- [x] 3.3 契約・digest、状態遷移、Evidence・秘密情報、リンク、入出力・終了コード、役割認可を責務別共有モジュールへ抽出し、標準ライブラリだけでimportできることを確認する
- [x] 3.4 CLI Facadeに役割情報、公開サブコマンド、引数、終了コード、JSON出力を実装し、共有コア不足時にfail-closedとなることを確認する
- [x] 3.5 Reviewer / Author各Launcherが実ファイル位置からBundleルートを解決し、`shared_core`の存在・Manifest・内容digestを検証してからBundleルートだけをimport対象へ追加すること、`PYTHONPATH`・cwd・未検証リンクでは起動できないことをstandalone配置negative testで確認する

## 4. Reviewer / Author入口と権限

- [x] 4.1 Reviewer入口を作成し、独立レビュー、ケース作成、handoff、Reviewer検証、closeの許可操作と次の参照先が短い`SKILL.md`で判別できることを確認する
- [x] 4.2 Author入口を作成し、handoff読取、response、submission、実行ポリシー、Reviewerへ戻す条件が短い`SKILL.md`で判別できることを確認する
- [x] 4.3 AuthorからReviewer専用操作、Reviewerから無許可のAuthor提出作成、Authorから正本・イベント・closureへの直接書込みを拒否するnegative testを通す
- [x] 4.4 許可されたReviewer統合だけがAuthor提出を正本候補へ反映でき、submission hash、base revision、対象Finding、Evidence整合性を検証することを確認する
- [x] 4.5 認可失敗の非ゼロ終了コードと構造化診断を確認し、秘密値、未許可パスの内容、内部Tokenがstdout/stderrへ出力されないことを確認する

## 5. 互換層と契約不変条件

- [x] 5.1 旧CLI入口から共有コアを呼ぶ互換層を作成し、既存引数で成功・失敗分類、終了コード、JSON必須フィールドが同等になることを比較fixtureで確認する
- [x] 5.2 handoffのsemantic/content digest、case revision、期待digest、状態遷移を検証し、stale・改ざん・競合入力が正本を変更せず拒否されることを確認する
- [x] 5.3 Evidenceの`unverified`、`evidence-gap`、`risk-accepted`、`fixed-and-verified`の区別を実装し、Owner判断なしの技術的未検証が受入済みへ変換されないことを確認する
- [x] 5.4 v1.0/v1.1を読み取り互換で処理し、履歴を変更しないこと、未知majorを安全停止することをlegacy fixtureで確認する
- [x] 5.5 相対リンク、`file://`拒否、外部参照の明示、秘密情報検出・マスク・出力拒否を検証する

## 6. 文書・Schema・派生物の蒸留

- [x] 6.1 分類、証拠階層、状態遷移、安全規則を重複なく`SPEC.md`へ整理し、既存の必須判断シナリオが仕様文書から追跡できることを確認する
- [x] 6.2 ReviewerとAuthorの`SKILL.md`を役割別行動規則、禁止事項、返却先、参照先へ整理し、初回読み込みだけで次の行動を判別できることを確認する
- [x] 6.3 必須フィールドを含む最小完全Templateとsingle-cycle / multi-cycleの代表例を残し、正常系・拒否系・複数cycleの再現性を確認する
- [x] 6.4 README、INSTALL、MANIFEST、CHANGELOG、adapter、evalの参照先を新Bundle構成へ更新し、リンク・import・Manifest検証を通す
- [x] 6.5 JSON Schemaを統合または維持する判断を行い、変更する場合は旧Schemaの全受理・拒否fixtureとの互換結果を記録する

## 7. 差分QAとサイズ評価

- [x] 7.1 旧版、Contract v1.2候補、圧縮版にgolden・negative・cross-skill・legacy fixtureを一括実行し、OpenSpec `spec.md`を正本とする裁定結果、契約差分、旧版互換差分、診断文差分を分離したレポートを作成する
- [x] 7.2 自己レビュー、自己検証、自己クローズ、Reviewer正本変更、未知Finding受理、誤実装開始が0件であることをnegative evalで確認する
- [ ] 7.3 機能ID欠落、必須Schema・Template欠落、終了コード変更、JSON必須フィールド欠落、未説明の拒否差分が0件であることを確認する
- [x] 7.4 Manifest条件でファイル数、行数、バイト数、常駐読み込み量を測定し、合計1,760行以下、または未達理由と能力維持判断を記録する
- [x] 7.5 単体、統合、subprocess、Bundle Validator、eval、構文検査を実行し、実行不能な項目は`unverified`として理由と再検証条件を記録する

## 8. 配備準備と完了判定

- [ ] 8.1 stagingからのdry-runで全差分、対象パス、backup対象、rollback対象を表示し、Manifest外のパスを変更しないことを確認する
- [ ] 8.2 backupから限定対象を復元するrollbackを実行し、復元後のSkill構成、Manifest、読み取り互換性を確認する
- [ ] 8.3 実装結果、fixture/eval結果、サイズ測定、残余リスク、未検証項目、配備差分をChange Evidenceへ記録する
- [ ] 8.4 Contract v1.2候補の未完了検証を受入済みと誤記せず、圧縮Changeの技術判定とOwnerのリスク判断を分離して記録する
- [ ] 8.5 すべての仕様・差分QA・rollbackゲートが合格した後、明示承認を取得するまで外部配置、旧版削除、commit、pushを実行しないことを確認する
