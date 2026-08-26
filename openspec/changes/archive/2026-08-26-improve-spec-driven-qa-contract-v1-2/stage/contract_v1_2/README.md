# Contract v1.2 stage構成

created: 2026-08-25 21:19 (JST)
update: 2026-08-25 21:19 (JST)
author: Codex (GPT-5)

## 所有境界

- `qa_cases/`: Reviewerが所有するQA正本。`review.md`、`findings.yaml`、`traceability.yaml`、`events.jsonl`などを保持する。
- `qa_cases/<case_id>/handoff.md`: Reviewer正本から生成するAuthor向け公開契約。Authorは直接編集しない。
- `author_submissions/<case_id>/<submission_id>/`: Authorが許可範囲内で追記する提出物。QA正本ではなく、Reviewerの統合Validatorが検証する。
- `reviewer/`: Reviewer Skill固有namespaceのstage実装。
- `author_response/`: Author Response Skill固有namespaceのstage実装。

## Manifest

stage Bundleの対象は、次の2つの固有namespaceとContract用ディレクトリである。

```text
spec_driven_qa_reviewer/
spec_driven_qa_author_response/
contract_v1_2/qa_cases/
contract_v1_2/author_submissions/
```

各Skillの元ファイル一覧は、それぞれのnamespace直下の`MANIFEST.txt`を正本とする。stage BundleのManifestには、次を含めない。

- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- 実データ、認証情報、外部システムの状態

## 変更権限

- Reviewer正本とhandoffの生成・更新: Reviewer側だけが担当する。
- Author提出物の作成: Author側が新規`submission_id`単位で担当する。
- Reviewer正本への統合: Reviewer側の統合Validatorだけが担当する。
- グローバル`~/.agents/skills/`への配備: このChangeの対象外。別途明示承認が必要。
