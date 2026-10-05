## Purpose

Reviewerから受け取った公開handoffに基づき、AuthorがFinding別の回答または修正提出を安全に作成し、Reviewerによる独立検証へ渡せるようにする。

## ADDED Requirements

### Requirement: Author回答をFinding単位で提出する

Authorは公開handoffに列挙されたFindingごとに、許可されたDispositionと根拠を含む回答提出を作成しなければならない。未知のFinding ID、空の根拠、handoffにない対象は提出に含めてはならない。これらの条件はMUST（必須）とする。

#### Scenario: Findingを受理する回答を提出する

- **WHEN** Authorがhandoffに存在するFinding IDについて`accepted`と具体的な理由を提出する
- **THEN** Author提出は新規`submission_id`を持つ回答として保存され、Reviewer検証待ちになる

#### Scenario: 未知Findingを提出する

- **WHEN** Author提出にhandoffまたはQA正本に存在しないFinding IDが含まれる
- **THEN** Validatorは提出を拒否し、Reviewer正本を変更しない

### Requirement: 修正提出の整合性を検証する

Authorの修正提出は、handoffの基準revisionとdigestを参照し、Disposition、実行テスト、Evidence、`modified_files`を記録しなければならない。Authorは技術修正を提出できるが、修正済みまたはクローズ済みと自己判定してはならない。これらの条件はMUST（必須）とする。

#### Scenario: 修正提出をReviewer検証へ渡す

- **WHEN** Authorが基準revisionに対応する`fix-submitted`と、存在する相対Evidenceおよび変更ファイルを提出する
- **THEN** Validatorは提出を受理し、Reviewerによる独立検証を要求する

#### Scenario: stale handoffを参照する修正を提出する

- **WHEN** Author提出が現行正本と一致しないdigestのhandoffを参照する
- **THEN** Validatorは`inconsistent-qa-state`相当で拒否し、正本を更新しない

### Requirement: Authorの書込み境界を強制する

Authorの書込み先は許可された回答提出ディレクトリに限定し、Reviewer所有のFinding、review、handoff、events、closureを直接変更してはならない。これらの条件はMUST（必須）とする。

#### Scenario: AuthorがReviewer正本を変更しようとする

- **WHEN** AuthorがReviewer所有ファイルまたはケース終了状態への書込みを試みる
- **THEN** 実行ポリシーは拒否し、許可された提出先への記録を要求する

#### Scenario: Authorが自己クローズを要求する

- **WHEN** Author提出が`closed`または`fixed-and-verified`を自ら設定する
- **THEN** Validatorは拒否し、Reviewer検証へ差し戻す

### Requirement: 依存欠落環境でも提出検証を継続する

Author提出の検証は必須依存が利用できない場合でも、標準ライブラリによる安全なフォールバックまたは明示的な非成功結果を返し、偽陽性の受理や未記録のクラッシュを発生させてはならない。これらの条件はMUST（必須）とする。

#### Scenario: YAML依存がない環境で検証する

- **WHEN** 任意依存のYAMLライブラリが存在しない環境でAuthor提出を検証する
- **THEN** 検証は標準機能で継続するか、理由を明示した`unverified`／`evidence-gap`として停止する
