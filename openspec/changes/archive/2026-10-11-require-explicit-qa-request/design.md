# 設計

## 現状と制約

提案書に記載したとおり、QA Skillのdescriptionの広さを揃え、明示的な実行依頼と単なる話題・報告を区別する。正本は`quality-loop/skills/`で、`quality-qa`、`quality-review`、`quality-response`には既存の評価例がある。`blind-qa-cycle`には評価例ファイルがない。ルート`.agents/skills/`にある3 Skillは正本と内容が異なり、`blind-qa-cycle`の同じ配置もない。

## 目標と対象外

**目標:**

- 4つの正本Skill descriptionの先頭で、現在のユーザーメッセージに明示的な実行依頼があることを共通条件として示す。
- 正例・負例を各Skillの評価データへ加え、誤発火と必要な発火の両方を確認できるようにする。
- 明示依頼があっても既存のQuality Loop案件、Role、操作、独立QAの条件は維持する。

**対象外:**

- runtime、CLI、Role遷移、案件データ形式、承認境界の変更。
- ルート`.agents/skills/`の個別コピーの同期・上書き、グローバルSkill配置、他リポジトリへの配備。
- descriptionだけでモデル選択を決定論的に強制できるとの保証。

## 設計判断

### descriptionを共通の起動条件にする

4つの`SKILL.md`のdescription冒頭に「ユーザーがこのSkillのQA操作を明示的に依頼した場合のみ使用する」と記し、Skillごとの適用範囲と短い正例・負例を続ける。結果の提示だけ、説明・相談、一般的なコードレビュー、別目的のOpenSpec依頼は非発火例に含める。明示依頼の例はQA実施、独立レビュー、再QA、依頼された状況確認など、Skillの既存操作に合わせる。

### Skill固有条件を残す

descriptionの共通条件を追加しても、`quality-review`の案件・Reviewer条件、`quality-response`のImplementer条件、`quality-qa`の通常QAとformal caseの境界、`blind-qa-cycle`の明示起動とモード条件は変更しない。評価例は共通の起動条件に加え、それぞれ固有条件も確認する。

### 正本と評価データだけを対象にする

変更するSkill定義は`quality-loop/skills/<skill>/SKILL.md`とする。3つの既存`evals/evals.json`に正例・負例を追加し、`blind-qa-cycle`にも同形式の評価ファイルを設ける。descriptionと評価データの条件を確認する静的テストを追加し、例の記載漏れや4 Skill間の不整合を検出する。ルート`.agents/skills/`のコピーは正本と異なるため、このChangeから自動同期・上書きしない。

## リスクとトレードオフ

- [descriptionはモデルへの選択指示であり決定論的な実行制御ではない] → 正例・負例を含む評価で代表会話を確認し、保証範囲を説明文の改善と選択評価に限定する。
- [descriptionを強く限定すると明示依頼も拾いにくくなる] → 各Skill固有の言い換え例を含む正例を用意し、必要な依頼の取りこぼしも評価する。
- [正本だけを変更しても、別配置の旧コピーは変わらない] → このChangeでは外部・ルート`.agents/skills/`を配備しないことを明記し、必要な配置更新は別の明示依頼で行う。

## 移行

実装時は正本の4 description、評価データ、静的テストを変更し、正負例を確認する。グローバル配置やルート`.agents/skills/`コピーの更新は含めない。RollbackではこのChangeで変更した正本と評価データだけを戻す。
