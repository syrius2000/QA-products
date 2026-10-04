"""採番、原文保持、排他、状態の原子的保存。"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo


class QAError(ValueError):
    def __init__(self, message: str, action: str = "入力と対象を確認して再実行してください"):
        super().__init__(message)
        self.action = action


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fingerprint(value) -> str:
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def now() -> str:
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M (JST)")


def header(title: str, author: str, created: str | None = None) -> str:
    if not author.strip() or "\n" in author:
        raise QAError("実際の担当ツールとモデル名を指定してください")
    return f"# {title}\n\ncreated: {created or now()}\nupdate: {now()}\nauthor: {author}\n\n"


def relative(value: str) -> str:
    p = PurePosixPath(value)
    if not value or p.is_absolute() or any(x in value for x in ["\\", "\0", "\n", "\r"]) or ".." in p.parts or str(p) != value or value.startswith("-") or value == ".":
        raise QAError(f"安全なリポジトリ相対パスではありません: {value}")
    if p.parts[0] == ".git":
        raise QAError("Git管理領域は対象にできません")
    return value


def safe_path(root: Path, value: str) -> Path:
    relative(value)
    p = root / value
    if not p.resolve().is_relative_to(root.resolve()):
        raise QAError(f"リポジトリ外を指すパスです: {value}")
    for q in [p, *p.parents]:
        if q == root:
            break
        if q.is_symlink():
            raise QAError(f"保存先にシンボリックリンクがあります: {value}")
    return p


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".qa-write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Store:
    def __init__(self, root: Path, git_dir: Path):
        self.root = root
        self.artifacts = root / "docs/Artifacts"
        self.lock = git_dir / "qa-workflow.lock"

    @contextmanager
    def transaction(self):
        # 状況確認はこの操作を呼ばない。採番も全依頼共通の排他対象。
        with self.lock.open("a+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def states(self) -> list[dict]:
        result = []
        for p in sorted(self.artifacts.glob("qa_state_*.json")):
            result.append(self.read(p.relative_to(self.root).as_posix()))
        return result

    def read(self, path: str) -> dict:
        try:
            s = json.loads(safe_path(self.root, path).read_bytes())
        except (OSError, json.JSONDecodeError) as e:
            raise QAError(f"状態ファイルを読めません: {path}: {e}") from e
        self.validate(s)
        if s["state_path"] != path:
            raise QAError("状態パスと内容が一致しません")
        return s

    def select(self, request: str | None = None) -> dict:
        states = self.states()
        if request:
            states = [s for s in states if s["id"] == request or s["state_path"] == request]
        else:
            states = [s for s in states if not s.get("superseded") and not s.get("decision")]
        if len(states) != 1:
            raise QAError(f"依頼を一つ選んでください: {[s['id'] for s in states]}", "対象の依頼IDを指定してください")
        return states[0]

    def allocate(self, slug: str, extension: str = "md", extra=()) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", slug):
            raise QAError("Artifactスラッグが不正です")
        names = [p.name for p in self.artifacts.glob(f"{slug}_*.*")]
        for state in self.states():
            names.extend(Path(p).name for p in state["operational"])
        names.extend(Path(p).name for p in extra)
        numbers = [int(m.group(1)) for name in names if (m := re.fullmatch(rf"{re.escape(slug)}_(\d{{3}})_\d{{4}}\.[a-z]+", name))]
        number = max(numbers, default=0) + 1
        if number > 999:
            raise QAError("Artifact採番が999を超えました")
        day = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%m%d")
        return f"docs/Artifacts/{slug}_{number:03d}_{day}.{extension}"

    def preserve(self, path: str, raw: bytes) -> str:
        p = safe_path(self.root, path)
        if p.exists():
            if p.read_bytes() != raw:
                raise QAError(f"同名別内容のため保存を停止しました: {path}", "訂正依頼で予約した新しいレビュー保存先を使ってください")
        else:
            atomic(p, raw)
        return digest(raw)

    @staticmethod
    def validate(s: dict) -> None:
        required = {"schema", "id", "cycle", "revision", "state_path", "repository", "branch", "initial_baseline", "baseline", "reviewed", "purpose", "criteria", "assumptions", "requirements_hash", "products", "operational", "excluded", "snapshot", "phase", "audience", "implementer", "invite", "review_path", "reviews", "active_review", "pending_correction", "unresolved", "events", "author"}
        if not isinstance(s, dict) or required - s.keys() or s.get("schema") != "unified-qa-workflow-v1":
            raise QAError("状態契約が不正です")
        if type(s["revision"]) is not int or s["revision"] < 1 or type(s["cycle"]) is not int or s["cycle"] < 1:
            raise QAError("状態revisionまたはサイクルが不正です")
        if s["audience"] not in {"local", "cloud"} or s["phase"] not in {"draft", "prepared", "published", "waiting", "invalid", "content_pending", "reviewed", "planned", "approved", "submitted", "decision"}:
            raise QAError("状態または宛先が不正です")
        for k in ["initial_baseline", "baseline", "reviewed"]:
            if not (k == "reviewed" and s[k] is None) and not re.fullmatch(r"[0-9a-f]{40}", str(s[k])):
                raise QAError(f"完全なSHAがありません: {k}")
        if not s["purpose"].strip() or not s["criteria"] or fingerprint([s["purpose"], s["assumptions"], s["criteria"]]) != s["requirements_hash"]:
            raise QAError("固定要件または要件指紋が不正です")
        for k in ["products", "operational", "excluded"]:
            if not isinstance(s[k], dict):
                raise QAError(f"パス集合が不正です: {k}")
            for p in s[k]:
                relative(p)
        for k in ["state_path", "invite", "review_path"]:
            relative(s[k])
        if s["active_review"] is not None and not any(r["hash"] == s["active_review"] and r.get("content_checked") and not r["issues"] for r in s["reviews"]):
            raise QAError("有効レビューの確認記録がありません")
        checks = s.get("checks", [])
        if not isinstance(checks, list):
            raise QAError("実行検証契約が配列ではありません")
        ids = set()
        for check in checks:
            if not isinstance(check, dict) or not re.fullmatch(r"CHECK-[A-Z0-9_-]+", str(check.get("id", ""))) or check["id"] in ids:
                raise QAError("実行check IDが不正または重複しています")
            ids.add(check["id"])
            if check.get("type") not in {"command", "python-version"}:
                raise QAError(f"実行checkの種類が不正です: {check['id']}")
            if check["type"] == "python-version" and not re.fullmatch(r"\d+\.\d+", str(check.get("python_minimum", ""))):
                raise QAError(f"Python version checkに最低versionが必要です: {check['id']}")
            if check["type"] == "command" and "python_minimum" in check:
                raise QAError(f"通常commandにPython専用条件は指定できません: {check['id']}")
            if type(check.get("required")) is not bool or not isinstance(check.get("argv"), list) or not check["argv"] or not all(isinstance(x, str) and x and "\0" not in x for x in check["argv"]):
                raise QAError(f"実行checkの必須性またはargvが不正です: {check['id']}")
            cwd = check.get("cwd", ".")
            if cwd != ".": relative(cwd)
            if not isinstance(check.get("env", {}), dict) or not all(re.fullmatch(r"[A-Z_][A-Z0-9_]*", k) and not re.search(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|PRIVATE_KEY|AUTH", k) and isinstance(v, str) for k, v in check.get("env", {}).items()):
                raise QAError(f"実行checkの環境変数が不正です: {check['id']}")
            if type(check.get("timeout_seconds")) is not int or not 1 <= check["timeout_seconds"] <= 3600:
                raise QAError(f"実行check timeoutが不正です: {check['id']}")
            if not isinstance(check.get("expected_exit_codes", [0]), list) or not check.get("expected_exit_codes", [0]) or not all(type(x) is int for x in check.get("expected_exit_codes", [0])):
                raise QAError(f"実行checkの期待終了コードが不正です: {check['id']}")

    def save(self, s: dict, expected: int | None = None, event: str = "作成") -> None:
        self.validate(s)
        p = safe_path(self.root, s["state_path"])
        if expected is not None:
            current = self.read(s["state_path"])
            if current["revision"] != expected:
                raise QAError("状態が他の操作で更新されています", "最新状況を読み直してください")
            s["revision"] = expected + 1
        elif p.exists():
            raise QAError("既存状態を上書きできません")
        s["events"].append({"at": now(), "event": event, "revision": s["revision"]})
        atomic(p, (json.dumps(s, ensure_ascii=False, indent=2) + "\n").encode())
