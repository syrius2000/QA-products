# add-pr-openspec-skill 第6版と実装の独立レビュー

created: 2026-10-25 21:55 (JST)
update: 2026-10-25 21:56 (JST)
author: Codex (gpt-6.1-sol)

## 判定と対象版

**判定: 指摘あり（修正が必要）。** 指定テスト37件は通過したが、計画・spec・実装の不整合と、既存テストが検出しない不正入力のPASSを確認した。task 1.1の独立レビューは実施済みだが、指摘対応済みまたはPASSという完了条件は満たしていない。

| 項目 | 固定した対象 |
|---|---|
| repository | `syrius2000/QA-products` |
| branch | `feat/pr-openspec-skill` |
| 対象commit | `67f8c8febc3f6f633efad6db9516f5f320a0ed71` |
| 前回計画レビュー対象 | `2c344b433996a3e94ce61fdafdfd456386669472` |
| 対象範囲 | `openspec/changes/add-pr-openspec-skill/`と`quality-loop/skills/pr-openspec/` |
| designのblob SHA | `dea2752360fbfb31e95eeb79cd6faf734a7d224d` |
| build_ledger.pyのblob SHA | `16fdd89ff5cf6ea1a608451d08761dbb558b4577` |
| validate_review_reply.pyのblob SHA | `baefb2ddedf70b8efbc7bd667c40dadfcd072769` |

確認時のremote branch先端は指定commitと一致した。指定commitを隔離スナップショットへ展開し、作成者の検証結果とは別にテストと追加の再現確認を実行した。台帳処理と規則適合は別のサブエージェントも読み取り専用で確認した。同じモデル系列内のレビューであり、モデル間の独立性は主張しない。

生成Artifactの日本語・JSTヘッダー・連番規則の未実装自体は、今回の明示的な対象外として指摘に含めていない。出どころの記録有無だけを確認した。

## 前回4件の解消確認

| 前回の指摘 | 評価 | 確認結果 |
|---|---|---|
| 1. 依頼書が自身のPとblob SHAを持つ自己参照 | **未解消** | design・テンプレートでは解消。テンプレート8行はP/blobを本文へ書かないとし、回答例61–62行はPR本文の値を参照する。しかしdelta spec 35行には依頼書へPの完全SHAを含めるMUSTが残る。P1-001。 |
| 2. RENAMEDのFROM/TOを台帳化できない | **解消** | `build_ledger.py:61–78`でFROM/TOを対として処理し、TO名と旧名を要求項目にする。FROMのみ、TOのみ、連続FROMは終了コード3となるテストがある。`tests/test_build_ledger.py:72–83,125–133`。 |
| 3. REMOVEDが台帳から漏れる | **新たな問題** | 実装とREMOVED要件は解消。`build_ledger.py:21,79–91`がREMOVEDのR/Sを抽出する。ただしdesign 179行とSKILL 32行の対象列挙は旧記述のままで、実装・新要件と矛盾する。P2-004。 |
| 4. manifestの保存・命名が未定義 | **解消** | `design.md:189`と`SKILL.md:53`が`docs/Artifacts/pr_openspec_manifest_<request_id>.json`、未追跡・ローカル専用と定義する。今回対象外の一般的な連番規則との適合は、この評価に含めない。 |

## 規則適合の指摘

### Medium-001: Artifact規則の出どころが記録されていない

- **対象:** `openspec/changes/add-pr-openspec-skill/implementation-record.md:23`、`design.md:245`。
- **事実:** 両文書は規則の出どころを「未確認」とするだけで、出典を記録していない。規則が実装されていないこと自体は今回の指摘対象外。
- **出典確認:** この会話の冒頭でユーザーが提示した「AGENTS.md instructions for /Users/myamaguchi/Programing/00TotalRWD/QA-products」に、日本語本文、JSTのcreated/update/author、同一slugの最大連番+1という指示がある。一方、対象commitのルート`AGENTS.md`にはそのArtifact規則の本文はなく、プロジェクトの安全弁・QA包括委任が記載されている。ユーザーが提示した規則とGitで追跡されるAGENTS.mdを混同しないことが必要である。
- **影響:** 次版で規則を扱う際、どの指示を根拠としたかを対象commit内の記録から追跡できない。
- **確認方法:** 次版の実装記録に、ユーザー提示指示の所在・該当規則と、対象commitのAGENTS.mdには本文がないことを記録する。形式の実装自体は今回要求しない。

## 仕様整合の指摘

### P1-001: 自己参照を要求するdelta specが残っている

- **対象:** `openspec/changes/add-pr-openspec-skill/specs/pr-openspec/spec.md:35`。関連箇所は`design.md:128,189`、`quality-loop/skills/pr-openspec/assets/review_request_template.md:8,53,61–62`。
- **事実:** delta specは「監査依頼書に…base・H・Pの完全SHA…を含めなければならない（MUST）」のまま。designは依頼書にP/blobを含めず、公開後にPR本文とmanifestへ記録すると定め、テンプレートもその方式へ修正されている。
- **影響:** 依頼書を含むcommitをPとする公開順序と、依頼書本文へPを含める必須要件は両立しない。第6版の実装方式に従うと、正本specのMUSTに違反する。
- **確認方法:** spec 35行とdesign 128・189行を照合する。依頼書を生成してPを確定した後、P自身をその本文へ追記するとtree/commitが変化することを公開順序に沿って確認する。実際の公開操作は不要。
- **対応案:** specの必須内容をbase・H・依頼IDへ合わせ、Pと依頼書blobを公開後にPR本文・期待値manifestへ対応づける要件を明記する。テンプレートへPを戻して解消しようとしない。

### P1-002: 承認者と理由がnullでも承認済み除外としてPASSする

- **対象:** `quality-loop/skills/pr-openspec/scripts/validate_review_reply.py:71–76,152–155`。基準はdelta spec 67–69行、design 166・182行。
- **事実:** manifestの承認者・理由を`str(value).strip()`で確認するため、JSONの`null`がPythonの`None`を経由して非空文字列`"None"`になり、有効と扱われる。
- **再現:** `tests/fixtures/manifest.json`の`required: false`項目を`"exclusion": {"approved_by": null, "reason": null}`へ置換した一時manifestと、既存の`reply_optional_out_of_scope.json`をCLIへ渡した。
- **観測結果:** 終了コード0、`result: PASS`、`structure: valid`、`problems: []`。内訳はconforms 3、out_of_scope 1。
- **期待結果・影響:** 承認者と理由がない除外はINCONCLUSIVEであるべきだが、実装は対象外を承認済みと扱う。必須基準を除外する際の中心的な検査を通過してしまう。
- **確認方法:** 上記入力のCLI結果が終了コード2となることを確認する。既存`test_manifest_unapproved_exclusion_is_inconclusive`は欠落フィールドだけを確認し、null等の型違いを検査していない。
- **対応案:** 承認者・理由を実際の非空文字列として検証し、null・配列・object等を拒否する。

### P2-001: 回答schemaに違反する入力を形式有効・PASSと判定する

- **対象:** `quality-loop/skills/pr-openspec/scripts/validate_review_reply.py:118–145,163–168`。基準は`references/review_reply.schema.json:6,32,41`、design 27・138・174行。
- **事実:** checkerは回答schemaを読み込まず、必須の`findings`・`unverified_items`を省略時に空配列扱いする。さらにevidenceの要素を文字列化して有無だけを確認するため、`[null]`も根拠ありと認める。
- **再現:** `reply_pass.json`から`findings`・`unverified_items`を削除し、最初の基準の`evidence`を`[null]`に置換して、正常manifestとともにCLIへ渡した。
- **観測結果:** 終了コード0、`PASS`、`structure: valid`、`problems: []`。一方、schema 6行は両フィールドを必須とし、32行はevidenceを文字列の配列とする。
- **影響:** 必須項目・型が不正で実際の根拠がない回答を、有効な適合回答として返す。task 2.1が求めるschemaの正常・欠落例検証も、現在のテストでは証明されていない。
- **確認方法:** この変形入力をINCONCLUSIVEにする試験を追加し、checkerの実際の受理条件とschemaを照合する。既存37件が通るだけでは本件を検出できない。
- **対応案:** schemaと一致する型・必須項目検査を行う。標準ライブラリのみという制約を維持する場合でも、schemaで宣言した制約を決定的な検査に反映する。

### P2-002: kept_findingsがFindingの内容を保持しない

- **対象:** `quality-loop/skills/pr-openspec/scripts/validate_review_reply.py:150–151`、`tests/test_validate_review_reply.py:74–84`。基準はdesign 139・174行の「確実なFindingは保持」。
- **事実:** `kept_findings`に入れるのは`criterion_id`と`verdict`だけであり、回答のFindingにあるobservation・impact・how_to_verifyや基準のevidence・reasonを引き継がない。既存テストもcriterion_idの一致だけをassertする。
- **再現:** 既存の`reply_fail_nonconforming.json`へ未知IDのconforms基準を1件追加して、構造不備と既知の不適合を混在させた。これは既存テストと同じ条件。
- **観測結果:** INCONCLUSIVEになり、入力Findingの`observation: 観測`・`impact: 影響`・`how_to_verify: 確認方法`は出力へ残らず、`kept_findings`は`[{criterion_id: …#1.2, verdict: nonconforming}]`のみとなる。
- **影響:** checker出力だけを後工程へ渡すと、不適合が存在することは分かるが、何が問題でどう検証するかを復元できない。原回答ファイルを再度参照する必要がある。
- **確認方法:** 構造不備時に、元のFinding本文・関連根拠が出力に保持されていることまでassertする。
- **対応案:** Finding本文と関連する基準の根拠を保持するか、原回答の当該内容へ確実に戻れる参照契約を明示する。

### P2-003: 期待値manifestの出どころがPR本文へ逆戻りしている

- **対象:** `quality-loop/skills/pr-openspec/SKILL.md:53`。基準は`openspec/changes/add-pr-openspec-skill/design.md:132,189–190`。
- **事実:** designは期待値をGitHub APIやGit objectから取得し、PR本文・コメントを期待値の出どころにしないと定める。一方、SKILL 53行の末尾はP/blobを「PR本文から取得する」と指示する。同じ行の前半のGitHub/Git object取得条件とも整合しない。
- **影響:** PR本文が古い値のまま、または後から誤記された場合、その値を期待値manifestへ転記すると、古い回答と一致してPASSする可能性がある。checker自身はremoteの現在状態を調べないため、呼出し側の取得手順が唯一の防止手段となる。
- **確認方法:** P/blobについて、PR本文を編集してもGitHubの実headとそのtreeのblobから期待値を構成することを手順上確認する。本文記載値は照合先とし、唯一の正本にしない。今回のレビューでは実PR本文は変更していない。
- **対応案:** ReviewerがPR本文の識別値を回答へ引用することと、Skillが期待値を独立取得することを区別する。実head SHAと、そのSHAに属する依頼書blobをAPI/Git objectから取得し、本文との不一致を検出する手順に統一する。

### P2-004: REMOVED対応がdesign・SKILLの対象列挙へ反映されていない

- **対象:** `openspec/changes/add-pr-openspec-skill/design.md:179`、`quality-loop/skills/pr-openspec/SKILL.md:32`。関連する新規定はdesign 183行、delta spec 63–65行、`scripts/build_ledger.py:21,79–91`。
- **事実:** 新規定と実装はREMOVEDを含むが、designとSKILLの台帳対象一覧はADDED・MODIFIED・RENAMEDだけを列挙している。標準FROM/TOに対応済みのRENAMEDについても、design 179行の「配下の全### Requirement」という旧抽出記述が残る。
- **影響:** 実装は削除要求を出力するが、手順・設計文書の正本を読む人は対象範囲を別のものとして解釈する。今回求められた計画と実装の整合を満たさない。
- **確認方法:** 4種のdeltaを同一specへ置いた追加確認では、R#1、S#1.1、R#2、S#2.1、R#3、R#4、S#4.1が出力され、番号衝突はなかった。実装の出力とdesign・SKILLの列挙を照合すれば不一致を確認できる。
- **対応案:** design 179行とSKILL 32行を4種のdelta・FROM/TO対応へ更新し、183行との重複説明を整合させる。

## 指定の検証結果

| 検証 | 結果と範囲 |
|---|---|
| `openspec validate add-pr-openspec-skill --strict` | 終了コード0、`Change 'add-pr-openspec-skill' is valid`。隔離スナップショットで実行。 |
| `python -B -m pytest tests -q -p no:cacheprovider` | **37 passed in 2.90s**。標準python3にpytestがなかったため、一時領域のvenvにpytest 9.1.1を導入して実行。Python 3.14。グローバル環境・リポジトリ依存関係は変更していない。 |
| `build_ledger.py --root <元repo> --head 67f8c8f --change add-pr-openspec-skill` | 終了コード0、headは完全SHAに一致、**19件（R 7・S 12）**。出典blobは`843b751c68f55d29d68cd5523dcc95481e15de81`。この対象specは全件ADDEDのため、この実行だけで他delta種別を検証したとは扱わない。 |
| 混在deltaと番号付け | 追加のメモリ内入力でADDED・MODIFIED・RENAMED・REMOVEDを混在させ、7項目、ID一意性、REMOVED配下Scenarioの採番を確認。RENAMEDのR番号をまたいでも衝突なし。 |
| null承認のCLI入力 | 本来INCONCLUSIVEにすべき入力がPASS。P1-002。 |
| schema不正のCLI入力 | 本来INCONCLUSIVEにすべき入力がPASS。P2-001。 |
| 構造不備時のFinding保持 | INCONCLUSIVEへの遷移は正しいが、本文がkept_findingsに残らない。P2-002。 |
| 差分の空白検査 | `git diff --check 2c344b4 67f8c8f`の対象範囲に問題なし。 |

既存テストは正常・不適合・未確認、IDの欠落/余剰/重複、版不一致、JSON block数、FROM/TOの対応不備、REMOVED要求のR項目を実際に検査している。一方、承認値の型、schemaの必須項目とevidence要素型、保持Findingの本文は十分に検査していない。したがって37件通過と、本レビューで追加確認した規則の適合は区別する。

## 権限境界と検証上の限界

`SKILL.md:63–68`、`evals/evals.json:31–58`、delta spec 71–77行には、準備時の外部書込み禁止、明示許可の範囲、merge・履歴改変・外部Skill配備の拒否、第三者回答の命令をデータ扱いする規定がある。この点に明白な文書上の不整合は確認しなかった。evalsはケース定義として確認したが、実モデルによる起動・手順実行評価はしていない。実PRの公開・本文更新・レビュー依頼もしていない。

指定どおり、対象コード・計画・tasks・実装記録は編集していない。本記録以外のリポジトリファイルを変更せず、commit・push・PR操作・正式Quality Loopケースへの書込みも行っていない。実行用のスナップショット、venv、再現用JSONはリポジトリ外の一時領域に保存した。作業開始時と終了時にGit差分と既存Artifactの内容を照合した。

規則適合は出典記録のMedium 1件。仕様整合はP1 2件、P2 4件。Artifact形式未反映そのものは集計対象外。
