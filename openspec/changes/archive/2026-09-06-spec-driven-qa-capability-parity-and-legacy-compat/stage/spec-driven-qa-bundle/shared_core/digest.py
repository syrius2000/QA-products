"""契約対象データの決定論的digest。"""

import hashlib
import json
from typing import Any


def content_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
