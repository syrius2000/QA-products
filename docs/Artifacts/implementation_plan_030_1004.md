# QAループ全体の権限・独立性・成果物契約改善計画

created: 2026-10-04 16:47 (JST)
update: 2026-10-04 16:47 (JST)
author: Codex (GPT-6)

## 目的

ローカルQAとクラウドQAを、依頼ごとの計画承認を挟まずに定型範囲で進めながら、レビューの独立性、対象固定、全受入基準の照合、結果の監査可能性を保つ。実際の操作契約を`AGENTS.md`、`quality-qa`、`blind-qa-cycle`、QA実装、OpenSpec、evalsと回帰テストで一致させる。

## 現状と改善理由

- ルート`AGENTS.md`のQA限定委任節は、クラウドQAで「新規topic branchへの通常push」を許可している。一方、`blind-qa-cycle`は既存topic branchとcheckpointを要求し、branch作成をフロー対象外としている。両者の実行契約が一致していない。
- 同節の「QA専用コミット」は、レビュー対象製品差分を固定するReviewed commit、依頼ファイルcommit、Reviewerが作るQA成果物commitの区別が曖昧である。
- `quality-qa`のレビュー生成・検査は依頼との要件指紋を照合するが、レビューMarkdown内に全受入基準を列挙させ、その全項目を依頼原文と照合する契約が不足している（QA-F01）。
- 再QAでは提出済み修正のsnapshotと再QA対象の関係を必須化し、提出後に同じ案件の別製品ファイル変更を新snapshotへ混入させない境界を回帰検証する必要がある（QA-F02）。
- Cloud依頼は自己完結した指示を含むが、対象commit上のQA SkillをReviewerが読む手順、Skill識別値、読めない場合の停止条件を全経路で一致させる必要がある。
- blind QAの成果物契約には4ファイルの存在、FindingとTasksの対応、JSON Gateと`STATUS.md`の一致などが既に定義されている。既存要件を保持しつつ、全基準の追跡とSkill由来の検証を統合する。

## 変更対象

- `AGENTS.md`: QA限定委任節を各Skillの実際の権限・ブランチ制約に整合させる。通常QA、クラウドQA、対象commit、依頼commit、QA成果物commitごとの起動条件と許可範囲を明記する。
- `.agents/skills/quality-qa/`: `SKILL.md`、依頼・公開・再QA・結果確認の該当参照、レビュー生成・検査runtime、必要な回帰テストとevalsを更新する。
- `.agents/skills/blind-qa-cycle/`: `SKILL.md`、branch/Git手順、cloud output contract、Audience案内を`AGENTS.md`と整合させる。既存のstaged-only、non-main topic、checkpoint、4成果物の保護条件を維持する。
- `openspec/changes/unify-qa-skill-workflow/`: 仕様・設計・タスクを最終契約と一致させ、QA-F01／QA-F02、Skill読込、権限境界、出力検証を受入条件へ結ぶ。
- 対応する既存テスト/Evalsを拡張し、必要ならQA workflow専用テストを追加する。正式Quality LoopのOwner/case裁定APIと配備先runtimeは変更対象に含めない。

## 実装方針と受入条件

### 1. 承認と実行権限をモード別に固定

- 通常QA依頼は、Skill指定の読み取り、依頼下書き、ローカルQA成果物作成までを許可する。通常QAだけではcommit、push、製品修正、Finding裁定、merge、deploymentを許可しない。
- クラウドQA依頼で許可するcommit種別を明記する。製品差分のReviewed固定、QA依頼ファイル、Reviewer成果物を別々のパス集合・commit目的として検査する。
- ブランチ契約はSkill間で単一化する。`blind-qa-cycle`の既存非main topic branch、checkpoint、利用者がstageしたindexのみの原則を既定として維持し、branch自動作成や別ブランチ公開を暗黙に許可しない。現ブランチや履歴が契約に合わない場合はpush前に停止し、必要な選択だけ人へ戻す。
- `AGENTS.md`の限定委任は、既定ブランチ・force-push・無関係な履歴・対象外ファイル・実クラウドQA実行まで許可したように読めない文面にする。

### 2. クラウドReviewerのSkill読込と独立性

- Cloud inviteに、レビュー対象commit内のQA Skillパス、commit SHAまたは内容hash、必須参照する出力契約を含める。Reviewerはレビュー開始前にその版を読み、欠落・hash不一致・取得不能ならGateをHOLD相当として成果物に記録する。
- 指示は全受入基準とレビュー範囲を自己完結させる。実施AIの結論・期待Findingは独立判定の前提として渡さず、Reviewer自身の根拠記録を要求する。
- ローカル／クラウドで同じ受入基準と成果物契約を使い、チャネル差は実行者、remote可視性、成果物の帰着方法に限定する。

### 3. QA-F01とQA-F02を検査可能な契約にする

- 依頼で固定した各受入基準に安定IDと原文を割り当て、依頼、レビュー本文、機械記録で同じ集合を保持する。レビューMarkdownの基準一覧に欠落・追加・改変・重複があれば取込検査を拒否する。要件指紋だけで列挙を代替しない。
- 修正提出時に許可された変更パス、各パスのsnapshot、承認済み修正計画との対応を固定する。再QA対象はこの許可集合内の提出済みsnapshotから構成し、提出後の追加・変更ファイルを黙って含めない。未提出変更、対象集合の拡張、要件変更は停止し、再承認または新しいQA依頼を求める。
- 初回目的・全基準・未解決Finding・元baselineを保持し、各再QAでは前回reviewedを差分baselineとして引き継ぐ。以前のサイクルの記録を上書きしない。

### 4. 結果検証と例外時のHuman-in-the-loop

- 予約出力の必須ファイル、受入基準の完全性、Finding/task対応、重大度・Gate整合、JSONとSTATUS一致、Skill hash、取得元SHAを機械検査し、矛盾があれば完了扱いにしない。
- Gate、テスト、パス・秘密情報検査、branch/remote ancestry、Skill読込、出力検証のどの条件で停止したかを具体的に返す。
- 人の判断は、対象・基準変更、未分類差分、公開先選択、HIGH/重大Findingの処置、残余リスク、Owner裁定、merge、deploymentに限定する。Findingの作成・選別・消去やReviewer Gate変更を人手で独立結果へ混入させない。

## 検証

- 読み取り専用ベースラインで既存差分165件（調査時点: 削除148、未追跡16、変更1）を確認した。実装前に再取得し、この既存状態を今回変更へ取り込まない。
- QA workflowの単体・統合テストで、基準欠落／改変／重複、指紋同一でも本文不一致、提出後の別製品ファイル変更、承認対象外パス、異なるReviewed SHA、サイクル履歴保持を検査する。
- Git操作テストで、main/master拒否、既存topic branch/checkpoint要件、unstaged/untracked拒否、対象別commit分離、push失敗・remote先行・既存差分保持、force-push不実行をbare remote等で検証する。
- Cloud契約テストで、Skillパス/hashの読み取り、出力4ファイル、基準一覧照合、Finding/task対応、Gate/STATUS一致、Skill欠落時の停止を検証する。
- ローカル／クラウド各経路のevalで、曖昧な「QAして」、明示的なローカルQA、明示的なクラウドQA、再QA、検査失敗時を比較する。明示されない公開・製品修正・自己裁定が0件であることを記録する。
- 関連QAテスト、Quality Loop既存回帰、対象OpenSpecのstrict validation、リンクとSkillパッケージ整合を実行し、未実施項目は`unverified`として残す。実際の独立クラウドレビュー結果はfixture検証と分ける。

## 今回の対象外

- remoteへのpush、PR作成・コメント、main/masterへのmerge、外部Skill配置、旧版削除、Owner裁定。
- 正式Quality Loopのcase正本・events・Owner権限、QAと無関係な既存削除・未追跡Artifact。
- 既存の`implementation_plan_029_1004.md`と`AGENTS.md`にある本作業開始前のユーザー差分の削除・復元。

## 承認状態

本書は全体改善の計画である。承認後に限り、記載したQA通常ループの文書・Skill・runtime・テスト・OpenSpecを一体として更新する。対象外の公開操作や正式Quality Loop権限は実行しない。
