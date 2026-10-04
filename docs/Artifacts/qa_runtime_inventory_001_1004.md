# QA runtime・既存基盤の開始時インベントリ

created: 2026-10-04 20:49 (JST)
update: 2026-10-04 20:49 (JST)
author: Codex (GPT-6)

## 対象と集計方法

計画033の実装worktreeを基準に、旧Quality Loop Core、既存2 Skillのruntime、新QA runtimeを相対パス・ファイル数・総byte数・内容manifest SHA-256で記録した。各manifest hashは、相対ファイル名、NUL、8-byte big-endian file size、file bytesをパス順に連結してSHA-256を計算した値である。実装開始時に旧正本と外部配置先への変更はなく、今回変更は新 `quality-qa` runtimeとその回帰テストに限定されている。

| 対象 | パス | ファイル数 | 総byte数 | Manifest SHA-256 |
|---|---|---:|---:|---|
| Quality Loop Core | `quality-loop/quality_loop/` | 12 | 149866 | `e133b7dfab83faead3d08070dc15de30e2b782aeb6eba33dc038ac159cf97927` |
| 既存Reviewer runtime | `quality-loop/skills/quality-review/runtime/` | 12 | 149866 | `0b8f2f656e69451c4cc7e5b631fd447822a3e871f37aa4052f2e8a0a0d82d08a` |
| 既存Author runtime | `quality-loop/skills/quality-response/runtime/` | 12 | 149866 | `0b8f2f656e69451c4cc7e5b631fd447822a3e871f37aa4052f2e8a0a0d82d08a` |
| 新QA runtime | `quality-loop/qa_workflow/` | 14 | 257998 | `3676b189cec151aecfb7df944fcb4c85353748daa469a7d582cc704f3d44330c` |

既存のunittest suiteは `quality-loop/tests/` 配下の既存入口を維持する。既存アーカイブの過去115件PASSは開始時の歴史Evidenceであり、今回の完了判定には使用しない。既存runtimeを変更せず新QA runtimeを追加する対応は、[統合QAの実装タスク](../../openspec/changes/unify-qa-skill-workflow/tasks.md)とそのテストEvidenceで追跡する。

## 新runtimeと受入領域の対応

| Runtime | 責務 | 主な受入領域 | 対応テスト・Evidence |
|---|---|---|---|
| `store.py` | 状態schema、revision、採番、排他、原文保全、atomic write | 2.1–2.3、5.2 | `test_qa_workflow_contract.py`、Store validation / stale revision / duplicate-path fixture |
| `gitops.py` | Git preflight、snapshot、path分類、限定commit・push | 3.1–3.4、4.1–4.4、7.1 | 一時git/bare remote fixture |
| `review.py` | 全基準照合、Skill hash、check Evidence、Finding/task/前回Finding整合 | 5.3–5.4、7.2 | `AcceptanceCriteriaContractTests` |
| `workflow.py` | 依頼、公開、回収、訂正、計画・承認・提出、再QA、終了判断 | 2.2、3.2–3.5、4.5、5.5、6.1–6.4、7.1–7.4 | `ExecutionContractIntegrationTests` |
| `legacy.py` | 旧4成果物の読み取り専用照合 | 8.1 | `test_legacy_four_file_import_is_read_only_and_checks_gate_consistency` |
| `github.py` | branch/PRから固定SHAのMarkdownのみ取得 | 5.1–5.2 | `GitHubAcquisitionTests` |
| `cli.py` | Skill向け内部CLIと状況表示 | 2.5、3.5、8.2 | CLI help/preflightとSkill代表操作 |

新QA runtimeは旧case engineのAPI・case正本へ接続せず、別package `qa_workflow` として実装する。既存runtimeとの同一性または非変更は開始manifest、終了時diff、回帰試験で確認する。
