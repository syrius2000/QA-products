"""ghで版を固定し、指定Markdownだけを取得する。"""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
from urllib.parse import quote
from .store import QAError, relative, now


class GitHub:
    def __init__(self, executable: str | None = None):
        self.executable = executable or shutil.which("gh")
        if not self.executable:
            raise QAError("ghがありません", "設定済みghとGitHub認証を確認してください")

    def run(self, *args) -> dict:
        r = subprocess.run([self.executable, *args], capture_output=True)
        if r.returncode:
            raise QAError("GitHubの取得に失敗: " + r.stderr.decode(errors="replace").strip(), "認証と取得元を確認してください。結果は未取得です")
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError as e:
            raise QAError("GitHub応答を解釈できません") from e

    def acquire(self, repository: str, path: str, branch: str | None = None, pr: str | None = None) -> tuple[bytes, dict]:
        relative(path)
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
            raise QAError("リポジトリ識別が不正です")
        if pr:
            if not re.fullmatch(r"https://github\.com/" + re.escape(repository) + r"/pull/\d+", pr):
                raise QAError("PRのリポジトリが元依頼と一致しません")
            info = self.run("pr", "view", pr, "--json", "headRefOid,headRefName,headRepository,headRepositoryOwner")
            commit = info["headRefOid"]; branch = info["headRefName"]
            owner = (info.get("headRepositoryOwner") or {}).get("login")
            name = (info.get("headRepository") or {}).get("name")
            source_repo = f"{owner}/{name}" if owner and name else repository
        else:
            source_repo = repository
            info = self.run("api", f"repos/{repository}/commits/{quote(branch or '', safe='')}")
            commit = info["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise QAError("取得元commitを固定できません")
        info = self.run("api", f"repos/{source_repo}/contents/{quote(path, safe='/')}?ref={commit}")
        if not isinstance(info, dict) or info.get("type") != "file" or info.get("path") != path or info.get("encoding") != "base64" or info.get("target"):
            raise QAError("指定された通常Markdownを取得できません")
        try:
            raw = base64.b64decode("".join(info["content"].split()), validate=True)
        except (ValueError, KeyError) as e:
            raise QAError("レビュー本文を復号できません") from e
        return raw, {"kind": "pr" if pr else "branch", "repository": source_repo, "branch": branch, "pr": pr, "commit": commit, "path": path, "acquired": now()}
