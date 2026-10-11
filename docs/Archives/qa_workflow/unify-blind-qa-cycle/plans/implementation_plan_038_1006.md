# blind-qa-cycle統合計画

created: 2026-10-06 23:58 (JST)
update: 2026-10-07 00:33 (JST)
author: Codex (GPT-6)

## 目的

分散している`blind-qa-cycle`の実装と運用知見を調査し、長所を統合して短所を解消した単一のSkillにする。QA対象はクラウドまたはローカルの独立Reviewerが監査用ブランチ上で確認し、実装側へ再現可能な指摘・修正タスクを返し、修正後の再QAを経て監査サイクルを同ブランチ上で終結できるものとする。QA終結時に人が5分程度で自分の理解を記録する「Human Understanding Note」の作成を助ける道具も、このサイクル内に設ける。`main`等へのマージは本フローの自動処理に含めず、Ownerとの相談・別判断に委ねる。

## 現状調査

作業開始時点のGit状態は`master...origin/master`でclean。既存差分は確認されなかった。

確認できた同名Skillは以下の二つ。

- `.agents/skills/blind-qa-cycle/`: 古い版。既存topic branch上のチェックポイント、Reviewed Yip commit、招待、レビュー4成果物、修正サイクルの基本手順を持つ。
- `quality-loop/skills/blind-qa-cycle/`: Git追跡対象の現行版。旧版の手順に加え、受入基準のID・原文固定、Reviewer Skill/契約のSHA-256固定、Cloud側での同一SHA読取検証、dirty checkoutのread-only preflightなどがある。

また、`quality-loop/skills/`には同名Skill以外に、QA関連Skillとして`quality-qa`、`quality-review`、`quality-response`がある。これらは今回の統合対象ではなく、役割の異なる既存フローとして扱う。

| Skill | 現行の役割 | 今回の扱い |
|---|---|---|
| `blind-qa-cycle` | Yip commitと固定SHAを使い、独立QA依頼・レビュー成果物・再QAをtopic/監査ブランチ上で往復させる明示起動型のサイクル | 今回の統合対象。分散した同名版を整理し、この用途の単一Skillにする |
| `quality-qa` | 通常QAの入口。依頼、結果確認、承認後のローカル修正、再QA、利用者の終了判断を案内する | 維持する。通常QAは引き続きこちらへ案内し、blind cycleとの入口選択・結果形式・Git責務の境界を明記する |
| `quality-review` | 正式Quality Loop案件のReviewer RoleをCLI経由で進める | 維持する。正式caseのreview/verify等をblind cycleの4成果物や状態管理に置き換えない |
| `quality-response` | 正式Quality Loop案件のImplementer応答をCLI経由で提出する | 維持する。caseのFinding応答・Plan承認境界をblind cycleで代替しない |

従って「同じSkillにする」は`blind-qa-cycle`の分散版を一本化する意味であり、`quality-qa`、`quality-review`、`quality-response`まで統合・改名・削除する意味ではない。実装時には各Skillの既存契約を読み、名称・入口・成果物・case正本/CLI・Git commit/push責務・次担当のhandoffを照合する。必要な連携は、適切なSkillへ案内する境界の明文化に限り、他Skillの実装や既存caseデータを変更しない。

両者で共通する強みは、Baseline/Reviewed SHAを固定した独立レビュー、監査前後のYipコミット、ローカルとクラウドのAudience区別、サイクルごとの出力保存、再QA時に前サイクルを凍結する考え方、mainへのマージとOwner判断の分離である。現行版固有の強みは、受入基準とReviewer資料の完全性・真正性確認、および既存変更の誤操作防止である。

統合時に解消すべき点は、二つの配置に同名Skillが残ること、他のQA Skillとの役割境界・入口選択がblind cycleの説明に明示されていないこと、QA開始からFinding対応・再QA・終了までの分岐が多く入口が分かりにくいこと、事前ベースラインQAと実装後の即時QAの選択条件が一連のライフサイクルとして説明されていないこと、QA完了後の監査ブランチ終結条件が明確でないことである。旧側は追跡対象外の配置なので、統合後に参照コピーをどう扱うかも変更対象として決める。

## 目標フロー

1. **開始・監査ブランチ確認**: 監査対象のtopic branchを明示し、既定ブランチでは開始しない。branch、HEAD、upstream、staged/unstaged/untrackedをread-onlyで確認し、無関係または不明な変更を混ぜない。
2. **開始時期の選択**: 理想は実装前にBaselineを固定してQA依頼の骨格と受入基準を作成する。事前作成できなかった場合は、完了した対象ファイル群を実装側が明示的にYip commitへ固定し、そのcommitをReviewedとしてQA依頼を発行する。開始時期とBaselineの意味を招待に記録し、事後作成を事前QAと誤認させない。
3. **QA handoff**: 招待にRepository、branch、Baseline/Reviewedの完全SHA、受入基準全文とfingerprint、変更パス、Reviewer資料のhash、出力先、Audience、実行可能な必須checkを含める。ローカルは共有clone内の監査ブランチを使用しpushしない。クラウドはtopic branch上の必要commitだけを可視化し、対象commitが取得できなければ別tipへ置換せずHOLDにする。
4. **独立レビュー**: 実装担当とは独立したReviewerが固定diffと基準を検査する。指定された出力DIRに日本語の評価、Finding別の具体的修正依頼・完了条件・検証方法、状態機械向け結果を保存する。実行必須checkの結果・未実施理由を区別する。
5. **実装側対応と再QA**: 実装側はFinding単位で対応し、修正をYip commitとして監査ブランチへ追加する。再QAは新しいサイクルDIRとし、前回Reviewedを次回Baselineとして固定する。前サイクルの依頼・評価・結果を上書きしない。
6. **終結準備**: 全Findingの処置と再QA結果、残余リスク、最終Gate、関連SHAを確認する。終結はOwner受入や製品マージを意味しない。main等へのマージ、配備、削除、pushは明示的に別判断する。
7. **理解の記録とサイクル終結**: `blind-qa-cycle`を使ったQAサイクルの最後に、担当者が5分程度でHuman Understanding Noteを自分の言葉で記入できる支援を提供する（通常QAやformal Quality Loop案件へ一律に適用しない）。Noteは今回のsystem boundary、守るinvariant、最も危険だったfailure mode、その防止mechanism、AIなしで説明できる設計、未理解点を記録し、対象cycle・関連SHA・QA結果へ結び付ける。QA報告やAIの説明をNoteへ自動転記して理解したように見せず、未理解点をそのまま残せるようにする。Note記録をサイクルの終結記録に含めるが、Noteの内容をQAのPASS/FAILやOwner受入の条件にはしない。

## 実装対象案

- 正本Skillを`quality-loop/skills/blind-qa-cycle/`に一本化し、参照配置が必要な場合も複製本文を持たず、管理方法を明文化する。
- `quality-qa`、`quality-review`、`quality-response`は統合・変更・削除せず、各々の既存用途を維持する。blind cycleを使う条件、通常QA/formal Quality Loopへ案内する条件、各フロー間で受け渡す情報と受け渡さない正本データをSkill本文で明確にする。
- Mode/入口をライフサイクル中心に整理し、事前Baseline、事後開始、レビュー、対応、再QA、終結を示す。cloud/localは同じQA契約のhandoff差として定義する。
- 既存のSHA固定、受入基準完全転記、Reviewer資料hash、read-only preflight、main/master guard、対象限定stage、push制御を維持する。
- `00_invite.md`およびQA結果DIRの契約、machine schema、各referenceを新ライフサイクルに整合させ、禁止操作と終結条件を明記する。
- QA終結後にHuman Understanding Noteの空テンプレートを作成・表示・保存する支援を`blind-qa-cycle`に追加する。配置は対象cycle DIRとし、cycle ID、Repository/branch、関連Baseline/Reviewed SHA、最終Gate等の出典を参照可能にする。人の記述内容は自動生成・採点・修正せず、未理解点や空欄を許容する。具体的なCLI/Skill内コマンド方式は設計段階で既存構成に合わせて決める。
- 必要なskill/fixture/doc検証を行い、現行契約との後方互換・移行方針を記録する。既存cycle成果物の書換え・移動・削除は行わない。

## 作業段階

1. **設計確定**: `blind-qa-cycle`全ファイルと`quality-qa`、`quality-review`、`quality-response`の入口・関連参照、git履歴、呼出元、QA成果物実例、既存テスト/validatorを調査し、役割分担・入口選択・handoff境界・状態遷移・commit境界・ローカル/クラウド差・Human Understanding Noteの配置と作成支援方式・完了条件を確定する。
2. **単一Skill統合と記入支援追加**: 承認済みの正本配置と参照配置方針に限定してSkillおよび参照契約を編集し、Human Understanding Noteの作成支援を追加する。各編集ラウンドで開始時/終了時の差分を記録し、既存ユーザー変更を保持する。
3. **検証**: Skill構造、相対リンク、スキーマ、代表的なlocal/cloud、事前/事後開始、再QA、HOLD経路、監査ブランチ終結、Noteの生成・cycleとの紐付け・手書き保持を検証し、未検証事項を区別して報告する。これはSkillの挙動検証であり、独立QA受入・Owner判断ではない。
4. **レビュー可能な報告**: 変更パス、差分、検証結果、残余リスク、監査ブランチ上の終了状態、Noteの保存場所、main等へのマージ未実施を提示する。

## 受入条件

- 同名Skillの正本が一意であり、古い本文を使って誤起動する経路がない。
- `blind-qa-cycle`を使う独立ブランチ監査、`quality-qa`を使う通常QA、`quality-review`/`quality-response`を使う正式caseの選択条件が明確で、互いの成果物・case正本・CLI責務を誤って混同しない。
- 他のQA Skillを今回の統合対象に含めず、既存利用方法とデータを変更しないことが差分と検証記録で確認できる。
- 実装前Baselineと事後開始の両方が明確に説明され、それぞれのコミット・SHA・招待の関係が追跡可能。
- Local/Cloudの違いがAudience、remote visibility、handoff、git帰着に限定して理解できる。
- QA側は固定対象に対する評価と修正依頼を所定DIRに保存し、実装側はFinding単位にYip commitで対応できる。
- 再QAは新規サイクルを作成し、過去サイクルを不変に保つ。
- QA終結の条件とOwner判断境界が明文化され、main等へのmergeが暗黙実行されない。
- QA後にHuman Understanding Noteを短時間で人が記入できるテンプレート/作成支援があり、対象cycleと関連SHA・QA結果を追跡できる。
- Note本文をAIが代筆・採点して人の理解として扱わず、未理解点を記録可能で、Note自体をQAのPASS/FAILやOwner受入の根拠にしない。
- Noteは該当する監査サイクルの成果物として監査ブランチ上に保存され、過去cycleのNoteを後続cycleで上書きしない。
- staged/unstaged/untrackedの既存変更、無関係パス、誤ったbranch、対象SHA欠落を安全に扱う。
- 検証結果は成功・失敗・未実施を区別し、実装完了や独立QA受入を誤って主張しない。

## 対象外

- `main`/`master`へのmerge、production配置、旧版Skillの外部削除、remote push（クラウドQAのための承認済み限定pushを除く）、force-push。
- 既存QAサイクル記録の書換え・移動・削除。
- Ownerとしての受入・裁定、QA対象製品コードの修正。
- 本計画Artifact作成後のコード・Skill・依存関係変更。これらはユーザーの明示承認後に限る。

## 承認ゲート

本書は調査結果と実装計画であり、実装承認ではない。対象配置、ライフサイクル、受入条件に対する明示承認を受けた後に限り、実装段階へ進む。
