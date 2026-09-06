"""リポジトリ内相対リンクと外部参照の境界を検証する。"""

from pathlib import PurePosixPath


def validate_link(value: str) -> bool:
    if value.startswith("file://") or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def classify_link(value: str) -> str:
    if value.startswith("file://") or not value:
        return "rejected"
    if value.startswith(("https://", "http://")):
        return "external"
    return "relative" if validate_link(value) else "rejected"
