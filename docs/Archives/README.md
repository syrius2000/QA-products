# QA-products Archive案内

作成日: 2026-08-31（JST）

## 目的

本ディレクトリは、QA-productsの設計、実装、独立QA、Owner裁定、比較検証の経緯を保存する履歴資料の入口である。現行の利用方法と仕様は、ルート[README.md](../../README.md)、[AGENTS.md](../../AGENTS.md)、[`quality-loop/` README](../../quality-loop/README.md)、[`FUNCTIONAL_SPEC.md`](../../quality-loop/FUNCTIONAL_SPEC.md)を参照する。

## 現行Quality Loop

- [実装履歴統合アーカイブ](archived_summary_003_0831.md): Plan 011〜016と初期実装・QA・Owner裁定
- [最終独立QA受入サマリー](qa_acceptance_summary_001_0831.md): v1.4.0のQA判定とOwner引き継ぎ
- [原本ZIP・tarball保管場所](../../archives/quality-loop/): 添付計画、QA用パッケージ、圧縮版原本

## 分類

### Quality Loop

- [実装計画・実装履歴](quality-loop/implementation/): 現行Quality Loopの開発記録
- [QA記録](quality-loop/qa/): Quality Loop固有の独立QA、QA依頼、Owner裁定

### spec-driven-qa

- [設計](spec-driven-qa/design/): Contract v1.2の設計検討、Finding、Gemini-Flash設計資料
- [圧縮企画](spec-driven-qa/compact/): 旧spec-driven-qa Skillのサイズ削減企画
- [QAプロンプト](spec-driven-qa/qa/): 旧Skill比較・評価用の実行指示

### その他

- `misc/`: Quality Loopの正本・仕様・運用資料ではない参考資料
- `temporary/`: 現在は使用していない一時資料の保存先。今回の削除対象は保存しない
- [Archive方針ADR](adr/0001-repository-document-archive-policy.md): ルート文書、Archive、公開Git履歴の境界

## 正本と履歴の区別

Archiveの本文は作成時点の判断と状態を保存したもので、現行状態へ自動更新しない。現行の操作・状態遷移・安全契約は`quality-loop/`を正本とし、最終QAの推奨とOwnerの正式裁定は別の記録として扱う。

## 読み方

初めて利用する場合は、ルートREADMEから`quality-loop/README.md`へ進む。過去の設計理由や変更の流れを確認する場合は、実装履歴統合アーカイブを読み、QAの受入状態を確認する場合は最終独立QA受入サマリーを読む。旧spec-driven-qaの比較・圧縮資料は、現行Quality Loopの実装仕様とは混同しない。
