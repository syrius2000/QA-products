"""negative fixtureを共有コアへ通し、役割逸脱を集計する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent / "spec-driven-qa-bundle"
sys.path.insert(0, str(ROOT))
from shared_core.authorization import allowed  # noqa: E402
from shared_core.compat import normalize_contract_version  # noqa: E402
from shared_core.guards import validate_handoff  # noqa: E402
from shared_core.secrets import safe_diagnostic  # noqa: E402


def evaluate(fixture: dict) -> dict:
    results = []
    current = {"case_revision": 2, "semantic_digest": "new", "content_digest": "new-content", "case_status": "needs-response"}
    for case in fixture["cases"]:
        ident = case["id"]
        value = case["input"]
        if ident == "stale-digest":
            passed = "semantic_digest_stale_or_tampered" in validate_handoff({"case_revision": 2, "expected_semantic_digest": value["expected_semantic_digest"], "expected_content_digest": "new-content"}, current)
        elif ident == "revision-conflict":
            passed = "revision_conflict" in validate_handoff({"case_revision": value["case_revision"], "expected_semantic_digest": "new", "expected_content_digest": "new-content"}, current)
        elif ident in {"author-direct-review-write", "author-self-close"}:
            passed = not allowed(value["role"], "close" if ident == "author-self-close" else "review")
        elif ident == "unknown-major":
            try:
                normalize_contract_version(value["contract_version"])
                passed = False
            except ValueError:
                passed = True
        elif ident == "secret-output":
            passed = "token=REDACTED" not in json.dumps(safe_diagnostic("secret", value["diagnostic"]))
        else:
            passed = False
        results.append({"id": ident, "passed": passed})
    return {"status": "ok" if all(item["passed"] for item in results) else "failed", "results": results, "violations": [item["id"] for item in results if not item["passed"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(__file__).resolve().parent.parent / "fixtures/negative/negative-cases.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "violations": len(report["violations"])}, ensure_ascii=False))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
