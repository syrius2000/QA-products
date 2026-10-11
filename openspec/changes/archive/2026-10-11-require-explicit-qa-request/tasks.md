# タスク

## 1. 明示依頼条件と評価例

- [x] 1.1 `quality-loop/skills/`の4つの`SKILL.md` descriptionを更新し、明示的な実行依頼を共通条件として記載する。Skillごとの適用範囲、必要な正例・負例、案件・Role・操作条件を保ったことを仕様deltaと照合する。
- [x] 1.2 既存3 Skillの`evals/evals.json`に明示依頼の正例と非発火の負例を追加し、`blind-qa-cycle`にも評価データを作成する。4ファイルすべてがJSONとして読み込め、各Skillに正例・負例があることを確認する。
- [x] 1.3 `quality-loop/tests/test_skill_contracts.py`に4 Skillのdescriptionと評価データの起動条件を検査するテストを追加し、対象テストを実行して通過を確認する。

## 2. 統合確認

- [x] 2.1 正例・負例の代表会話をdescriptionと評価データに照らして確認した。実行環境にSkill選択結果を観測する機能がないため、自動選択の実行時確認はできず、静的な起動条件・評価例の整合性確認までとする。
- [x] 2.2 `openspec validate require-explicit-qa-request --strict`と`git diff --check`を実行し、両方成功した。今回の差分は4つの正本Skill定義、評価データ、対象テスト、OpenSpec文書に限られ、runtime・CLI・ルート`.agents/skills/`・外部配置には及んでいない。作業開始時から存在する別Changeの差分は保持した。
