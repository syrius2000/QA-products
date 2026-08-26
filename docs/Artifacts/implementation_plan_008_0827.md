# compact連鎖API追加実装計画

created: 2026-08-27 01:03 (JST)
update: 2026-08-27 01:10 (JST)
author: Codex (GPT-5)

## 1. 目的

compact版のReviewerとAuthorを、単発のJSON応答入口から、Reviewer判定、handoff生成、Author提出、digest・revision検証まで連続利用できるステージング実装へ拡張する。これにより、現在の完全互換Changeで未完了となっているcross-skill検証を実行可能にする。

## 2. 対象範囲

- `openspec/changes/spec-driven-qa-capability-parity-and-legacy-compat/stage/`配下のcompactステージング実装、fixture、テスト、Evidence。
- Reviewerが作成するhandoffの`case_revision`、`semantic_digest`、`content_digest`を正本候補として固定する処理。
- Author submissionの対象Finding、期待digest、base revision、Dispositionを検証する処理。
- AuthorがReviewer正本、イベント、closureを直接変更できない権限境界。
- cross-skill実行結果と、三版比較Runnerから参照するBundle Manifest・digestの更新。

## 3. 実装方式

1. 既存アーカイブBundleは変更せず、Change配下に新しいcompactステージングBundleを作成する。
2. 共有コアへ、case状態、Finding、Evidence、revision、semantic/content digestを扱う連鎖APIを追加する。
3. Reviewer入口へ、連鎖開始とhandoff生成を追加する。ただしReviewer正本の確定・closeはReviewer権限に限定する。
4. Author入口へ、handoff読取とsubmission検証を追加する。未知Finding、stale digest、revision不一致、Reviewer所有フィールド変更はfail-closedで拒否する。
5. 既存の単発`review`、`handoff`、`respond`、`submit`の認可と終了コードを維持し、連鎖APIは明示操作として追加する。
6. cross-skill fixtureを三版へ投入し、compactではhandoff、submission、digest、revisionの全証跡をObservedとして保存する。Legacy／Candidateの既存結果とはRunを分離する。

## 4. 検証計画

- 正常系: Reviewerがhandoffを生成し、Authorが有効なsubmissionを提出できる。
- stale系: semantic/content digestまたはbase revisionを改変したsubmissionが拒否され、正本が不変である。
- 権限系: AuthorによるReviewer正本、events、closureの変更が拒否される。
- Finding系: 未知Finding、未回答Finding、禁止Dispositionが拒否される。
- 依存系: 標準ライブラリのみで実行し、外部LLM・pytestに依存しない。
- 回帰系: 既存の21テスト、Bundle Manifest検証、3.2 Runner、QA-0006／QA-0007由来のdigest境界を再検証する。
- OpenSpec: 3.3の比較Evidenceが三版で揃うまで、互換性合格や本番配備可とは判定しない。

## 5. 安全境界と非目標

- 外部Skillディレクトリへの配置、旧版削除、commit、pushは行わない。
- アーカイブ済みcompact Bundle、Legacy ZIP、Candidateアーカイブは直接改変しない。
- `fixed-and-verified`や`closed`をAuthor APIから設定可能にしない。
- digest入力へ秘密値を含めず、秘密値検出時は保存せず拒否する。
- 3.3が完了しても、4章以降の互換性判定、独立QA、人間裁定を自動完了扱いにしない。

## 6. 完了条件

- compactステージングBundleにReviewer→handoff→Author submission→digest・revision検証のAPIが存在する。
- 正常系と拒否系のテストが全件成功する。
- cross-skill Evidenceでhandoff、submission、semantic/content digest、revision、正本不変性を確認できる。
- `tasks.md`の3.3を、実行結果が全条件を満たした場合のみチェックする。
- OpenSpec検証が`valid`であり、残る未検証項目と本番非対象を明記する。
