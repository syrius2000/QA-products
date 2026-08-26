# semantic/content digest分離の設計

created: 2026-08-26 22:27 (JST)
update: 2026-08-26 22:27 (JST)
author: Codex (GPT-5)

## Context

QA-0006では、Reviewer lifecycleとAuthor submissionが共有コアのdigest関数を利用しているが、`semantic_digest`と`content_digest`が同一値であることが確認された。本Changeは、Reviewerのhandoff生成とAuthorの提出検証を同じ入力定義へ更新し、意味変更と本文だけの変更を区別する。

## Goals / Non-Goals

**Goals:**

- 意味構造と文書内容から独立した決定的digestを生成する。
- Reviewer生成、Author検証、stale拒否、内容のみ変更の人間確認を一貫させる。
- 旧同値digestを新契約の検証済みEvidenceとして誤受理しない。
- 標準ライブラリだけで再現可能なfixtureと相互運用テストを提供する。

**Non-Goals:**

- QA-0006のF06を本Changeの実装前にクローズすること。
- 既存QA履歴や旧版Skillの書換え。
- Author/Reviewerの役割境界、Finding状態遷移、Skill配置、外部APIの変更。
- digestアルゴリズムの暗号学的署名化。改ざん耐性の強化は別Changeとする。

## Decisions

### 1. digest入力を明示的に分離する

`semantic_digest`にはcase ID、未解決Finding ID、case revision、状態・次アクションなど意味構造に属する正規化フィールドだけを入力する。`content_digest`にはhandoffおよび関連正本の正規化された文書内容を入力する。フィールド順・改行・YAML表現差は正規化し、同一意味・同一内容の再計算結果を安定させる。

代替案として既存の単一digestを両キーへ複製する方法は、F06を解消せず内容変更を検知できないため採用しない。

### 2. Reviewerを生成側、Authorを照合側とする

Reviewer lifecycleが正本からhandoffを生成し、同じ共有コアの公開関数で両digestを算出する。Author submissionはhandoffに記載された値を受け取るだけでなく、許可されたcanonical case directoryから両digestを再計算して照合する。どちらかが不一致なら保存・統合を拒否する。

### 3. 内容だけの変更は非終端とする

semanticが一致しcontentだけが不一致の場合は、意味変更として扱わず`content-changed`または`evidence-gap`相当の診断を返す。Reviewerによるhandoff再生成と人間確認が完了するまで、Author提出を成功状態へ進めない。

### 4. 旧形式は読み取り専用互換とする

旧履歴の同値digestは読み取り可能な履歴として保持するが、新Contractの両digest検証済みhandoffとはみなさない。移行fixtureで旧形式を検出し、推測による分離値生成や履歴書換えを行わない。

## Risks / Trade-offs

- [正規化規則の差異] → shared coreに入力スキーマとcanonicalizationを一元化し、Reviewer/Authorの同一fixtureで比較する。
- [本文に意味情報が含まれる場合の分類曖昧性] → semantic field allowlistを仕様化し、分類不能な変更は人間確認へ送る。
- [旧handoffの互換性低下] → 旧形式は読み取り専用で保持し、移行要求を明示する。自動受入は行わない。
- [実装途中の既存Evidence不整合] → 旧Evidenceを上書きせず、新旧digestとfixture digestを別々に記録する。

## Migration Plan

1. shared coreにcanonicalization、semantic digest、content digestの入力境界を追加する。
2. Reviewer生成とAuthor検証を新APIへ接続し、相互運用fixtureを実行する。
3. unchanged、semantic-only、content-only、stale、旧同値digestのテストとEvidenceを保存する。
4. QA-0006 F06をReviewerへ再提出し、独立検証後に人間裁定を更新する。
5. 本番Skill配置、旧版削除、commit、pushは別Changeで扱う。
