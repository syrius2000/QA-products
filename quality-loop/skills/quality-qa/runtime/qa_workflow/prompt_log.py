"""利用者の発言ログ（hookが記録）に承認文が含まれるかを確認する。"""
from __future__ import annotations

import json
from pathlib import Path


def verbatim_in_log(log: Path, message: str) -> bool:
    needle = message.strip()
    if not needle or not log.is_file():
        return False
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            prompt = json.loads(line).get("prompt")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(prompt, str) and needle in prompt:
            return True
    return False
