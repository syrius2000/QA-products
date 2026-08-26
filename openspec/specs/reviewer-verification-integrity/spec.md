# reviewer-verification-integrity Specification

## Purpose

Reviewer が Author 提出を受理する際に、handoff digest の鮮度と Evidence／変更ファイル参照の実在を機械検証し、偽陽性の検証成功と handoff 完全性の過大主張を防ぐ。

## Requirements

### Requirement: Stale handoff digest を拒否する

Reviewer の提出検証は、入力 handoff の `semantic_digest` および `content_digest` を現行 QA 正本から再計算した値と照合しなければならず、いずれかが不一致の場合は提出を受理してはならない。これらの条件は MUST とする。

#### Scenario: semantic_digest が stale な handoff を拒否する

- **WHEN** Author 提出が参照する handoff の `semantic_digest` が現行正本から再計算した値と一致しない
- **THEN** Reviewer 検証は非ゼロ終了で拒否し、Finding 状態を `fixed-and-verified` へ更新しない

#### Scenario: content_digest のみが stale な handoff を拒否する

- **WHEN** `semantic_digest` は一致するが `content_digest` が現行正本と一致しない handoff を用いて検証する
- **THEN** Reviewer 検証は受理せず、handoff 再生成を要求する診断を返し、正本を変更しない

#### Scenario: 鮮度が一致する handoff で検証を継続する

- **WHEN** handoff の両 digest が現行正本と一致し、他の必須フィールドも満たす
- **THEN** Reviewer 検証は digest 理由では拒否せず、後続の revision／Evidence 検査へ進む

### Requirement: リポジトリ相対 Evidence パスの実在を検証する

Author 提出の `test_evidence` がリポジトリ相対パスとして解釈可能な場合、Reviewer 検証はそのパスが対象ワークスペース上に存在することを確認しなければならない。存在しないパスを成功 Evidence として受理してはならない。非パスの自由記述は非空であることを必須とし、パス実在検査の対象外としてよい。

#### Scenario: 存在する相対パス Evidence を受理する

- **WHEN** `test_evidence` が存在するリポジトリ相対パスを指し、他の検証条件も満たす
- **THEN** Reviewer 検証は Evidence パス理由では拒否しない

#### Scenario: 存在しない相対パス Evidence を拒否する

- **WHEN** `test_evidence` がリポジトリ相対パスとして解釈できるが対象パスが存在しない
- **THEN** Reviewer 検証は提出を拒否し、成功判定や `fixed-and-verified` を記録しない

#### Scenario: 非パスの非空 Evidence 記述を許容する

- **WHEN** `test_evidence` がパスではない非空の自由記述である
- **THEN** Reviewer 検証はパス実在検査を適用せず、空文字のみを Evidence 不足として拒否する

### Requirement: modified_files の存在を検証する

Author 提出に `modified_files` が含まれる場合、Reviewer 検証は列挙された各パスが対象ワークスペース上に存在することを確認しなければならない。1 件でも欠落があれば提出を拒否しなければならない。変更ファイル一覧を要求する提出では、空または欠落の `modified_files` を成功として扱ってはならない。

#### Scenario: すべての modified_files が存在する提出を受理する

- **WHEN** 提出の `modified_files` が 1 件以上あり、すべてが存在するパスである
- **THEN** Reviewer 検証はファイル欠落理由では拒否しない

#### Scenario: 欠落パスを含む modified_files を拒否する

- **WHEN** `modified_files` のいずれかのパスが対象ワークスペースに存在しない
- **THEN** Reviewer 検証は提出を拒否し、正本の Finding 技術状態を成功へ進めない

#### Scenario: 要求があるのに modified_files が空または欠落なら拒否する

- **WHEN** handoff または検証契約が変更ファイル一覧を要求しているのに、提出の `modified_files` が欠落または空配列である
- **THEN** Reviewer 検証は提出を拒否する

### Requirement: 厳密化の自動テストを提供する

本 Capability の stale digest 拒否、Evidence パス実在拒否、`modified_files` 欠落拒否は、再現可能な自動テスト（golden および negative）で確認できなければならない。テスト未整備のまま完了主張をしてはならない。

#### Scenario: stale digest の negative テストが失敗を検出する

- **WHEN** 正本と不一致の digest を持つ handoff 入力で検証を実行する自動テストを走らせる
- **THEN** テストは検証拒否を期待どおり観測し、偽陽性の成功を許容しない

#### Scenario: Evidence パス欠落と modified_files 欠落の negative テストが失敗を検出する

- **WHEN** 存在しない Evidence パス、または欠落を含む `modified_files` を用いた検証を自動テストする
- **THEN** 各ケースで拒否が観測され、成功扱いにならない
