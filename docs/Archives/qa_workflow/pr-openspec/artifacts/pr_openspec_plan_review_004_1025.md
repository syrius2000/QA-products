# add-pr-openspec-skill 第4版の独立レビュー記録

created: 2026-10-25 21:23 (JST)
update: 2026-10-25 21:23 (JST)
author: Codex (GPT-6)

## 対象と範囲

対象branchは `feat/pr-openspec-skill`、対象commitは `b3a4848d7dca53f1a3047db1b4b541ee7332ef08`。対象Changeは [`add-pr-openspec-skill`](../../openspec/changes/add-pr-openspec-skill/) の `proposal.md`、`design.md`、`specs/pr-openspec/spec.md`、`tasks.md`。`design.md`のblob SHAは `03722e70dae4e82baaa9425fa9de616c69045415`。

Skill実装は依頼どおり未開始で、今回は計画・OpenSpec Changeだけをレビューした。指定commitのスナップショットに対し `openspec validate --strict add-pr-openspec-skill` を実行し、成功を確認した。これはOpenSpec構造の検証であり、Skillの実装検証ではない。

Quality Loopケース `add-pr-openspec-skill-v4-review` で通常のreviewを実行した。case revision 2、handoff `hnd-19610785-371c-4098-a65d-6cc55f2cff8e`。このケースにはF-001とF-002を記録し、現在の次担当はImplementer、次操作は `submit-response`。別レビュアーの読み取り専用確認では追加指摘I-001、I-002を得た。これら2件はQuality Loopケースrevision 2には登録されていないため、独立レビューの追加所見として区別して報告する。

## 指摘

| ID | 重要度 | 根拠と所見 | 推奨対応 |
|---|---|---|---|
| I-001 | P1 | `design.md` 164・177行は必須基準の`out_of_scope`をINCONCLUSIVEにする一方、`required`の値はSkillが対象Changeの要求から決めるだけで、Requirement/Scenario由来基準を全件抽出し、必須に固定する規則がない。該当source requirementをmanifest上で`required: false`にすれば、回答を`out_of_scope`としてもPASSし得る。`tasks.md` 12行の基準ID網羅も、回答とmanifest間の照合であり、manifest自体のsource網羅性を検証していない。 | manifest各基準にChange ID・source path・Requirement/Scenario IDを必須化する。全Requirement/Scenario由来基準は`required: true`とし、`required: false`は補助基準に限定する。source欠落・重複・網羅不足・Requirement由来基準のfalseをINCONCLUSIVEにする試験を追加する。 |
| F-001 | Medium | `design.md` 108行は監査依頼書を`docs/Artifacts/pr_openspec_review_NNN_MMDD.md`に作るが、依頼者提示のArtifact規則（日本語本文、JSTのcreated/update/authorヘッダー、同一slugの最大連番+1）をその出力へ適用する仕様がない。231行は規則の出どころを確認できず未反映と記録しているが、本依頼に規則が提示されている。 | Skill仕様とテンプレートにArtifact規則を追加し、分割時も番号が衝突しない採番手順を定める。 |
| F-002 / I-002 | P2 | `proposal.md` 27行は計画書v3と旧SHAを参照する。`design.md` 4行の`update`は第3版時点のまま、231行で第4版更新を追記している。さらに`tasks.md` 5行のtask 1.1は第3版の独立レビューを対象に固定しており、第4版レビューを完了条件にしていない。 | `proposal.md`の参照版・SHAと`design.md`の更新日時を現行版に揃える。task 1.1は第4版の固定commit/SHAを対象にし、今回のレビュー結果と指摘対応を記録する条件に更新する。 |

## 第3版からの修正確認

- **必須基準の`out_of_scope`問題:** 第4版で判定ルールとfixture要件が追加された（`design.md` 164、172、188行、spec 48–50行）。ただし、必須基準を全件manifestに載せて`required: true`にする保証がないため、I-001の迂回経路が残る。
- **外部書込みの権限境界:** 権限要件と模擬ケースが追加された（spec 56–62行、`design.md` 216–219行、tasks 22・26行）。この指摘は設計上解消されている。
- **Artifact規則:** 第4版でも未反映のまま。

## 判定境界

第4版には未解消のP1があり、計画は独立レビュー済みPASSとは判定できない。Quality LoopケースではF-001（Medium）とF-002（Medium）が未解消。Peer reviewからのP1/I-001とP2/I-002は別記録である。Skill実装・activation eval・checker試験・PR動作の検証は未実施であり、実装完了を示すものではない。

対象branchはremote上で確認した。レビューのためcommitをFETCH_HEADへ取得し、対象Changeのスナップショットを`/tmp`へ展開した。作業開始時と終了時の作業branchは`main`で、既存の未追跡`docs/Artifacts/`を保持した。リポジトリ内の変更はこのレビュー記録1ファイルのみ。commit・pushは行っていない。
