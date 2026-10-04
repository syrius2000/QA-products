# 統合QAの実装タスク

created: 2026-10-04 09:39 (JST)
update: 2026-10-04 21:17 (JST)
author: Codex (GPT-6)

本書は計画033承認後の実装タスクを追跡する。チェック済みは実装とEvidenceが揃った項目だけとし、書類作成・strict検証を機能実装や独立QAの完了に数えない。

## 1. 実装境界と基準の固定

- [x] 1.1 4書類と計画033の承認範囲を確認し、調査HEAD `ad6ca1ee196bd75bed026858c2de9586ca49c85c`の既存隔離worktreeを確認した。元checkoutの既存差分とindexは[持込元manifest](../../../docs/Artifacts/qa_source_manifest_001_1004.md)、本worktreeの開始時点47 status entries・内容hash・staged/unstaged diff hashは[実装baseline](../../../docs/Artifacts/qa_implementation_baseline_001_1004.md)に固定した。worktreeはdetached HEADのまま使用し、branch自動作成・pushはしない。
- [x] 1.2 既存Coreと旧2スキルruntimeの相対パス・サイズ・SHA-256 manifest、旧runtime同士の一致、既存テスト入口と過去結果の証拠限界を[開始時インベントリ](../../../docs/Artifacts/qa_runtime_inventory_001_1004.md)へ記録した。外部配置先と旧正本は開始時差分に含まれない。
- [x] 1.3 新runtimeの配置・変更対象と受入領域・Evidenceの対応を[開始時インベントリ](../../../docs/Artifacts/qa_runtime_inventory_001_1004.md)に固定し、旧case engineを変更せず独立 `qa_workflow` packageへ追加した。

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
- [x] 5.3 Markdown parserで全受入基準、check ID/状態/argv/cwd/env/timeout/runtime/exit code/duration/stdout・stderr excerptと完全出力hash、実施側taskとFinding参照を照合する。必須FAIL→総合FAIL、必須NOT_RUN/ERROR→INCONCLUSIVE、契約不一致→確認待ちを回帰fixtureで確認。
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
- [ ] 9.3 別の独立担当によるQAを実施し、指摘・対応・未検証・残余事項を記録する。実クラウドQAを行う場合は明示指示の公開範囲を確認し、fixture検証と実環境QAのEvidenceを区別する。
- [ ] 9.4 実装報告へ要件対応、タスク数、実行検証、独立QA状態、未確認事項、外部配置・削除・commit・push・master統合の実施有無と次操作を記載する。終了判断と統合の指示がなければ実行せず、既存差分を保持した最終差分で今回の境界を確認する。
