"""stage BundleのManifest、JSON Schema、全fixtureを必須ゲートとして検証する。"""

from __future__ import annotations

import json
from pathlib import Path

from run_evals import run_evals


FORBIDDEN_PARTS = {".pytest_cache", "__pycache__"}


def validate_bundle(stage: Path) -> list[str]:
    errors: list[str] = []
    for path in stage.rglob("*"):
        if not path.is_file():
            continue
        if any(part in FORBIDDEN_PARTS for part in path.parts) or path.suffix == ".pyc":
            errors.append(f"forbidden cache or bytecode: {path.relative_to(stage)}")
    for schema in stage.rglob("*.schema.json"):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"invalid JSON Schema: {schema}: {error}")
    required = [stage / "manifest_v1_2.txt", stage / "spec_driven_qa_reviewer", stage / "spec_driven_qa_author_response", stage / "contract_v1_2"]
    errors.extend(f"missing Bundle path: {path}" for path in required if not path.exists())
    evaluation = run_evals(stage)
    if not evaluation["ok"]:
        errors.append("run_evals.py did not pass")
    return errors
