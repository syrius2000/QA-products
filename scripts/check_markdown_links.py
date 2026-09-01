#!/usr/bin/env python3
"""Markdown内のリポジトリ相対リンクを検査する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted(set(files))


def target_path(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(None, 1)[0]
    return unquote(target.split("#", 1)[0])


def is_external(target: str) -> bool:
    lowered = target.lower()
    return (
        not target
        or target.startswith("#")
        or lowered.startswith(("http://", "https://", "mailto:", "data:", "//"))
        or target.startswith("/")
    )


def broken_links(path: Path, root: Path) -> list[tuple[int, str, Path]]:
    errors: list[tuple[int, str, Path]] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_PATTERN.finditer(line):
            raw = match.group(1)
            target = target_path(raw)
            if is_external(target):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append((number, target, resolved))
                continue
            if not resolved.exists():
                errors.append((number, target, resolved))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors: list[tuple[Path, int, str, Path]] = []
    for path in markdown_files([item.resolve() for item in args.paths]):
        errors.extend((path, number, target, resolved) for number, target, resolved in broken_links(path, root))
    if errors:
        for path, number, target, resolved in errors:
            print(f"{path}:{number}: リンク切れ: {target} -> {resolved}")
        return 1
    print(f"Markdown相対リンク検査OK: {len(markdown_files([item.resolve() for item in args.paths]))}ファイル")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
