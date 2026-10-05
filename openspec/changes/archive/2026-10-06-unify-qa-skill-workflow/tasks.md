# 統合QAの実装タスク

created: 2026-10-04 09:39 (JST)
update: 2026-10-05 23:35 (JST)
author: Codex (GPT-6)

本書は計画033承認後の実装タスクを追跡する。チェック済みは実装とEvidenceが揃った項目だけとし、書類作成・strict検証を機能実装や独立QAの完了に数えない。

## 1. 実装境界と基準の固定

- [x] 1.1 4書類と計画033の承認範囲を確認し、調査HEAD `ad6ca1ee196bd75bed026858c2de9586ca49c85c`の既存隔離worktreeを確認した。元checkoutの既存差分とindexは[持込元manifest](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_source_manifest_001_1004.md)、本worktreeの開始時点47 status entries・内容hash・staged/unstaged diff hashは[実装baseline](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_implementation_baseline_001_1004.md)に固定した。worktreeはdetached HEADのまま使用し、branch自動作成・pushはしない。
- [x] 1.2 既存Coreと旧2スキルruntimeの相対パス・サイズ・SHA-256 manifest、旧runtime同士の一致、既存テスト入口と過去結果の証拠限界を[開始時インベントリ](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_runtime_inventory_001_1004.md)へ記録した。外部配置先と旧正本は開始時差分に含まれない。
- [x] 1.3 新runtimeの配置・変更対象と受入領域・Evidenceの対応を[開始時インベントリ](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_runtime_inventory_001_1004.md)に固定し、旧case engineを変更せず独立 `qa_workflow` packageへ追加した。

## 2. ローカル状態と次工程の案内

- [x] 2.1 依頼ID／cycle／baseline／要件fingerprint／path集合／review・訂正・修正承認・提出snapshot・execution checkを持つ状態をfixture生成し、`Store.validate`で初期状態とrevision/check ID不正を拒否することを確認。
- [x] 2.2 各phaseの次担当・操作・理由・必要入力をfixtureで確認し、未確定draftのhandoffと訂正待ちの修正計画・終了判断を拒否することを確認。
- [x] 2.3 revision照合、排他、原子的更新、再取込の同一性を回帰検証した。lockのthread競合、atomic replace失敗時の旧本文保持とtemp cleanup、同一Markdown二重取込の履歴非重複、古いrevision拒否をfixtureで確認。
- [x] 2.4 読み取り専用の状態確認と複数依頼時の選択を実装する。2依頼fixtureでID省略時の選択要求・指定IDの選択と、status前後の全ファイル内容一致を確認。
- [x] 2.5 phaseと次操作をCLI JSONと日本語Skillに記載し、標準CLI help・preflightと代表status/prepare経路で利用者向け操作案内を確認。管理用JSONと旧Role入力の手作業を求めない。

## 3. 対象固定と自己完結したQA依頼

- [x] 3.1 read-only preflightでrepo/branch/HEAD/upstream/default/staged・unstaged・untracked/diff要約を報告し、dirty状態を変更しないことをfixtureで確認。対象確定・cloud publishではdefault branch、未分類path、範囲外indexを拒否する。既存WIP checkpointはblind-qa-cycleの明示手順へ限定。
- [x] 3.2 目的・受入基準fingerprint、初回と修正差分baseline、下書き・確定SHAの境界を保存。全受入基準の原文・順序を再照合し、確定SHAの書換え、ancestor不一致、内容差分を拒否するfixtureを確認。
- [x] 3.3 構造化実行検証契約を依頼state・Cloud依頼・CLIへ実装した。一意check ID、必須性、argv、cwd、env、timeout、期待終了codeを固定し、無許可依存導入・network・認証情報アクセスを禁止する案内を追加。依頼生成fixtureとCLI helpで確認。
- [x] 3.4 ローカル／クラウド共通の依頼契約、準備のみでGit変更しないこと、ローカルcommitによる対象確定、対象外stageの保持、クラウドの対象限定pushを一時Git fixtureで確認。未commit下書きは正式レビューへ渡せず、暗黙pushしない。
- [x] 3.5 依頼作成の会話例と不足事項だけを尋ねる運用を[依頼手順](../../../quality-loop/skills/quality-qa/references/prepare.md)へ記載。取得可能な環境・Git情報を再質問しないと明示。

## 4. 対象限定のクラウド公開

- [x] 4.1 Cloud公開時のユーザー指示、製品・依頼集合、branch/remote、index、全送出commit履歴をpreflightで照合。無関係なstaged差分を保ち、remote先行製品変更と既定branchを拒否するbare remote fixtureを確認。
- [x] 4.2 ローカルbare remote fixtureで、製品対象SHAのcommitと依頼だけの追跡commitを分離し、対象差分にQA管理JSON・inviteが混ざらず、invite commitが対象SHAを保持することを確認。
- [x] 4.3 topic branchへの通常push後にremote tipから対象／依頼commitの到達可能性を照合する成功系と、既定branch公開拒否・HEAD/remote不変をbare remoteで確認。force-push・暗黙mergeは経路に含まない。
- [x] 4.4 対象commit直後・依頼commit直後・push失敗から同じcommit SHAを再利用する再試行fixtureを追加。remote先行は登録済みレビューArtifactだけをfast-forwardし、製品変更混在なら停止するbare remote fixtureを確認。
- [x] 4.5 [公開手順](../../../quality-loop/skills/quality-qa/references/publish.md)へ対象確定・公開・QA実行・終了・統合の境界と分岐時の停止を記載。statusで公開をQA完了や既定branch統合と表示しない。

## 5. Markdown結果の取得と検査

- [x] 5.1 branch／PR／本文取得でGitHub取得元の完全SHA固定、fork head repo参照、通常Markdownだけの取得をfixture確認。認証失敗をQAErrorとして返し、成功扱いしない。
- [x] 5.2 指定Markdownだけの取得、原文hash保持、PR head SHA固定、同名別内容・symlink・予約外path拒否、訂正版の別保存先と前版保持をfixtureで確認。取得処理に製品コードmerge経路がないことを確認。
- [x] 5.3 Markdown parserで全受入基準、check ID/状態/argv/cwd/env/timeout/runtime/exit code/duration/stdout・stderr excerptと完全出力hash、実施側taskとFinding参照を照合する。QA-003対応でGate優先順位をHOLD（provenance不一致）→FAIL（確認済みFAIL）→INCONCLUSIVE（FAILなしで必須check未完了）→PASSに修正し、Gate matrix fixtureで確認。
- [x] 5.4 指摘と修正タスク・結論・前回確認の整合を検査する。重大未解決とPASS、対応タスク欠落、前回指摘省略、テンプレート文を根拠と誤認する状態を拒否する回帰fixtureを追加。
- [x] 5.5 [結果確認手順](../../../quality-loop/skills/quality-qa/references/results.md)へ取得と内容確認の違い、訂正依頼・取得失敗・本文手渡しを記載。訂正ID予約、別path・前版保全、訂正待ち停止、重複取込防止をfixtureで確認。

## 6. 指摘整理・修正計画・承認後の提出

- [x] 6.1 Skill手順とparserで要求未達・不具合・改善提案・未検証を分離し、重大FindingとPASSの矛盾・改善Findingの不要な修正強制を拒否する。仕様外改善を必須扱いしないことをレビュー手順に記載。
- [x] 6.2 Finding別の理解・方針・対象・影響・完了条件・確認方法を持つ計画を生成し、計画前後に製品ファイルsnapshotが不変であることをmulti-path fixtureで確認。
- [x] 6.3 人の承認をplan hashとpath集合へ束縛し、提出時に対象・Evidence・未検証・計画本文・実装方式を必須照合。承認なし、stale hash、path/方式変更を拒否。未commit提出は再QA下書きとなり、正式QA前に対象SHA確定を要する。
- [x] 6.4 [修正・再QA手順](../../../quality-loop/skills/quality-qa/references/repair.md)へ計画・承認・提出・再確認例を記載。提出時は `independently_verified=false` を保持し、修正自己申告でFindingを閉じない。

## 7. 再QAと終了判断

- [x] 7.1 前回reviewedを新baselineにし、初回基準・受入基準・未解決Findingを引き継ぐ完全なローカル再QA fixtureを実行。製品／運用／対象外分類とrename旧新path、全path snapshot境界を確認。
- [x] 7.2 前回Findingを省略またはテンプレート根拠で解消扱いにする結果を拒否し、対象SHA上の具体的Evidenceを伴う再確認後だけ未解決一覧から除くことをparser・cycle fixtureで確認。
- [x] 7.3 残余事項のユーザー判断を独立記録し、QA終了判断を別操作に分離。統合fixtureでこの操作がHEAD・remote既定branchを変えず、残余判断も独立QA証拠へ読み替えないことを確認。
- [x] 7.4 [修正・再QA手順](../../../quality-loop/skills/quality-qa/references/repair.md)で再QA宛先を要求し、曖昧な依頼でクラウド公開しない。終了後の統合先を現在の既定branchとして案内し、別途指示を要求する。

## 8. 旧形式・パッケージ・利用入口

- [x] 8.1 旧blindの4成果物と原依頼を読み取り専用で変換する。正常系、Gate不一致、未知Findingを参照するtaskを検査し、原文を編集しないことをfixtureで確認。受入基準不足の拒否も parser pathで確認対象に含む。
- [x] 8.2 新スキルへruntime・CLI・テンプレート・単一Markdown Reviewer契約・参照を同梱する。一時DIRへskillをコピーしCLI helpと開発runtime内容一致を確認。Reviewer参照には旧4成果物契約を混在させない。
- [x] 8.3 同期スクリプトへ`quality-qa`用のruntime/bin検査と対象定義を追加。宛先だけにある追加ファイル、同じVERSIONの未知差異、dirtyな配布先は`--force`指定でも上書きしない。外部実コピーなしの4 dry-run fixtureで確認。
- [x] 8.4 README・機能仕様・配布ガイドへ通常QA `quality-qa` と正式case `quality-review`/`quality-response` の境界、Cloud/Python実行条件、配置境界を記載。9文書の相対リンク検査OK、CLI help/preflightも確認。

## 9. 統合確認と引渡し

- [x] 9.1 Preflight、初回依頼、結果確認、計画・承認・提出、修正commit、再QA、前回指摘再確認、終了判断までをlocal fixtureで実行。dirty preflightの非変更、default branch・範囲外remote先行・unrelated staged path拒否／保持、必須PASS/FAIL/ERROR、環境不足、任意未実行をfixtureで確認。
- [x] 9.2 既存Quality Loop regression suite込みで163 passed・39 subtests、Python 3.14.7／pytest 9.0.2、`pytest tests -q`、cwd `quality-loop/`、exit 0、duration 15944ms、stdout SHA-256 `fb03358cc0592ec499dcae783b6012b8097fa796673386d8e6c927c10d2a2788`、stderr SHA-256（空）`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`を記録。Python 3.10環境は見つからずunverified。旧Core/2 runtime diffなし、新QA runtime一致、strict OpenSpec valid。
- [x] 9.3 別の独立担当によるQA-003 Cycle 1を受領した。判定FAIL、QA-F01〜QA-F05修正対象、QA-F06追試対象として[原レビュー](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_003_1004.md)へ記録。修正後の独立QAは本項の完了とは混同せず後続cycleで実施する。
- [x] 9.4 [引渡し報告](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/implementation_report_002_1005.md)へ要件対応、タスク状況、現行HEADでの実行検証、独立QA状態、未確認事項、外部配置・削除・commit・push・master統合の実施有無と次操作を記載した。Cycle 1はFAIL、Cycle 2は未実施と明記。終了判断・統合は実行せず、既存の未追跡gomi.memo.mdを保持した。

## 10. QA-003指摘対応（Plan 035）

- [x] 10.1 公開前に製品snapshotと依頼文を走査し、秘密鍵・secretらしい代入・個人ローカルパスを検出したらGit preflight/commit/pushより前に停止する。必須argv checkをshellなしで実行し、Evidenceを製品snapshot hashとcheck contract hashに結び付ける。bare remoteで未実施拒否、成功、snapshot変更拒否、機密fixture拒否時のHEAD/index/remote不変を確認。
- [x] 10.2 [公開手順](../../../quality-loop/skills/quality-qa/references/publish.md)へverify先行、停止条件、Evidence、合成fixture例外を追記し、runtimeと照合。
- [x] 10.3 再QA時に既存check ID・required・argv・cwd・env・timeout・expected exit code・Python最低版を完全保持し、変更は別引数 `--check-contract-approval` へ実際の人の承認を明記しなければ作れない。削除・required解除・新check追加の無承認拒否と、承認済みの追加時に既存契約を保つことをfixtureで確認。
- [x] 10.4 Reviewer parser、Reviewer契約、OpenSpecのGate優先順位を統一し、FAILとERROR/NOT_RUN、PASSとERROR、FAILと別check NOT_RUN、provenance不一致と未完了checkの組合せを検証。同一原文の再検査fixtureは旧validator問題履歴・本文を保持した。QA-003原文SHA-256 `bdc999f1cd5c3e5127ebf97d8658b83e26b8011df15df5913ead6d82460a0f52`もread-onlyで再評価し、現行parserのissuesは0件、gateはFAIL。運用状態JSONは承認path外の既存差分のため書き換えていない。
- [x] 10.5 静的Markdown templateにparser必須節、参照資材hash行、実施側タスク節、check記録形式を揃え、静的templateのparser受入テストを追加。
- [x] 10.6 Plan 033と履歴の退避済み・復元可能表現をQA対象SHAのGit treeと照合し訂正。024〜028の所在不明、029/030/032のflat存在、031の記録hash不一致を区別し、復元未検証とした。
- [x] 10.7 Provenance plansの壊れたArtifacts README相対linkを対象tree内の実在参照へ直し、関連文書linkを検査。
- [x] 10.8 QA-003 Cycle 1のCloud Reviewerによるpytestは、pytest未導入で起動前ERRORとなった（詳細は原レビュー）。以下はそれとは別の実装側検証記録であり、CloudQAの成功結果ではない。元Reviewed SHA `d9bad5c125791306e38bca8830b4082f7f38fc6b`を`git archive`で隔離し、Python 3.14.7／pytest 9.0.2、`pytest tests -q`、cwd `quality-loop/`、env `PYTHONDONTWRITEBYTECODE=1; PYTHONPATH=.`、timeout 300s、exit 0、duration 16302ms、163 passed／39 subtests、stdout SHA-256 `fd863f5c0b362da564cbbb488babbc798cdb7938de223492c7abfd18a9d7b9de`、stderr SHA-256（空）`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`を確認。修正候補は未commit作業ツリーのためcommit SHAではなく、HEAD `418dcb995344b611f9831e7f683d8cdbdf9cbc70`＋対象コード/runtime/test 12ファイルのsnapshot SHA-256 `930358545c56fd91377b33449d1173c979aaa44c1b39e473b01c0182885d62b6`で識別した。同環境・同argv・cwd・env・timeoutでexit 0、duration 17947ms、173 passed／44 subtests、stdout SHA-256 `d61a4001b088de997d7f61368f44150f9b526a9017b9748c574ecef413e95a2d`、stderr SHA-256（空）は同上。現行固定HEAD `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb`でも実装側で同じ必須suiteを再実行した。Python 3.12.3／pytest 7.4.4、`pytest tests -q`、cwd `quality-loop/`、env `PYTHONDONTWRITEBYTECODE=1; PYTHONPATH=.`、timeout 300秒、exit 0、duration 9896ms、173 passed、stdout SHA-256 `3452b8fff506aea3725c266b2ee5ca6653eac73fc988225cf784aefdfa0afd00`、stderr SHA-256（空）`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`を記録した。この実行も実装側検証であり独立追試ではない。続くQA-003 Cycle 2の独立レビューは[レビュー記録](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_review_003_cycle2_local_1005.md)のとおりGate HOLD。Baseline `d9bad5c125791306e38bca8830b4082f7f38fc6b`は163 passed、Reviewed `17bd3e7a3d81842bb5906ac7ab25329ec0be4ffb`は173 passed。QA-F01/F02未解決とReviewer契約hash不一致によりPASSではない。

## 11. QA-003 Cycle 2 HOLD対応（Plan 036）

- [x] 11.1 QA-F01: 対象SHA確定後の最終招待本文を走査し、招待SHAを状態と公開Evidenceに記録。走査後の改変をcommit前に拒否し、招待commit内blobとのhash一致後に限りpushする。bare remote fixtureで最終招待hash＝状態記録hash＝commit blob hashを確認。
- [x] 11.2 QA-F02: 既存必須checkの削除・ID変更・任意化・実行条件弱化を拒否。その他のcheck契約変更は旧新hashを含む承認を要求し、hashと構造化差分を記録する。削除、ID変更、required、argv、cwd、env、timeout、expected exit変更と不一致hashを拒否するfixtureを追加。
- [x] 11.3 基盤/runtime同期、F01/F02正常系・拒否系、全quality-loop pytest suiteを検証。Python 3.12.3、`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q`、cwd `quality-loop/`、exit 0、174 passed in 9.96s。`openspec validate unify-qa-skill-workflow --strict --json`はvalid。対象commit SHAの固定と独立QAは11.4で別途実施する。
- [x] 11.4 修正後SHAからQA依頼を作り直し、Reviewer Skill・契約hashを対象treeと照合して、別担当によるローカル独立QAを実施した。Cycle 3は174 passed、QA-F01/F02解消、QA-C3-F01を新規FindingとしてGate FAIL。記録は[Cycle 3レビュー](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c3/01_review.md)。Cycle 2のHOLD/Finding原文は変更していない。
- [x] 11.5 独立QAの結果を受領し、OwnerがQA-C3-F01の修正・再QAを選択した。修正はPlan 037で管理し、Cycle 4の独立QAがPASSするまで完了扱いしない。

## 12. QA-003 Cycle 3 Finding 対応（Plan 037）

- [x] 12.1 最終走査拒否時の停止境界と状態保存を、対象commit・最終依頼hash・case state・ユーザーindex・招待commit・remoteの各条件に分けて定義し、2026-10-05にOwnerが実装計画037を承認した。
- [x] 12.2 承認された計画に従い、QA-C3-F01の拒否状態保存と回復案内を正本runtime・配布runtime・OpenSpec・公開手順へ実装した。
- [x] 12.3 secret/個人パスの最終走査拒否について、Reviewed SHA・招待本文hash・Reviewer資材hash・check契約hashのstate一致、製品限定target commit、拒否後の再公開停止、新規stateによる同SHA再利用、招待commit/pushなし、remote/index不変をfixtureで確認した。Python 3.14.7／pytest 9.0.2、`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest tests -q`で175 passed・52 subtests passed。正本runtimeと配布runtimeは一致し、OpenSpec strict validationはvalid。
- [x] 12.4 固定Reviewed SHA `154e2ae875d7485fa9fafab60769f79bbfb45ec1` とReviewer資材hashを照合して別担当によるCycle 4ローカル独立QAを実施した。175 passed・52 subtests passed、Findingなし、Gate PASS。記録は[Cycle 4レビュー](../../../docs/Archives/qa_workflow/unify-qa-skill-workflow/artifacts/qa_cycles/unify-qa-skill-workflow/c4/01_review.md)。Cycle 3のFAIL・Finding・Evidenceは変更していない。
