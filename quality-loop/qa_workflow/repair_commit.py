"""承認済みの修正パスだけを、承認文の範囲内でcommitする。"""
from __future__ import annotations

from pathlib import Path

from . import gitops
from .store import QAError, relative

COMMIT_PHRASE = "修正後のcommitまで"


def commit_approved_paths(root: Path, approved_paths: list[str], message: str, approval_text: str) -> str:
    if COMMIT_PHRASE not in approval_text:
        raise QAError("承認文に修正後のcommitの範囲が含まれていません", "承認文に「修正後のcommitまで」を含めて再承認してください")
    paths = [relative(path) for path in approved_paths]
    already_staged = set(gitops.git(root, "diff", "--cached", "--name-only").splitlines())
    if already_staged & set(paths):
        raise QAError("承認パスに他者のステージ済み変更があります", "ステージを外すか内容を確認してから再実行してください")
    gitops.git(root, "add", "--", *paths)
    gitops.git(root, "commit", "-m", message, "--", *paths)
    return gitops.sha(root, "HEAD")
