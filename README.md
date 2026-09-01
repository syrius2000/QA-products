# QA-products

人間Owner、Reviewer、ImplementerがFindingとEvidenceを使って改善を前進させる、最小QMS協働ループを提供します。最初に「使う」ための手順を示し、その後に現在の状態、設計思想、評価・開発情報を説明します。

## すぐ使う

1. 2つのSkillをグローバルまたは対象リポジトリへ配置する場合は、[Skill手動配置ガイド](quality-loop/SKILL_DEPLOYMENT_GUIDE.md)を開きます。既存Skillを上書きせず、対象パスを特定した承認後に手動コピーします。
2. Reviewer工程には`quality-review`、Implementer工程には`quality-response`を使います。どちらも最初に`status`を実行し、現在のRoleとhandoffを確認します。
3. 新しい案件を始める場合は、下の[最初の案件を開始する](#最初の案件を開始する)へ進みます。

現行の公開操作、入力Template、詳細仕様は[Quality Loop README](quality-loop/README.md)と[機能仕様](quality-loop/FUNCTIONAL_SPEC.md)を参照してください。

## 2つのSkillの使い分け

- `quality-review`: 明示されたQuality Loop案件で、`next_role=reviewer`の初回レビュー、Response Plan評価、独立検証、最終リスク評価を行う。
- `quality-response`: 明示されたQuality Loop案件で、`next_role=implementer`かつ`next_action=submit-plan`または`submit-response`の回答・修正提出を行う。

一般的なコードレビュー、一般的な回答作成、OpenSpec案件一般、Owner裁定、自己クローズには使いません。Reviewerは回答を代筆せず、ImplementerはReviewer検証やOwner裁定を代行しません。

## 最初の案件を開始する

最小入力は[quality-loop/templates/intake.json](quality-loop/templates/intake.json)をコピーして作成します。`actor_id`と`owner`は、案件を作成する人間Ownerの識別子に揃えてください。

```bash
cd quality-loop
cp templates/intake.json create-case.json
# create-case.jsonのcase_id、owner、baseline、対象revisionを編集する
python3 -B -m quality_loop.cli --case-root ../qms-cases create-case --input create-case.json
```

成功結果の`next_role`、`next_action`、`handoff`を次のAIへ渡します。各AIは最初に`status`を確認し、現在のhandoffとrevisionに従ってください。

案件正本の`qms-cases/<case-id>/case.json`は直接編集しません。修正は必ず該当するCLI操作を通し、EvidenceとInvocation IDを記録します。

## 現在の状態

v1.4.0 Coreは、実装者側のローカル検証と独立QAを完了し、独立QAの判定は`ACCEPT / READY FOR OWNER ADJUDICATION`です。Critical、High、Medium、Lowの新規Findingはいずれも0件です。ただし、正式なOwner最終裁定、外部配置、commit、pushは未実施です。

資料は、実装履歴とQA結果を分けて管理しています。[実装履歴統合アーカイブ](docs/Archives/archived_summary_003_0831.md)はPlan 011〜016と初期資料の経緯を、[最終独立QA受入サマリー](docs/Archives/qa_acceptance_summary_001_0831.md)はv1.4.0のQA判定とOwner引き継ぎを記録します。過去の計画ZIP・tarball・QA用ZIPは[原本アーカイブ](archives/quality-loop/)に保存しています。

## Quality Loopの役割

品質要求をAIが勝手に上げ下げしないこと、責任追及ではなく改善を進めることを基本とします。

1. Reviewerが、要求・Purpose・客観的Evidenceに基づいてFindingを作成する。
2. Implementerが、Findingごとに回答し、Ownerが許可した範囲だけを修正して提出する。
3. Reviewerが、Implementerとは別Invocationで独立検証する。
4. 人間Ownerが、Evidenceと残余リスクを確認して受入、保留、却下、再作業を裁定する。

## 中座・変更観測の支援

`status --resume-format markdown`は、正本を変えずに`resume.md`を生成します。現在地、未解決Finding、必要Evidence、観測範囲、次のCLI操作を確認して再開してください。

対象ファイルのSHA-256有限manifestと、明示起動の読取り専用Git観測も利用できます。対象外のファイル、ignored、submodule内部、外部サービスについて「変更なし」とは判定しません。詳細は[Quality Loop README](quality-loop/README.md)を参照してください。

## 他AIで評価するときのコツ

AIごとに案件ディレクトリを分け、同じ`case.json`へ同時に書き込ませないでください。たとえば、`qms-cases/eval-cursor-001/`、`qms-cases/eval-antigravity-001/`のように分離します。

- 各AIには、対象Skill、案件ID、入力handoff、評価目的を明示する。
- AIの識別子とInvocation IDを毎回記録する。
- 評価結果は`pass`だけでなく、未確認事項、追加質問、誤ったRole行動、Evidence不足も保存する。
- AIが作成した結果を、同じAIに自己検証させない。別Invocation、可能なら別AIのReviewerで検証する。
- Token数や応答時間は取得できた場合だけObservedとし、推定値を実測値として扱わない。
- 1つのAIの成功だけで全モデルの能力を保証しない。モデル名、設定、日時、Prompt、対象Skillのdigestまたは版を記録する。
- 失敗してもAIや人を責めず、再現可能なFindingとEvidenceに変換して次の改善へ渡す。

複数AIの結果を統合する場合は、各AIの原本を変更せず、Coordinatorが比較表を別ファイルに作成します。結果の混在を避けるため、他AIへ渡す依頼文には「指定された案件ディレクトリだけに保存し、共有正本や他AIのEvidenceを変更しない」と明記してください。

## 開発者向け検証

```bash
cd quality-loop
/usr/bin/python3 -B -m unittest discover -s tests -v
/usr/bin/python3 -B -m quality_loop.cli --help
```

製品本体はPython標準ライブラリだけで動作します。外部LLM APIへの接続、Token・Latencyの自動測定、本番Skill環境への配備は初期版の範囲外です。

## 変更時の注意

変更前に`AGENTS.md`と、現行の承認済み計画を確認してください。過去の実装計画は[実装履歴統合アーカイブ](docs/Archives/archived_summary_003_0831.md)にあります。大きな変更は日本語の実装計画を先に作成し、Owner承認後に実装します。Remoteへのpush、外部Skill環境への配置、旧資産の削除は、別途明示的に承認された場合だけ行います。
