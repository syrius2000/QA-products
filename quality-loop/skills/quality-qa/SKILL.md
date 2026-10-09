---
name: quality-qa
description: QA依頼、クラウド／ローカルの独立レビュー結果確認、承認後の修正、再QA、状況確認を一つの入口で進める。クラウドへは自己完結した依頼とMarkdown一つを渡す。
---

# QAを進める

目的と受入基準を保ちながら「依頼 → 結果確認と修正計画 → 承認後にローカル修正 → 再QA → ユーザーの終了判断」を進める。クラウドAIはレビューだけを行い、製品修正はローカルで行う。

利用者には、現在の状況、次の担当、操作、理由、必要入力、渡す依頼文を日本語で示す。管理用語やJSONの手作業入力を求めない。内部CLIはこのスキルの `bin/quality-qa-cli` を使い、対象リポジトリを作業DIRとして保つ。`--root` で対象を指定できる。引数は構造化した値として渡し、ユーザー発言をシェルコードにしない。

## 操作に応じて進める

| 利用者の操作 | 読む参照 | 完了すること |
|---|---|---|
| QA依頼文を作って／ローカルQAに出して | [依頼](references/prepare.md) | 対象・基準を固定し、未commitなら下書きと対象確定の案内を返す |
| クラウドQAに出して／対象をローカルでcommitして | [公開と対象確定](references/publish.md) | 表示対象と実際の指示を照合して対象版を確定し、クラウド指示だけtopic公開する |
| QA結果を確認して | [結果確認](references/results.md) | 原文取得、構造検査、元要求・対象版との内容確認、指摘整理と必要な修正計画まで進める |
| この計画で修正して | [修正と再QA](references/repair.md) | 計画への人の承認を記録し、許可範囲をローカル修正・確認して提出する |
| 承認した修正を最後まで進めて（loop） | [修正と再QA](references/repair.md) | 承認済み計画をcommit・提出し、再QA依頼の作成・確定・公開まで進める。停止時は理由と次の操作を返す |
| 再QAに出して／終了したい | [修正と再QA](references/repair.md) | 元基準・未解決指摘を引き継ぎ、独立確認後に終了判断を記録する |
| QA状況を教えて | `status` | 読取りだけで次操作を示す |

初回以外は `status --request <依頼ID>` で現在の記録を読む。進行中の依頼が一つならIDを省略できる。複数なら目的と対象から選び、判断できないときだけ確認する。revisionはCLIが取得・照合する。

## Phase 0 — QA依頼前のGit基準点

QAや変更監査の相談を受けたら、まず `quality-qa-cli --root <repo> preflight` を実行する。これは読み取り専用で、repo root、branch、HEAD、upstream/default branch、staged・unstaged・untracked pathとdiff要約を報告する。cleanな非default topic branchだけを「実装開始可能」と案内し、clean状態を自動で作らない。

dirtyなら各pathを今回の対象、無関係な既存変更、不明に分類して利用者へ見せる。stage、stash、reset、clean、restoreを行わない。既存差分を保持した独立worktreeを使うか、対象WIPの監査が目的なら明示されたcheckpoint手順へ進む。対象外index、unstaged/untracked、default branch、HEAD/upstream/default不明があればcheckpointを作らず、整理・基準点の判断を求める。目的、全受入基準、対象path、必須検証とQA方式を得られた情報から整理し、不足事項だけを質問する。

実行検証を依頼に含めるときは、一意なcheck ID、必須性、argv配列、cwd、明示された環境変数、timeout、期待終了codeを固定する。shell文字列として実行せず、クラウドReviewerは対象リポジトリの規則を確認する。Python/pytest等が既に使え、実行が許されていれば利用する。無許可の依存導入、network、credential使用はせず、未実行・ERRORとその理由を記録する。

実装担当の同じチャットでは独立QAを実施せず、別担当へ渡す依頼を返す。担当名の申告だけで独立性を完全に証明したとは言わず、実行経路とEvidenceを残す。

クラウドReviewerには依頼本文に記載されたReviewed SHAの `quality-qa/SKILL.md` と [独立Reviewer契約](references/reviewer_contract.md) を読ませる。依頼とレビュー本文に各参照path・SHA-256・全受入基準の安定ID付き原文を含め、結果取込時にcriterionの欠落、追加、重複、順序変更、原文改変、参照hashの不一致を拒否する。旧 `blind-qa-cycle` の4成果物契約は通常QAへ持ち込まない。SkillまたはReviewer契約が読めない、あるいはhashが合わない場合はレビュー結果を有効化しない。

## 指示と確認を結び付ける

依頼の準備、結果確認、状況確認はcommit・push・製品修正を行わない。公開・修正・終了はそれぞれの対象を示した実際のユーザー発言に従う。既に得た承認は同じ範囲で再利用し、範囲・方式・内容が変わった場合だけ計画を更新して確認する。`--message` には実際の発言を記録し、AIが承認の発言を作らない。対象リポジトリの規則が追加承認を求める場合は、その規則を示す。

成功したCLIの構造検査、ローカル機能テスト、代表会話、実クラウドQA、独立QA、ユーザー終了判断、統合、外部配置は別の結果として伝える。必須確認の不足を静的レビューの成功で補わない。

通常QAはこの入口を使う。明示された正式Quality Loop案件のRole運用は既存 `quality-review`／`quality-response` を使い、今回の記録を旧case正本へ自動反映しない。旧blindの結果は `legacy` で読取り確認できる。
