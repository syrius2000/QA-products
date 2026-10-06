# Tasks

## 1. 実装境界と現行契約の確認

- [x] 1.1 正本Skill、旧`.agents`配置、参照資料、Ignore/追跡状態を一覧化し、差分を判別できないローカル配置はPlan 039の承認ゲートへ隔離する。検証: [実装前調査記録](implementation-record.md)に対象パス、Git状態、内容差分、配置移行の停止条件を記録した。
- [x] 1.2 招待、レビュー4成果物、machine schema、local/cloud Git帰着、再QAの現行契約を新ライフサイクル仕様と照合する。検証: [実装前調査記録](implementation-record.md)に新旧の契約項目対応表を作り、保持・変更・追加項目に仕様/設計上の根拠を付けた。

## 2. blind-qa-cycleの統一

- [x] 2.1 `quality-loop/skills/blind-qa-cycle/`のSkill本文を実装前`prepare`、事後開始、レビュー、Finding対応、再QA、終結の順に整理し、quality QA系3 Skillへのルーティング境界を記載する。検証: Skill内の入口表とフローから全モード・停止条件・次担当を追跡できる。
- [x] 2.2 `00_plan.md`と最終invite、local/cloud、output contract、machine schema、Git運用referenceを統一ライフサイクルに合わせて更新する。検証: 計画commitがBaselineになりレビューdiffから準備成果物を除外でき、明示した新branch開始時のpost-change Baseline、招待必須項目・レビュー結果条件・相対リンクが整合する。
- [ ] 2.3 旧`.agents/skills/blind-qa-cycle/`を正本へ案内する互換shimへ移行し、旧本文の二重正本を解消する。Plan 039の承認後に限りbackup、dry-run、配置、対象限定rollbackを行う。検証: 配置結果が承認済みdry-runと一致し、shimから正本Skillへ到達でき、旧ルールと矛盾する実行指示が残っていない。承認前または作業前に既存利用者変更が見つかった場合は変更を止める。

## 3. Human Understanding Note支援

- [x] 3.1 `/blind-qa-cycle note`モードを追加し、QA成果物からcycle ID、Repository/branch、Baseline/Reviewed SHA、最終Gateだけを参照情報として取得する。検証: 完全なcycleでは各値が一致し、不足/不整合時はNoteを生成せず不足を表示する。
- [x] 3.2 cycle DIRに`04_human_understanding.md`を新規作成する記入支援を実装する。6つの指定質問を提示し、チャット回答は逐語保存し、空テンプレート作成も選べるようにする。検証: 各設問が存在し、AI補完・要約・採点なしで回答が保存され、5分程度の目安が表示される。
- [x] 3.3 Noteの既存ファイル保護とQA Gateとの分離をSkill・成果物契約へ反映する。検証: 既存Noteを上書きせず、未理解/空欄を記録でき、Gate・Finding状態・Owner裁定が変化しない。

## 4. サイクル境界と統合確認

- [x] 4.1 監査ブランチ終結時にFinding処置、残余リスク、最終Gate、SHA、Note保存先を対応づける手順を記載する。検証: サイクル完了チェックから終結状態が確認でき、main/master merge・配備が自動経路にない。
- [x] 4.2 specの各Scenarioに対してlocal/cloud、新branch開始前/事後開始、SHA欠落、修正再QA、Note新規/既存/未理解、別QA Skillルーティングを机上検証する。検証: 各Scenarioの期待結果と実装箇所を記録し、未対応Scenarioがない。
- [x] 4.3 OpenSpec成果物、Skill相対リンク、変更パスを最終確認する。検証: `openspec validate --strict unify-blind-qa-cycle`が成功し、差分に`quality-qa`、`quality-review`、`quality-response`、既存QA cycle記録、製品コードの変更が含まれない。
