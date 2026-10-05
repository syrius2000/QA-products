"""構造化入出力と終了コードの共有定義。"""

import json
from typing import Any

EXIT_OK = 0
EXIT_REJECTED = 2


def encode_result(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
