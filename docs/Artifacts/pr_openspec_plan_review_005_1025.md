# add-pr-openspec-skill 第5版の独立レビュー

created: 2026-10-25 21:39 (JST)
update: 2026-10-25 21:39 (JST)
author: Codex (gpt-6.1-sol)

## 対象と判定

task 1.1として、第5版計画の独立レビューを実施した。仕様整合の指摘が残るため、PASSおよびtask 1.1の完了条件達成とは判定しない。

- 対象branch: `feat/pr-openspec-skill`
- 計画対象commit: `2c344b433996a3e94ce61fdafdfd456386669472`
- 比較基準: 第4版 `b3a4848d7dca53f1a3047db1b4b541ee7332ef08`
- 確認時のremote先端: `fb66c67aa53f54dc66b8f91101c3a2d265fffb24`
- 対象文書: `openspec/changes/add-pr-openspec-skill/` 内のproposal、design、delta spec、tasks。
- designのblob SHA: `902c191c832a872cc322ba3a3d0ceabf1d61b41a`
- designのSHA-256: `48c55995ac445550df1d6a20f13e11b5da9815f99ffe5150717958022b1075b4`

remote先端には後続の実装が追加されていたが、今回の評価は計画commitの4文書に固定した。design・proposal・delta specは後続実装commitでも同一であり、tasksは実装側でチェック状態が更新されている。後続実装の品質は今回の判定範囲に含めない。

## 方法と独立性

計画の作成・修正担当とは別のこのチャットで、固定commitのGit objectと隔離スナップショットを読んだ。さらに規則適合と仕様整合を別のサブエージェントへ割り当て、各所見を独立に取得した。同じモデル系列による確認であり、モデル間の独立性や盲検性は主張しない。規則適合と仕様整合の結果は以下に分けて保持する。

## 規則適合

**STD-001 / P2 — manifestの保存規則が未定義**

- 根拠: `design.md:188`。manifestを`docs/Artifacts/`配下の未commit JSONとして保存するが、Artifactか内部一時データか、同一slugの最大連番からの採番を適用するかが未定義。
- 適用規則: 依頼者が本会話の冒頭で提示したAGENTS.md指示。Artifactは`docs/Artifacts/`へ保存し、`{filename}_{NNN}_{MMDD}`で採番する。拡張子は原則Markdownであり、JSONそのものを禁止する規則ではない。
- 影響: 複数依頼のmanifest保存時に命名と区別の方法が実装判断へ残り、出力規則との整合が確認できない。
- 対応案: 内部一時データとして専用領域へ保存するか、`pr_openspec_manifest_NNN_MMDD.json`等の命名と例外適用を明示する。

## 仕様整合

**SPEC-001 / P1 — 公開head Pを依頼書自身に含める自己参照**

- 根拠: delta spec `specs/pr-openspec/spec.md:35`は依頼書にbase・H・Pの完全SHAを含めることを必須とする。一方、`design.md:128`は依頼書自身を含む最終commit SHAを本文に埋め込まないと定め、同129–130行は依頼書を含むcommitをPとして後から公開する。
- 影響: Pを依頼書本文に書き込むとファイル内容・tree・commit SHAが変化するため、specの必須条件と設計の公開順序を同時に満たせない。
- 対応案: 依頼書はbase・H・依頼IDを保持し、commit後にPをPR本文・P固定URL・期待値manifestで対応づける方式へspecを統一する。
- 確認方法: 生成からcommitまでの順序を文書で追い、Pを含むcommitの本文にそのP自身を要求する箇所がないことを確認する。

**SPEC-002 / P1 — RENAMEDの標準形式を台帳化できない**

- 根拠: `design.md:179`はRENAMED配下の`### Requirement:`見出しとScenarioを抽出すると定める。しかしOpenSpecの名称変更はFROM/TOの対で記述され、通常のRequirement見出しを持たない。ローカルのOpenSpec同期Skillにある書式例でもFROM/TO形式が指定されている。この抽出定義はdelta spec `specs/pr-openspec/spec.md:57`の全要求網羅および`tasks.md:13`のRENAMED例検証と整合しない。
- 影響: 名称変更だけのChangeは台帳0件として公開不能になり、他の追加要求と混在する場合は名称変更の監査基準が欠落する。
- 対応案: RENAMEDをFROM/TOとして読み、対象Hと必要な既存specから名称対応と監査対象を解決する規則を定める。解決できない場合は基準未確定とし、標準形式のfixtureを検証対象に追加する。
- 確認方法: FROM/TOだけの名称変更、およびADDEDと名称変更が混在した例の期待台帳を定義し、名称変更が黙って消えないことを確認する。

**SPEC-003 / P2 — REMOVEDが全要求台帳から脱落する**

- 根拠: delta spec `specs/pr-openspec/spec.md:57`はspecデルタの全Requirement・Scenarioを基準化すると定めるが、`design.md:179`の抽出対象はADDED・MODIFIED・RENAMEDに限られ、REMOVEDがない。`design.md:104`自身は削除後の契約を確認することを要求している。
- 影響: ADDEDとREMOVEDが混在したChangeで、削除後契約や移行条件を台帳・回答の対象にせず、追加部分の適合だけで台帳に対するPASSが成立し得る。
- 対応案: REMOVEDについて削除後契約を確認する必須基準を台帳へ含める。台帳を現行契約に限定するなら、その範囲をspecへ明示し、削除確認を別の必須基準として保持する。
- 確認方法: ADDEDとREMOVEDの混在、およびREMOVEDだけのChangeを計画の検証ケースへ追加し、削除確認が欠落しないことを確認する。

## 前回指摘への対応

第5版では既定必須の台帳と利用者承認による除外を追加している。`required`を自由に任意扱いする前回の問題に対する方針は具体化したが、抽出対象の欠落が上記SPEC-002・003として残る。proposalとtask 1.1の第3版参照は第5版へ更新されており、参照版の指摘は解消している。外部書込みの権限境界とその評価ケースも引き続き計画に含まれている。

## 検証と変更境界

- 指定計画commitの隔離スナップショットで`openspec validate --strict add-pr-openspec-skill`を実行し、終了コード0、`Change 'add-pr-openspec-skill' is valid`を確認した。
- `git diff --check b3a4848 2c344b4`は成功した。
- これらは構造・空白の検証であり、仕様矛盾の解消や後続Skill実装の適合を証明しない。
- task 1.1は独立レビューの実施結果を得た段階。PASSまたは指摘対応済みの記録という完了条件は未達のため、チェックを完了へ変更しない。Implementerが本記録を`implementation-record.md`へ反映し、計画を修正した後、修正版を対象に再レビューする。
- 既存の未追跡Artifactを保持し、本レビュー記録だけを追加した。対象の計画・実装・tasksは変更していない。作業開始時と終了時にGit差分を確認し、commit・pushは実施していない。正式Quality Loopケースへの状態変更も行っていない。

規則適合はP2が1件。仕様整合はP1が2件、P2が1件。
