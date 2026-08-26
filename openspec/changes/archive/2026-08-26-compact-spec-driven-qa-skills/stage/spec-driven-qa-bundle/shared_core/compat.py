"""旧CLI入力を共有コアの比較可能な契約へ読み取り変換する。"""

from typing import Any

from .authorization import allowed

SUPPORTED_CONTRACTS = {"v1.0", "v1.1", "v1.2"}


def normalize_contract_version(value: str | None) -> str:
    version = value or "v1.2"
    if version in {"1.0", "1.1", "1.2"}:
        version = "v" + version
    if version not in SUPPORTED_CONTRACTS:
        raise ValueError("unknown_contract_major")
    return version


def invoke_legacy(role: str, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    version = normalize_contract_version(payload.get("contract_version"))
    if not allowed(role, operation):
        return {"exit_code": 2, "contract": version, "state": "unchanged", "side_effects": [], "status": "rejected"}
    state = payload.get("state", payload.get("case_status", "unchanged"))
    side_effects = payload.get("side_effects", [])
    if not isinstance(side_effects, list):
        return {"exit_code": 2, "contract": version, "state": "unchanged", "side_effects": [], "status": "rejected"}
    return {"exit_code": 0, "contract": version, "state": state, "side_effects": side_effects, "status": "ok", "role": role, "operation": operation}
