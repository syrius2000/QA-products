#!/usr/bin/env python3
"""ReviewerLifecycle.render_handoff を呼び出す薄い CLI ラッパー。"""
import argparse
import json
import sys
from pathlib import Path

from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def main():
    parser = argparse.ArgumentParser(description="Render handoff contract (Thin wrapper)")
    parser.add_argument("case_id")
    parser.add_argument("--cycle", type=int, default=1)
    parser.add_argument("--case-revision", default="rev-001")
    parser.add_argument("--qa-root", default="docs/ADR/QA")
    args = parser.parse_args()

    lifecycle = ReviewerLifecycle(qa_root=args.qa_root, role="reviewer")
    res = lifecycle.render_handoff(
        case_id=args.case_id,
        cycle=args.cycle,
        case_revision=args.case_revision,
    )
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
