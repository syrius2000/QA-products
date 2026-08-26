## Purpose

このCapabilityは、ReviewerとAuthorの役割、安全境界、既存契約、互換性を維持したまま、2つのQA Skillを共有コアと薄い役割別入口へ整理し、検証可能な形で配布物と常駐コンテキストを小さくするためのものである。

## ADDED Requirements

### Requirement: ReviewerとAuthorの役割入口を分離する

圧縮後の配布物は、`spec-driven-qa-review`と`spec-driven-qa-author-response`という役割名を維持し、それぞれの入口から許可された操作だけを実行可能にしなければならない（SHALL）。Reviewer入口は独立レビュー、handoff生成、Reviewer検証、ケース終了を扱い、Author入口はhandoff読取、Author Response、提出保存、実行ポリシー確認を扱う。共有コアは入口名だけでなく実行時の役割情報も検証しなければならない。

#### Scenario: Reviewer入口がReviewer操作を実行できる

- **WHEN** Reviewer役割で独立レビューまたはhandoff生成を要求する
- **THEN** 共有コアは許可されたReviewer操作を実行し、結果と終了コードを返す

#### Scenario: Author入口からReviewer専用操作を要求する

- **WHEN** Author役割で独立検証、Reviewer統合、またはケースクローズを要求する
- **THEN** 共有コアは操作を拒否し、正本・検証結果・closureを変更しない

#### Scenario: ReviewerがAuthor専用の提出保存を要求する

- **WHEN** Reviewer役割でAuthor専用の提出保存操作を、許可されたReviewer統合操作以外の経路から要求する
- **THEN** 共有コアは操作を拒否し、提出物とイベントを新規作成しない

### Requirement: Contract v1.2候補の安全不変条件を維持する

圧縮後の実装は、Contract v1.2候補で定義されたhandoffの信頼境界、semantic/content digest、case revision、状態遷移、Evidence分類、秘密情報防護、`risk-accepted`と`fixed-and-verified`の区別を同等に検証しなければならない（SHALL）。Contract v1.2候補が未検証であることを、圧縮後の実装の受入済み根拠として扱ってはならない。

#### Scenario: 古いhandoffまたはrevisionを提出する

- **WHEN** Author提出の期待digestまたはcase revisionがReviewer正本の現在値と一致しない
- **THEN** 提出は拒否され、正本とケース状態は変更されない

#### Scenario: AuthorがReviewer正本を直接変更する

- **WHEN** Authorの入力がFinding、severity、verification、events、closureなど許可されていない正本フィールドを変更しようとする
- **THEN** 変更は拒否され、秘密情報を含まない診断情報だけが返される

#### Scenario: 技術的未検証を受入済みと偽装する

- **WHEN** Evidenceが`unverified`または`evidence-gap`であり、Ownerの明示的なリスク判断が存在しない
- **THEN** 結果は技術的な`fixed-and-verified`へ変換されず、再検証または判断待ちとして保持される

### Requirement: 旧入口と公開契約を互換維持する

圧縮後の配布物は、既存利用者が依存するCLI入口、引数、終了コード、JSON出力の必須フィールド、テンプレートの必須フィールドを、非互換変更として明示されない限り維持しなければならない（SHALL）。旧形式の入力は読み取り互換アダプターで扱い、未知のmajor契約は安全停止しなければならない。

#### Scenario: 旧CLI入口を既存引数で呼び出す

- **WHEN** 圧縮前に成功していたCLI入口を同じ引数とfixtureで実行する
- **THEN** 圧縮後も同等の成功・失敗分類、終了コード、必須JSONフィールドを返す

#### Scenario: 旧Contract形式を読み取る

- **WHEN** v1.0またはv1.1の読み取り可能なQAケースを入力する
- **THEN** 履歴を書き換えず、読み取り互換アダプターとして内容を解釈する

#### Scenario: 未知major契約を入力する

- **WHEN** サポート対象外のmajor versionを含むhandoffまたは提出物を入力する
- **THEN** システムは安全停止し、正本・提出物・イベントを変更しない

### Requirement: 機能台帳と差分検証で能力維持を証明する

圧縮版を配布候補とする前に、圧縮前のReviewおよびAuthorの全公開機能を、機能ID、引数、終了コード、出力形式、拒否条件、副作用、役割分類とともに台帳化しなければならない（SHALL）。圧縮前版、Contract v1.2候補、圧縮版は共通fixtureで比較し、正常系だけでなく拒否系、境界系、競合、秘密情報、権限逸脱、cross-skill経路を検証しなければならない。

#### Scenario: 機能IDに対応する圧縮版の実装がある

- **WHEN** 台帳に登録された公開機能を圧縮版で実行する
- **THEN** 対応する実装または互換アダプターが存在し、結果が台帳の契約と比較可能である

#### Scenario: 正常系の比較を実行する

- **WHEN** 同一の正常系fixtureを圧縮前版、Contract v1.2候補、圧縮版へ入力する
- **THEN** 契約上同等の出力、終了コード、状態変化が得られ、差分があれば理由を記録できる

#### Scenario: 役割逸脱を比較する

- **WHEN** Authorによる自己検証、自己クローズ、Reviewer正本変更を含むnegative fixtureを実行する
- **THEN** すべての候補版で圧縮版が拒否し、誤実装開始、正本変更、自己クローズを0件とする

### Requirement: 常駐コンテキストと配布サイズを予算内に収める

圧縮後の2つの`SKILL.md`は、各役割の次アクション、禁止事項、返却先、参照先だけを常駐規則として提示し、詳細仕様の重複を持ってはならない（SHALL）。配布物全体は、テスト、正本仕様、必須テンプレート、最小完全サンプル、安全境界を削らず、合計1,760行以下を第一目標とする。

#### Scenario: Reviewer Skillを初回読み込みする

- **WHEN** Reviewer入口を読み込む
- **THEN** Reviewerが最初に行うべき確認、禁止事項、次の参照先が短い入口だけで判別できる

#### Scenario: Author Skillを初回読み込みする

- **WHEN** Author入口を読み込む
- **THEN** Authorが参照可能な入力、提出可能な成果物、Reviewerへ戻す条件、禁止操作が判別できる

#### Scenario: サイズ目標を測定する

- **WHEN** 配布対象をmanifestの集計条件で測定する
- **THEN** 合計行数、ファイル数、バイト数、常駐読み込み量を記録し、1,760行を超える場合は未達理由と能力維持上の判断を記録する

### Requirement: ステージングとrollbackの境界を守る

圧縮版はステージング領域で生成・検証し、差分表示、backup、rollback手順、残余リスク記録が確認されるまでグローバルSkill配置先を変更してはならない（MUST）。旧版の削除、外部配置、commit、pushは、本Changeの検証合格と別途の明示承認後に限る。

#### Scenario: ステージング版の検証が失敗する

- **WHEN** manifest、構文、差分fixture、役割negative test、またはrollback検証のいずれかが失敗する
- **THEN** グローバルSkillは変更せず、圧縮版を未受入として失敗理由を記録する

#### Scenario: 明示承認なしに配備を要求する

- **WHEN** 検証結果が合格でも、外部配置または旧版削除の明示承認が存在しない
- **THEN** 配備操作は実行せず、現在のステージング成果物とrollback情報を保持する

#### Scenario: rollbackを実行する

- **WHEN** 配備後の互換性確認で問題が検出され、承認済みbackupを指定する
- **THEN** 対象を限定して旧版を復元し、復元結果と残余リスクを記録する
