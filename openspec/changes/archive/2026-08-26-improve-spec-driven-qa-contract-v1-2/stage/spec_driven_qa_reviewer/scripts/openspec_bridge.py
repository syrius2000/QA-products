"""指定OpenSpec ChangeとGitの読み取り専用baselineを収集する。"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def _run(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.PIPE).strip()


def collect_baseline(repo: Path, change_name: str) -> dict[str, Any]:
    status_raw = _run(["openspec", "status", "--change", change_name, "--json"], repo)
    status = json.loads(status_raw)
    revision = _run(["git", "rev-parse", "HEAD"], repo)
    diff = subprocess.check_output(["git", "diff", "--binary"], cwd=repo, stderr=subprocess.PIPE)
    diff_digest = hashlib.sha256(diff).hexdigest()
    return {
        "change_name": change_name,
        "change_root": status.get("changeRoot"),
        "git_revision": revision,
        "working_tree_digest": diff_digest,
        "evidence_policy": {
            "openspec_task_status_is_implementation_evidence": False,
            "openspec_valid_true_is_implementation_evidence": False,
        },
    }
