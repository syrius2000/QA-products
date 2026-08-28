# QMS思想Reference

created: 2026-08-27 21:51 (JST)
update: 2026-08-27 21:53 (JST)
author: Codex Research Agent (GPT-5.6 Luna)

## 目的と位置付け

本書は、将来の`quality-review`／`quality-response` Skillが、品質判断の意味を解釈するときだけ読む詳細Referenceである。通常の状態遷移、status表示、単純な入出力処理では読み込まない。規格・ガイダンスの思想を本QMSの設計判断へ要約した教育・設計資料であり、法規制、GxP、ISO、FDAその他への適合宣言、認証、validation完了の証拠ではない。

ICH Q10は医薬品品質システムのモデルであり、既存の地域GMPを置き換えるものではなく、ライフサイクルに応じて適切かつ比例的に適用する考え方を示す。[ICH Q10（公式PDF）](https://database.ich.org/sites/default/files/Q10_Guideline.pdf)

## QMSの中心命題

品質とは、単に修正を提出した状態ではない。要求を明確にし、リスクに応じたEvidenceを集め、判断を要求へtraceし、不確実性を明示し、必要な修正の有効性を確認し、handoffの受領まで閉じた状態である。人やAIの一時的な注意力に依存せず、役割、制約、確認、履歴によって誤りの影響を小さくする。

## 規範となる8原則

### 1. 品質基準とリスク許容は人間Ownerが決める

Ownerは、対象の目的、受入基準、許容できる残余リスク、エスカレーション先を定める。AIは選択肢、根拠、未確実性を提示できるが、組織のリスク許容や最終責任を自動的に決めない。ISO 9001のプロセス所有権・説明責任、ICH Q10の経営責任、NIST AI RMFの責任構造と整合する。[ISO 9001 プロセスアプローチ](https://www.iso.org/files/live/sites/isoorg/files/archive/pdf/en/iso9001_2015_process_approach.pdf)／[ICH Q10](https://database.ich.org/sites/default/files/Q10_Guideline.pdf)／[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

### 2. 判定は要求とEvidenceへtraceできる

判定には、どの要求・Finding・受入条件を、どのEvidence（内容、出所、時点、適用範囲）で評価したかを残す。Evidenceから導けない断定は、受入済みではなく`unverified`または`evidence-gap`とする。ICH Q9(R1)が科学・知識・データの健全性をリスク判断の基盤とし、ISO 9001が入力・出力・プロセス相互作用・測定を管理対象とする思想を、trace可能な記録へ落とし込む。[ICH Q9(R1)](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)／[ISO 9001 プロセスアプローチ](https://www.iso.org/files/live/sites/isoorg/files/archive/pdf/en/iso9001_2015_process_approach.pdf)／[MHRA GxP Data Integrity](https://www.gov.uk/government/publications/guidance-on-gxp-data-integrity)

### 3. 不確実性を隠さない

観測できていないこと、根拠が弱いこと、解釈が分かれること、実行経路やruntime Evidenceがないことを、判定と分離して明記する。不確実性を消して見かけの合格を作らない。ICH Q9(R1)は不確実性、重要度、複雑性が形式性を左右するとし、NIST AI RMFはライフサイクルを通じた継続的な測定・管理を求める。[ICH Q9(R1)](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)／[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

### 4. 厳格さはリスクに比例する

低リスクの確認に高リスク案件と同じ形式・工数を要求せず、高リスク、重要な判断、複雑または不確実な対象には、より強いEvidence、独立確認、明確なOwner裁定を要求する。ただし比例性は品質要求や必須規制要件を引き下げる理由ではない。ICH Q9(R1)は努力・形式性・文書化をリスクに見合うものとしつつ、許容できない実務を正当化するために使ってはならないと明記する。FDA CSAも自動化への信頼をリスクベースで確立し、追加の厳格さが必要な箇所を特定する。[ICH Q9(R1)](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)／[FDA Computer Software Assurance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/computer-software-assurance-production-and-quality-management-system-software)

### 5. 修正提出でなく有効性確認で完了する

`fix-submitted`は、修正案・修正物が提出された事実にすぎない。完了は、元の要求またはFindingが解消されたことを、対象範囲に適切な再確認・再試験・レビューEvidenceで検証し、必要なら残余リスクをOwnerが裁定した後に成立する。ISO 9001のPDCA（Plan-Do-Check-Act）とICH Q10の状態管理・継続的改善に対応する。[ISO 9001 プロセスアプローチ](https://www.iso.org/files/live/sites/isoorg/files/archive/pdf/en/iso9001_2015_process_approach.pdf)／[ICH Q10](https://database.ich.org/sites/default/files/Q10_Guideline.pdf)

### 6. handoffは受領確認まで閉じる

送信、受領、内容理解、必要な応答または確認を記録し、受け手が不明確なままケースを閉じない。AHRQ TeamSTEPPSのCheck-Backは、受信者が受領・理解を言い返し、送信者が正確さを確認する閉ループ通信である。本QMSでは、handoffの案件ID／revision／対象成果物を照合し、受領者の確認または明示的な差戻しを完了条件とする。[AHRQ TeamSTEPPS Check-Back](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/checkback.html)

### 7. 人の誤りはsystemで無害化する

入力漏れ、取り違え、見落とし、誤解は、個人の能力不足を責めて終わらせず、UI、必須項目、role firewall、確認、再現可能な履歴、エスカレーションで検出・封じ込める。FDA Human Factorsは意図された利用者・用途・環境における使用エラーと危害を減らす設計を重視し、WHOは安全を個人の行為だけでなく医療システム全体の改善として扱う。[FDA Human Factors](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices)／[WHO Patient Safety](https://www.who.int/news-room/fact-sheets/detail/patient-safety)

### 8. AIは助言・実行・検証を担うが最終リスクを引き受けない

AIは、要求整理、リスク候補、修正、テスト、Evidence整理を担える。しかし、権限・適用範囲・評価基準を越えて承認したり、自己の出力だけで検証を完結したりしない。Ownerが品質基準と残余リスクを裁定し、AIの関与範囲・制約・不確実性・検証者を記録する。NIST AI RMFのGovern／Map／Measure／Manageと、経営・組織の説明責任に対応する。[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)／[ICH Q9(R1)](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)

## 用語と判定の最低限の境界

- `evidence-gap`: 必要なEvidenceの種類または範囲が不足しており、判定を確定できない状態。
- `unverified`: 実装・主張・結果が存在していても、要求に対する適切な検証をまだ実施または確認できない状態。
- `failed`: 要求、受入条件、または検証手順に対して不適合がEvidenceで確認された状態。単なる未確認とは分ける。
- `fix-submitted`: 修正提出のイベント。完了、受入、または有効性確認を意味しない。

Evidenceは、文書が多いことではなく、完全性、正確性、適時性、原データとの関係、変更履歴、利用目的への適合性によって評価する。MHRAのデータ完全性の考え方は、データガバナンスをライフサイクル全体の管理対象とするものであり、書類の量を増やすこと自体を品質とはしない。[MHRA GxP Data Integrity](https://www.gov.uk/government/publications/guidance-on-gxp-data-integrity)

## 誤解しやすい・今後学ぶべき論点

### 規格準拠と設計参考の違い

一次資料から思想や設計上の示唆を学ぶことと、その規格・法域・用途への適合を判定することは別である。本書は設計参考であり、全規格への準拠を意味しない。

### 比例性と品質要求引下げの違い

比例性は、リスクに合わせて確認の形式、深さ、記録量を調整すること。最低限の要求、Ownerが定めた受入基準、適用される規制要件を緩めることではない。[ICH Q9(R1)](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)

### `fix-submitted`と有効性確認の違い

提出は入力、確認は検証、完了は検証結果に基づく状態である。修正者の自己申告だけで元のFindingを閉じない。

### `Evidence gap`／`unverified`／`failed`の違い

不足は`evidence-gap`、検証未完了は`unverified`、不適合の確認は`failed`である。ラベルを混ぜると、追加取得すべきEvidenceと修正すべき不適合が見えなくなる。

### 独立性と別モデル利用の違い

独立性は、同じ主張を同じ前提のまま再出力することではなく、評価者が対象・要求・Evidenceを批判的に再確認できる状態である。別モデルを使うことは独立性を補助し得るが、それだけで独立性や正しさは証明されない。

### 閉ループhandoff

送った記録だけではhandoffは閉じない。受領者の内容確認と送信者の訂正・承認、または明示的な差戻しまでを追跡する。[AHRQ TeamSTEPPS Check-Back](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/checkback.html)

### human errorとsystem accountability

人の誤りを前提にしても、個人へ責任を押し付けることはしない。原因となった設計、権限、情報、手順、環境、検出可能性をsystemの説明責任として調べる。[FDA Human Factors](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices)／[WHO Patient Safety](https://www.who.int/news-room/fact-sheets/detail/patient-safety)

### data integrityと文書量

完全性は、記録の量ではなく、信頼できるデータが意図した目的に対して維持され、変更・出所・時点を説明できることにある。リスクに無関係な帳票を増やすことは、かえって重要なEvidenceを埋没させる。[MHRA GxP Data Integrity](https://www.gov.uk/government/publications/guidance-on-gxp-data-integrity)

## 本QMSへ今採用するもの

- Ownerが品質基準、リスク許容、残余リスクを裁定する役割境界。
- 要求、Finding、Evidence、判定、状態遷移を相互にtraceする記録。
- `evidence-gap`、`unverified`、`failed`、`fix-submitted`を混同しない判定語彙。
- リスク、重要度、複雑性、不確実性に応じた確認の比例性。
- 修正提出と有効性確認を分離し、確認Evidenceが揃うまで完了させないライフサイクル。
- handoffの受領・理解・応答を要求する閉ループ通信。
- role firewall、必須入力、案件ID／revision照合、再確認、エスカレーションによる誤操作の無害化。
- AIの助言・実行・検証を許可範囲内で使い、最終裁定と残余リスクを人間Ownerへ戻すこと。
- 小さな運用をPDCAで見直し、Evidenceの質と検出可能性を改善すること。[ISO 9001 プロセスアプローチ](https://www.iso.org/files/live/sites/isoorg/files/archive/pdf/en/iso9001_2015_process_approach.pdf)／[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

## 初期版へ持ち込まないもの

初期版は、上記の判断境界と閉ループを実装可能な最小契約として扱い、次を本Referenceからの自動実行要件にはしない。

- 規格本文の大量転記、条項の網羅的な再現、または全規格準拠宣言。
- ICH Q10のCAPA、変更管理、経営レビュー等を含む全機能の実装。
- 電子署名、規制当局向け記録、法域別の保存・承認制度。
- 医薬品・医療機器・GLP/GCP/GMP/GDP等の規制別validationや適合性判定。
- 組織横断の品質ダッシュボード、KPI基盤、統計的工程管理の全面展開。
- AIモデルの認証、モデル性能の一律閾値、別モデル利用だけを独立性の証明とする仕組み。

これらは必要性、対象法域、利用目的、Ownerの決定、追加Evidenceを確認した後に別途設計する。比例性を理由に必須要件を省略するのではなく、初期版の対象外として明示的に管理する。

## Skillからの読込条件

`quality-review`または`quality-response` Skillは、次の場合に限り本書の該当節を読む。

1. 品質基準、受入基準、残余リスク、Owner裁定の意味を解釈するとき。
2. リスク、重要度、複雑性、不確実性に応じて確認の厳格さを決めるとき。
3. Evidenceを`evidence-gap`／`unverified`／`failed`として分類し、判定のtraceを確認するとき。
4. `fix-submitted`から有効性確認・完了へ進める条件を判断するとき。
5. handoffの送信、受領、理解、応答、差戻しを閉ループとして確認するとき。
6. 人的誤操作、取り違え、見落とし、権限越境をsystem制御で無害化するとき。
7. AIの助言・実行・検証の範囲と、人間Ownerへ戻す最終裁定を確認するとき。

通常の状態遷移、既に定義済みのstatus表示、単純なCase／Findingの読み書き、機械的なJSON検証では本書を読まない。読込後も、本書だけを根拠に受入、適合、リリース、配備を宣言しない。

## 参照した一次資料

以下は本書の思想対応付けに使用した公式一次資料・公式機関資料である。要約のみを記載し、全文引用は行っていない。

- [ICH Q10 Pharmaceutical Quality System](https://database.ich.org/sites/default/files/Q10_Guideline.pdf)
- [ICH Q9(R1) Quality Risk Management](<https://database.ich.org/sites/default/files/ICH_Q9(R1)_Guideline_Step4_2025_0115.pdf>)
- [ISO 9001:2015 The Process Approach](https://www.iso.org/files/live/sites/isoorg/files/archive/pdf/en/iso9001_2015_process_approach.pdf)
- [FDA Computer Software Assurance for Production and Quality Management System Software](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/computer-software-assurance-production-and-quality-management-system-software)
- [FDA Applying Human Factors and Usability Engineering to Medical Devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices)
- [AHRQ TeamSTEPPS Check-Back（Repeat-Back）](https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/checkback.html)
- [WHO Patient Safety](https://www.who.int/news-room/fact-sheets/detail/patient-safety)
- [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- [MHRA Guidance on GxP Data Integrity](https://www.gov.uk/government/publications/guidance-on-gxp-data-integrity)

## 未確認事項

- 本QMSの正式な品質Owner、代理Owner、エスカレーション権限、許容可能な残余リスクの数値または分類は、一次資料からは決められないため未確認である。
- 本QMSの個別の規制法域、製品分類、保存期間、電子記録・電子署名要件、validation方針は未確認である。
- 実装済みSkillが本書の読込条件、role firewall、Evidence判定、有効性確認、handoff受領確認を満たすかは、本Artifact作成時点では検証していない。
- AIモデルの性能、runtime経路、実データに対する安全性、独立QAの実行結果は、本書の一次資料調査では確認していない。
- 一次資料の改訂・撤回・法域ごとの採用状況は変化し得るため、実運用または規制判断の前に各公式サイトの最新版と適用法域を再確認する必要がある。
