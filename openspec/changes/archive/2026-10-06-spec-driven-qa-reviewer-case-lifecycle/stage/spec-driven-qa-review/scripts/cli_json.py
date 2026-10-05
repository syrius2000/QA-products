"""構造化CLI JSONの共通出力。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .secret_guard import sanitize


def case_id_from_path(path: Path) -> str | None:
    match = re.search(r"QA-[0-9]{4,}", path.name)
    return match.group(0) if match else None


def emit(*, ok: bool, status: str, path: Path, next_action: str, errors: list[str]) -> None:
    print(json.dumps(sanitize({
        "schema_version": "qa-cli-v1.2",
        "contract_version": "1.2",
        "ok": ok,
        "status": status,
        "case_id": case_id_from_path(path),
        "next_action": next_action,
        "errors": errors,
    }), ensure_ascii=False, sort_keys=True))
