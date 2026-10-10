"""Git対象固定と許可集合だけのcommit・topic公開。"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from .store import QAError, digest, relative


def git(root: Path, *args: str, env=None, check=True) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=env)
    if check and r.returncode:
        raise QAError(r.stderr.decode(errors="replace").strip() or "Git操作に失敗しました")
    return r.stdout.decode("utf-8", errors="strict").strip()


def git_bytes(root: Path, *args: str, env=None) -> bytes:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=env)
    if r.returncode:
        raise QAError(r.stderr.decode(errors="replace").strip() or "Git読取りに失敗しました")
    return r.stdout


def root_for(path: Path) -> Path:
    return Path(git(path, "rev-parse", "--show-toplevel")).resolve()


def git_directory(root: Path) -> Path:
    p = Path(git(root, "rev-parse", "--git-dir"))
    return (root / p).resolve() if not p.is_absolute() else p


def sha(root: Path, ref: str) -> str:
    if not ref or ref.startswith("-") or any(c in ref for c in ["\n", "\0"]):
        raise QAError("対象版を指定してください")
    value = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise QAError("完全なcommit SHAを取得できません")
    return value


def ancestor(root: Path, a: str, b: str) -> bool:
    r = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", a, b], capture_output=True)
    if r.returncode not in {0, 1}:
        raise QAError("commitの祖先関係を確認できません")
    return r.returncode == 0


def default_branch(root: Path) -> str:
    ref = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD", check=False)
    if ref:
        return ref.removeprefix("refs/remotes/origin/")
    names = [name for name in ["main", "master"] if git(root, "rev-parse", "--verify", f"refs/heads/{name}", check=False)]
    if len(names) == 1:
        return names[0]
    raise QAError("既定ブランチを取得できません", "origin/HEADの設定または既定ブランチの明示が必要です")


def repository(root: Path, explicit: str | None = None) -> str:
    remote = git(root, "remote", "get-url", "origin", check=False)
    m = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?$", remote)
    if m:
        value = m.group(1)
        if explicit and explicit != value:
            raise QAError("指定リポジトリとoriginが一致しません")
        return value
    if explicit and re.fullmatch(r"[\w.-]+/[\w.-]+", explicit):
        return explicit
    raise QAError("GitHubリポジトリを取得できません", "owner/repositoryを指定してください")


def baseline(root: Path, explicit: str | None = None) -> str:
    if explicit:
        return sha(root, explicit)
    branch = default_branch(root)
    ref = f"refs/remotes/origin/{branch}"
    if not git(root, "rev-parse", "--verify", ref, check=False):
        ref = f"refs/heads/{branch}"
    return sha(root, git(root, "merge-base", "HEAD", ref))


def changed(root: Path, a: str, b: str) -> set[str]:
    tokens = git_bytes(root, "diff", "--name-status", "-z", "--find-renames", a, b).split(b"\0")
    result = set(); i = 0
    while i < len(tokens) and tokens[i]:
        status = tokens[i].decode(); i += 1
        count = 2 if status[0] in "RC" else 1
        for _ in range(count):
            result.add(tokens[i].decode()); i += 1
    return result


def dirty(root: Path) -> set[str]:
    result = set()
    for args in [("diff", "--name-only", "-z", "HEAD"), ("ls-files", "--others", "--exclude-standard", "-z")]:
        result.update(x.decode() for x in git_bytes(root, *args).split(b"\0") if x)
    return result


def status_preflight(path: Path) -> dict:
    """Read-only Git inventory used before QA preparation or implementation."""
    root = root_for(path)
    branch = git(root, "branch", "--show-current") or None
    head = sha(root, "HEAD")
    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False) or None
    default = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD", check=False)
    default = default.removeprefix("refs/remotes/origin/") if default else None
    staged = sorted(x.decode() for x in git_bytes(root, "diff", "--cached", "--name-only", "-z").split(b"\0") if x)
    unstaged = sorted(x.decode() for x in git_bytes(root, "diff", "--name-only", "-z").split(b"\0") if x)
    untracked = sorted(x.decode() for x in git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if x)
    remotes = git(root, "remote", check=False).splitlines()
    summary = {}
    for name, args in {
        "staged": ("diff", "--cached", "--stat", "--no-renames"),
        "unstaged": ("diff", "--stat", "--no-renames"),
    }.items():
        summary[name] = git(root, *args, check=False) or "差分なし"
    clean = not (staged or unstaged or untracked)
    return {
        "repository_root": str(root), "branch": branch, "head": head,
        "upstream": upstream, "default_branch": default, "remotes": remotes,
        "staged": staged, "unstaged": unstaged, "untracked": untracked,
        "diff_summary": summary, "clean": clean,
        "safe_to_implement": bool(clean and branch and default and branch != default),
        "next": "実装可能。作業中も既存差分を保持してください" if clean and branch and default and branch != default else "差分・branch・基準点を分類し、明示判断を得るまで状態を変更しないでください",
    }


def snapshot(root: Path, paths) -> dict:
    values = {}
    for name in sorted(paths):
        relative(name)
        p = root / name
        # 製品symlinkはリンク文字列だけを読み、外部実体を読まない。
        for parent in p.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise QAError(f"対象の親がシンボリックリンクです: {name}")
        if p.is_symlink():
            values[name] = {"mode": "120000", "hash": digest(os.readlink(p).encode())}
        elif p.is_file():
            values[name] = {"mode": "100755" if p.stat().st_mode & 0o111 else "100644", "hash": digest(p.read_bytes())}
        elif not p.exists():
            values[name] = None
        else:
            raise QAError(f"ファイル単位で対象を指定してください: {name}")
    return values


def tree_snapshot(root: Path, commit: str, paths) -> dict:
    result = {}
    for name in sorted(paths):
        relative(name)
        line = git(root, "ls-tree", commit, "--", name)
        if not line:
            result[name] = None
            continue
        mode, kind, rest = line.split(" ", 2)
        blob, _ = rest.split("\t", 1)
        if kind != "blob":
            raise QAError(f"対象commitの通常ファイルではありません: {name}")
        result[name] = {"mode": mode, "hash": digest(git_bytes(root, "cat-file", "blob", blob))}
    return result


_SECRET_ASSIGNMENT = re.compile(r"(?i)\b(?:[a-z0-9_]*(?:token|secret|password|passwd)|api[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]{4,})")
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
# 検査自身のソースが検出されないよう、パスの接頭辞は連結して書く。
_PERSONAL_PATH = re.compile(r"(?:/Us" r"ers/|/ho" r"me/)([^/\s]+)(?:/|$)")
_SAFE_FIXTURE_VALUES = {"example", "dummy", "placeholder", "redacted", "test-token", "qa-user", "your-token"}


def _scan_text(name: str, text: str) -> list[str]:
    findings = []
    if _PRIVATE_KEY.search(text):
        findings.append(f"{name}:private-key")
    for match in _SECRET_ASSIGNMENT.finditer(text):
        value = match.group(1).strip(" ,;)")
        if value.lower() not in _SAFE_FIXTURE_VALUES and not (value.startswith("<") and value.endswith(">")):
            findings.append(f"{name}:secret-like-assignment")
            break
    for match in _PERSONAL_PATH.finditer(text):
        if match.group(1).lower() not in {"example", "test", "qa-user", "username"}:
            findings.append(f"{name}:personal-local-path")
            break
    return findings


def publication_findings(root: Path, paths: set[str]) -> list[str]:
    """Scan only bytes that are about to be published; synthetic test identities are explicit exceptions."""
    findings = []
    for name in sorted(paths):
        current = snapshot(root, [name])[name]
        if current is None:
            continue
        path = root / name
        if path.is_symlink():
            content = os.readlink(path).encode()
        else:
            content = path.read_bytes()
        findings.extend(_scan_text(name, content.decode("utf-8", errors="ignore")))
    return findings


_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def outgoing_findings(root: Path, base: str, head: str = "HEAD") -> list[str]:
    """Scan, commit by commit, the bytes each outgoing commit adds or changes.

    The net diff of base..head hides a secret that a middle commit adds and a later commit removes,
    yet the secret still travels in the pushed history.
    """
    findings: list[str] = []
    scanned: set[tuple[str, str]] = set()
    for commit in git(root, "rev-list", "--reverse", f"{base}..{head}").splitlines():
        parents = git(root, "rev-list", "--parents", "-n", "1", commit).split()[1:]
        for name in sorted(changed(root, parents[0] if parents else _EMPTY_TREE, commit)):
            blob = tree_snapshot(root, commit, [name])[name]
            if blob is None or (name, blob["hash"]) in scanned:
                continue
            scanned.add((name, blob["hash"]))
            content = git_bytes(root, "cat-file", "blob", f"{commit}:{name}")
            findings.extend(_scan_text(name, content.decode("utf-8", errors="ignore")))
    return list(dict.fromkeys(findings))


def execute_checks(root: Path, checks: list[dict]) -> list[dict]:
    """Run the structured argv contracts without a shell and return compact, hash-backed evidence."""
    results = []
    for check in checks:
        cwd_name = check.get("cwd", ".")
        candidate = root / cwd_name
        cursor = candidate
        while cursor != root:
            if cursor.is_symlink():
                raise QAError(f"check cwdがsymlinkです: {check['id']}")
            cursor = cursor.parent
        cwd = candidate.resolve()
        if cwd != root.resolve() and root.resolve() not in cwd.parents:
            raise QAError(f"check cwdがリポジトリ外です: {check['id']}")
        if not cwd.is_dir():
            raise QAError(f"check cwdが利用できません: {check['id']}")
        env = os.environ.copy()
        env.update(check.get("env", {}))
        env["PYTHONDONTWRITEBYTECODE"] = env.get("PYTHONDONTWRITEBYTECODE", "1")
        started = time.monotonic()
        try:
            proc = subprocess.run(check["argv"], cwd=cwd, env=env, capture_output=True, timeout=check["timeout_seconds"], shell=False)
            stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
            runtime = f"Python {os.sys.version.split()[0]}" if check["type"] == "python-version" else f"{check['argv'][0]} (exit {code})"
            passed = code in check.get("expected_exit_codes", [0])
            if check["type"] == "python-version":
                match = re.search(rb"Python\s+(\d+)\.(\d+)", stdout + b"\n" + stderr)
                passed = passed and bool(match and tuple(map(int, match.groups())) >= tuple(map(int, check["python_minimum"].split("."))))
                runtime = (stdout + stderr).decode(errors="replace").strip()[:200] or runtime
            status = "PASS" if passed else "FAIL"
            reason = None
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
            runtime, status, reason = check["argv"][0], "ERROR", f"timeout after {check['timeout_seconds']} seconds"
        except OSError as exc:
            stdout, stderr, code = b"", str(exc).encode(), None
            runtime, status, reason = check["argv"][0], "ERROR", f"command unavailable: {type(exc).__name__}"
        results.append({
            "id": check["id"], "status": status, "exit_code": code,
            "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
            "duration_ms": int((time.monotonic() - started) * 1000), "runtime": runtime,
            "reason": reason,
        })
    return results


def classify(root: Path, initial: str, base: str, target: str, products: dict, operations: dict, excluded: dict) -> dict:
    overlap = set(products) & (set(operations) | set(excluded))
    if overlap:
        raise QAError(f"製品と運用／対象外の分類が重複しています: {sorted(overlap)}")
    result = {}
    for label, a in [("initial", initial), ("delta", base)]:
        paths = changed(root, a, target)
        unknown = paths - set(products) - set(operations) - set(excluded)
        if unknown:
            raise QAError(f"差分の未分類パスがあります: {sorted(unknown)}", "製品対象に追加するか、対象外とする理由を記録してください")
        result[label] = {"product": sorted(paths & set(products)), "operational": sorted(paths & set(operations)), "excluded": {p: excluded[p] for p in sorted(paths & set(excluded))}}
    return result


def commit_paths(root: Path, paths, expected: dict, message: str) -> str:
    paths = sorted(paths)
    if snapshot(root, paths) != expected:
        raise QAError("表示済み対象から内容が変わりました", "対象を再表示し、再承認してください")
    staged = set(x.decode() for x in git_bytes(root, "diff", "--cached", "--name-only", "-z").split(b"\0") if x)
    if staged & set(paths):
        raise QAError(f"対象に既存ステージ内容があります: {sorted(staged & set(paths))}", "対象indexの扱いをユーザーに確認してください")
    active = sorted(set(paths) & dirty(root))
    if not active:
        commit = sha(root, "HEAD")
        if tree_snapshot(root, commit, paths) != expected:
            raise QAError("既存commitと下書きの内容が一致しません")
        return commit
    # 別indexでcommitし、対象外のステージ内容を保持する。
    with tempfile.TemporaryDirectory(prefix="quality-qa-index-") as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp)/"index"))
        git(root, "read-tree", "HEAD", env=env)
        git(root, "add", "--", *active, env=env)
        git(root, "commit", "-m", message, env=env)
    commit = sha(root, "HEAD")
    for p in active:
        line = git(root, "ls-tree", commit, "--", p)
        if line:
            mode, _, blob_path = line.split(" ", 2)
            blob = blob_path.split("\t", 1)[0]
            git(root, "update-index", "--add", "--cacheinfo", mode, blob, p)
        else:
            git(root, "update-index", "--force-remove", "--", p)
    if tree_snapshot(root, commit, paths) != expected or snapshot(root, paths) != expected:
        raise QAError("commit後の対象が下書きと一致しません")
    return commit


def remote_tip(root: Path, branch: str) -> str | None:
    data = git(root, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if not data:
        return None
    value = data.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise QAError("remote tipを確認できません")
    git(root, "fetch", "--no-tags", "origin", value)
    return sha(root, value)


def preflight(root: Path, state: dict, allowed: set[str]) -> dict:
    branch = git(root, "branch", "--show-current")
    if branch != state["branch"] or branch in {"main", "master", default_branch(root)}:
        raise QAError("選択された開発ブランチでだけ公開できます")
    if not git(root, "remote", "get-url", "origin", check=False):
        raise QAError("公開先originがありません")
    tip = remote_tip(root, branch)
    head = sha(root, "HEAD")
    if tip and tip != head and ancestor(root, head, tip):
        ahead = changed(root, head, tip)
        all_reviews = state.get("history_reviews", []) + state["reviews"]
        permitted = {state["review_path"]} | {r["path"] for r in all_reviews}
        if state.get("pending_correction"):
            permitted.add(state["pending_correction"]["review_path"])
        if not ahead <= permitted or git(root, "diff", "--cached", "--name-only"):
            raise QAError("remote先行分を既存差分を保持して更新できません")
        collisions = dirty(root) & ahead
        registered = {r["path"]: r["hash"] for r in all_reviews}
        if collisions:
            local = snapshot(root, collisions)
            remote = tree_snapshot(root, tip, collisions)
            if local != remote or any(not local[p] or local[p]["hash"] != registered.get(p) for p in collisions):
                raise QAError("remoteのレビューとローカル原文が一致しません")
            # 取得・保持済みの同一原文だけをindexへ登録してFF可能にする。
            # ユーザーの未知ファイル、異なる原文、既存indexは上書きしない。
            for p in sorted(collisions):
                line = git(root, "ls-tree", tip, "--", p)
                mode, _, blob_path = line.split(" ", 2)
                blob = blob_path.split("\t", 1)[0]
                git(root, "update-index", "--add", "--cacheinfo", mode, blob, p)
        # 成果物だけと確認できた場合に限定したfast-forward。
        git(root, "merge", "--ff-only", tip)
        head = sha(root, "HEAD")
    if tip and not ancestor(root, tip, head):
        raise QAError("remoteが分岐しています", "履歴の安全な統合を別途判断してください")
    start = tip or remote_tip(root, default_branch(root))
    if not start:
        raise QAError("公開履歴の基準remote commitがありません")
    if not ancestor(root, start, head):
        raise QAError("既定remoteと開発履歴の祖先関係が不明です")
    commits = git(root, "rev-list", "--reverse", f"{start}..{head}").splitlines()
    for c in commits:
        # 最終差分だけでは一度追加して削除された範囲外ファイルを見逃す。
        parents = git(root, "rev-list", "--parents", "-n", "1", c).split()[1:]
        if len(parents) != 1 or not changed(root, parents[0], c) <= allowed:
            raise QAError(f"送出履歴に未承認の変更があります: {c}", "表示した送出commitとパス集合の承認範囲を確認してください")
    return {"remote": start, "commits": commits, "allowed": sorted(allowed)}


def guarded_push(root: Path, state: dict) -> None:
    """Every push to origin goes through here: scan each outgoing commit first, and never push on a finding."""
    base = remote_tip(root, state["branch"]) or state["initial_baseline"]
    findings = outgoing_findings(root, base, "HEAD")
    if findings:
        raise QAError(
            "送出するコミットに機密情報または個人ローカルパスの疑いがあります: " + "、".join(findings),
            "原因を除いたコミットを作ってから再実行してください。pushはしていません",
        )
    git(root, "push", "origin", f"HEAD:refs/heads/{state['branch']}")


def push(root: Path, state: dict, invite_commit: str) -> str:
    guarded_push(root, state)
    tip = remote_tip(root, state["branch"])
    if not tip or not ancestor(root, state["reviewed"], tip) or not ancestor(root, invite_commit, tip):
        raise QAError("公開後の対象／依頼の到達可能性を確認できません")
    return tip
