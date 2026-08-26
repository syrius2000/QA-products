from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_revision(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "review"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_simple_frontmatter(text: str) -> dict[str, str]:
    """Parse only simple top-level YAML scalar fields used by validator.

    This intentionally avoids a PyYAML runtime dependency. It is not a general YAML parser.
    """
    if not text.startswith("---\n"):
        return {}
    try:
        _, block, _ = text.split("---\n", 2)
    except ValueError:
        return {}
    result: dict[str, str] = {}
    for line in block.splitlines():
        if not line or line.startswith(" ") or line.startswith("\t") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def extract_frontmatter_scalar(text: str, key: str, default: str = "") -> str:
    """Extract a scalar from simple frontmatter, including one-level nested keys."""
    meta = parse_simple_frontmatter(text)
    if key in meta:
        return meta[key]
    pattern = rf"(?m)^\s+{re.escape(key)}:\s*([^\n]+)$"
    block = text
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            block = parts[1]
    match = re.search(pattern, block)
    if not match:
        return default
    return match.group(1).strip().strip('"').strip("'")


def redact_sensitive(value: str) -> str:
    """Prevent common credential-shaped values from entering derived handoffs."""
    value = re.sub(r"(?i)(token|password|secret|api[_-]?key)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", value)
    value = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", value)
    value = re.sub(r"(?i)\b(sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{8,})\b", "[REDACTED]", value)
    return value


def parse_findings_summary(path: Path) -> list[dict[str, str]]:
    """Parse predictable finding scalars without introducing a runtime YAML dependency."""
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    nested: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        match = re.match(r"^\s*- id:\s*(.+)$", line)
        if match:
            if current:
                rows.append(current)
            current = {"id": match.group(1).strip().strip('"').strip("'")}
            nested = None
            continue
        if current is None:
            continue
        scalar = re.match(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if scalar:
            key, value = scalar.groups()
            value = value.strip().strip('"').strip("'")
            if value in {"null", "~"}:
                value = ""
            current[key] = value
            nested = key if value == "" else None
            continue
        evidence = re.match(r"^\s{8}- type:\s*(.+)$", line)
        if evidence:
            current.setdefault("evidence_type", evidence.group(1).strip().strip('"').strip("'"))
            nested = "evidence"
            continue
        reference = re.match(r"^\s{8}reference:\s*(.+)$", line)
        if reference and nested == "evidence":
            current.setdefault("evidence_reference", reference.group(1).strip().strip('"').strip("'"))
    if current:
        rows.append(current)
    return rows


def next_case_number(qa_root: Path) -> int:
    mx = 0
    if qa_root.exists():
        for p in qa_root.iterdir():
            m = re.match(r"QA-(\d+)-", p.name)
            if m:
                mx = max(mx, int(m.group(1)))
    return mx + 1
