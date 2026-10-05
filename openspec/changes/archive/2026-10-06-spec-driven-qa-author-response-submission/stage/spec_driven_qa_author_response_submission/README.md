# Author提出Stage

Reviewerの公開handoffを入力として、Author回答と修正提出を構造化し、Reviewer検証へ返却するStage実装である。

## 実行

```bash
python -m spec_driven_qa_author_response_submission.launcher handoff.md submission.json --workspace .
```

終了コード0はReviewer検証待ち、2は提出拒否を示す。Reviewer正本はこのCLIから変更しない。
