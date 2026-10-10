"""公開前の機密情報検査と、再QA前の祖先関係確認。"""
from __future__ import annotations

from pathlib import Path

from . import gitops
from .store import QAError


def assert_publishable(root: Path, paths: list[str]) -> None:
    findings = gitops.publication_findings(root, set(paths))
    if findings:
        raise QAError("公開対象に機密情報または個人ローカルパスの疑いがあります", "検出: " + ", ".join(findings))


def assert_reachable_from_origin(root: Path, branch: str, shas: list[str]) -> None:
    ref = f"refs/remotes/origin/{branch}"
    for sha in shas:
        if not gitops.ancestor(root, sha, ref):
            raise QAError("対象commitが origin/<branch> の祖先ではありません", "pushの成功を確認してから再QAを依頼してください")
