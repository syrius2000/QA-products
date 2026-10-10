# Design

## Context

現状の正本は`quality-loop/skills/blind-qa-cycle/`で、`SKILL.md`と参照契約が招待・レビュー・4成果物・再QAを定義する。`.agents/skills/blind-qa-cycle/`には異なる旧本文が残っている。通常QAの`quality-qa`は別の単一Markdown workflowを持ち、`quality-review`／`quality-response`は正式case正本をCLI経由で操作する。詳細な動作契約は[proposal.md](proposal.md)と[spec delta](specs/blind-qa-cycle/spec.md)を参照。

既存cycleの4成果物は`00_invite.md`、`01_review.md`、`02_tasks.md`、`03_machine.json`、`STATUS.md`。既存cycleの書換えは許可されず、通常QAと正式caseの保存形式も今回変更しない。

## Goals / Non-Goals

**Goals:**

- `blind-qa-cycle`の一つの正本と互換導線を定義する。
- 実装前Baselineまたは明示された実装後Reviewed commitから、ローカル／クラウドの固定SHAレビュー、Finding対応、再QA、監査ブランチ上の終結を一貫させる。
- QA後に人が約5分で理解を記録する行為を支援し、QA結果とNoteを監査可能に関連づける。

**Non-Goals:**

- `quality-qa`、`quality-review`、`quality-response`の要件・CLI・case正本を変更すること。
- Noteから理解度・QA Gate・Owner受入を自動判定すること。
- 既存cycle記録の移動・書換え、main/masterへのmerge、外部Skill配置、force-push。

## Decisions

### 実装前計画とReviewed対象を別commitで固定する

- `/blind-qa-cycle prepare`はcleanな非default topic branchで`docs/Artifacts/qa_cycles/<topic>/c<N>/00_plan.md`を作り、目的、受入基準、準備前HEADを記録する。stageするのはこの生成ファイルだけとし、`Yip: QA plan <topic> c<N>`および`Blind-QA-Plan: <topic>` trailerのcommitを作る。この計画commitのSHAを後続レビューのBaselineにする。`00_plan.md`自身には後から確定する自分のcommit SHAを要求しない。
- 実装完了後、clean staged-only Reviewed規則で製品対象をYip commitへ固定し、同じcycleの`00_plan.md`から受入基準を引き継いだ完全な`00_invite.md`を別commitにする。レビュー範囲はBaseline（計画commit）からReviewed（製品commit）までであり、計画ファイルはBaseline tree内にあるためdiffへ混ざらない。
- 事前準備がない場合は現在のcheckpoint→Reviewed→invite経路を残し、最終inviteに事後開始と基準選択理由を記録する。
- 完了済み差分に対して今回の明示依頼で新しいtopic branchを作る場合は、切替直前のbranch HEADを固定Baselineとして許可する。branchはそのSHAから開始し、Reviewedより前に他commitを作らない。inviteに元branch名とbranch-start理由を残し、Baseline/Reviewedの祖先関係をcloud handoff前に検証する。
- 代替案: 実装後のinviteだけを唯一の入口にする。実装前に受入基準と境界を合意する目的を満たせないため採らない。SHA未確定のinviteをReviewerへ渡す案も、必須フィールドと固定SHAを壊すため採らない。

### 独立QAサイクルを新しいspec capabilityにする

- `blind-qa-cycle`を新規capabilityとして定義し、既存の`unified-qa-workflow`等の仕様は変更しない。
- 理由: 通常QAとformal Quality Loopの既存契約は異なる。監査ブランチ上のYip commit往復と別のcycle DIRを独立したbehavior contractとして管理し、似た入口を持つ既存SkillへQA成果物やcase状態を書き込まないため。
- 代替案: `unified-qa-workflow`へ要件を追加する。今回は対象フローと保存・Git契約を一体化し、既存の通常QA要件を変更しない方針に合わないため採らない。

### 正本と旧配置の関係

- `quality-loop/skills/blind-qa-cycle/`を唯一の編集正本にする。
- `.agents/skills/blind-qa-cycle/`を独立した複製として維持しない。移行時は同配置のSKILLを正本へ案内する短い互換shimへ置き換え、旧本文を起動根拠として残さない。その他の古い参照資料は差分を確認し、必要な独自ルールだけを正本へ統合してから扱う。
- 変更前に`.agents`側のGit追跡・ignore状態とローカル利用箇所を再確認する。既存ユーザー変更や個人配置を削除せず、互換shimへの置換範囲を承認済み対象に限定する。
- 代替案: 2つの全文コピーを引き続き同期する。ドリフトを再発させるため採らない。旧ディレクトリを無条件削除する案も、配置状態と利用者の変更を失う可能性があるため採らない。

### Noteは`blind-qa-cycle`の人間記入モードとして支援する

- `/blind-qa-cycle note`を専用モードとして設ける。終結済みレビューcycleの`00_invite.md`、`03_machine.json`、`STATUS.md`を読取り、cycle ID、Repository、branch、Baseline/Reviewed SHA、最終Gateを参照情報として提示する。
- 出力先はcycle DIR内の`04_human_understanding.md`とする。新規ファイルのみ作成し、既存Noteがある場合は停止して読取りまたは新cycleを案内する。
- モードは6つの質問を提示し、担当者の回答だけをそのまま記録する。人がチャットへ回答する方式と、空テンプレートを作って人が直接編集する方式のどちらでも開始できる。回答の要約・推測補完・採点・書換えはしない。所要5分は目安として提示し、timerで理解度を測らない。
- Noteの質問はsystem boundary、守るinvariant、最も危険だったfailure mode、防止mechanism、AIなしで説明できる設計、まだ理解していない点に対応する。未理解点を明記できる。
- 代替案: ReviewerにNoteを書かせる、またはAI生成の要約を人の理解として保存する。どちらも独立QAと自己理解の境界を崩すため採らない。別CLI/packageの追加も既存Skillの構成に不要な依存を増やすため行わない。

### NoteとQA Gateを別の状態として保つ

- `PASS|HOLD|FAIL|INCONCLUSIVE`は技術レビューのGateのままにする。Noteの存在・内容をGate算出へ混ぜない。
- Note記入が完了したことはcycle終了記録に示すが、空欄や「まだ理解していない点」は認め、理解の評価やOwner裁定とは扱わない。
- Note生成モードはQA artifact commitやpushを実行しない。作成ファイルの保存と人による記入までを支援し、commit/pushはユーザーの明示操作に従う。
- 代替案: NoteをPASS条件にする。理解に関する記録を技術Gateへ混在させ、過度な完了保証に見せるため採らない。

### Local/Cloudで対象・成果物契約を共有する

- Local/Cloudは同じBaseline、Reviewed、AC、Finding、結果契約を使い、Audience、remote visibility、handoffと許可されたGit帰着だけを分岐させる。
- Localはpushしない。Cloudは明示的なCloud QAモードで固定topic branchの必要commitだけを扱い、main/masterへのmergeをしない。ReviewerはNoteを作成・編集しない。
- 代替案: LocalとCloudで別の成果物契約を持つ。運用差が増え、相互比較・再QAの一貫性を損なうため採らない。

## Risks / Trade-offs

- [旧`.agents`配置が利用中である] → 変更前に追跡・ignore・利用箇所を確認し、正本を指すshimを使う。無関係ファイルやユーザー変更は保持する。
- [Noteの回答がAIに整形されて本人の理解と混同される] → 回答を逐語で保存し、AIは未回答欄を推測で埋めず、Noteへ作成者が人であることを記録する。
- [QA成果物追加により既存validatorや4ファイル契約と互換性が崩れる] → 4つのReviewer成果物契約を維持し、NoteをReviewer output contract外の人間側終結記録として追加する。新旧cycleの読み込みは新形式Noteがない既存cycleも有効とする。
- [NoteがQA完了やOwner受入を示すと誤解される] → Note headerと最終応答で技術Gate・Owner判断とは別の振り返り記録と明示する。

## Migration Plan

1. 実装前に既存2配置、Git追跡・ignore、参照先、出力契約、validatorを再確認し、承認対象外の既存変更を保護する。
2. 正本Skillと参照資料を整理し、旧ローカル配置は承認範囲内で互換shimへ移行する。既存QA cycleファイルは一切変更しない。
3. 新規cycleだけへ`04_human_understanding.md`作成支援を適用し、Reviewerの4ファイル出力は保つ。
4. 旧cycleのNote欠落をエラーにせず、旧4成果物の読取互換を維持する。QA挙動検証の後も独立QA、Owner判断、外部配置、mergeを別のGateとして扱う。
5. Rollbackが必要な場合は、当該変更ラウンドで追加した正本Skill・shim・契約変更だけを戻し、作業前に存在したファイル・利用者変更・QA記録は復元対象に含めない。
