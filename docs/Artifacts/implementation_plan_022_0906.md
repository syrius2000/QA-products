# Author Response Change独立QA計画

created: 2026-09-06 14:44 (JST)
update: 2026-09-06 14:44 (JST)
author: Codex (GPT-5)

## 1. 目的

`spec-driven-qa-author-response-submission` の実装結果を、実装者の自己申告と分離したReviewer視点で確認し、残タスク6.2の独立QA Evidenceを記録する。

## 2. 確認対象

- Authorの自己クローズ拒否
- 未知Finding拒否
- stale semantic/content digest拒否
- Evidenceの相対パス、存在、Workspace外、`file://`境界
- 正常系submissionの保存先とReviewer検証待ち状態

## 3. 実施方法

1. Changeのproposal、spec、design、tasks、stage実装を独立に読み取る。
2. キャッシュなしでAuthor側テストとReviewer回帰テストを実行する。
3. 既存テストと別の入力を用いた拒否系プローブを一時Workspaceで実行する。
4. 対象成果物、Reviewer正本、Owner裁定、外部Skill配置先を変更せず、QA記録だけを`docs/ADR/QA/QA-0011-*`へ保存する。

## 4. 判定境界

- 判定語は`verified`、`not-verified`、`unverified`、`evidence-gap`を使用する。
- Author Change自体の実装、正本の自己変更、自己クローズ、外部配置、commit、pushは実施しない。
- LLM性能、外部配置後動作、別Agentによる正式QMS CLI判定は未検証として記録する。

## 5. 完了条件

- 独立入力で対象拒否境界を再現できる。
- 実行結果、終了コード、対象revision、未検証項目をQA記録に保存する。
- 残タスク6.2のチェックを、Evidenceと実装結果が一致した場合だけ完了へ更新する。
