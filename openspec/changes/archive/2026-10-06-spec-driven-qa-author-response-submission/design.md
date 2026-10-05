## Context

Reviewer側のケース正本と公開handoffは既存のReviewer lifecycle ChangeおよびContract v1.2で定義済みである。本Changeはその契約を読み取り専用で利用し、Authorの回答・提出だけを許可された境界に記録する。

## Goals / Non-Goals

**Goals:**

- ReviewerとAuthorの入口を分離しつつ、digest・revision・Finding IDの検証ロジックを共有する
- Authorの書込み先を提出ディレクトリへ限定し、Reviewer正本の変更を機械的に拒否する
- 回答、修正提出、反証、リスク受容を同一の構造化submissionとして検証可能にする
- 外部依存がない環境でも、偽陽性を避けた検証結果を返す

**Non-Goals:**

- Reviewerのケース作成、Finding判定、独立検証、ケースクローズの実装
- Ownerのrisk-accepted裁定をAuthorが代行すること
- 外部Skill配置、旧版削除、commit、push
- LLMの正答率やToken/Latencyの測定

## Decisions

### 1. 共有コア＋Author薄型入口

Author入口は役割説明と入力経路に限定し、digest、revision、Finding ID、Evidence、権限境界の検証は既存共有コアへ委譲する。単一Skillへ統合する案は役割逸脱を招きやすいため採用しない。

### 2. 提出記録を単一の公開形式にする

`submission_id`、`base_revision`、handoff digest、Finding別Disposition、根拠、Evidence、`modified_files`を一つの提出形式で保持する。Dispositionの意味とReviewer検証待ち状態を明示し、Authorは`fixed-and-verified`や`closed`を設定できない。

### 3. 書込み境界を許可リストで強制する

Authorが書き込めるのは対象QAケースの`cycles/cycle-NN-author-response.md`と、契約で明示された提出Evidenceだけとする。`review.md`、`findings.yaml`、`handoff.md`、`events.jsonl`はReviewer所有として拒否する。

### 4. パスと依存の失敗をFail-Closedにする

相対Evidenceと`modified_files`は対象Workspace内に解決して存在確認し、絶対パス、`file://`、Workspace外解決、未知Finding、stale digestは拒否する。YAML依存が欠落した場合は標準ライブラリ経路を使うか、`unverified`／`evidence-gap`を返して受理しない。

### 5. 代替案

- AuthorとReviewerを単一入口に統合する案: 役割誤認と自己レビューを防ぎにくいため不採用。
- PyYAMLを必須化する案: 配備環境の依存欠落で検証不能になるため不採用。
- Reviewer正本へ直接回答を書き込む案: 職務分離と履歴不変性を壊すため不採用。

## Risks / Trade-offs

- [共有コアとの契約ドリフト] → Contract version、digest、revisionを提出時に必須化し、既存Reviewerのテストを共通fixtureで再実行する。
- [自由記述Evidenceの曖昧性] → パス形式と自由記述を分類し、パス形式だけ実在検査する。成功根拠の不足はReviewer側で判定する。
- [独立性の不足] → Author実装後に別Agent・別Skill入口で独立QAを実施し、Author自身にFindingをクローズさせない。
- [本番配備差分] → 本Changeではstage内で完結し、配備は別Changeのdry-run・backup・rollback完了後に限定する。

## Migration Plan

1. stage内にAuthor入口、提出Validator、共有契約アダプタ、fixtureを追加する。
2. 正常系・拒否系・依存欠落のテストを実行し、Reviewer正本が変更されないことを確認する。
3. Authorの独立QAとReviewer verificationを完了する。
4. 本番Skill環境への配置は別の配備Changeで承認後に行う。失敗時はstage変更を配備せず、既存Skillを維持する。
