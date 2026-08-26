#!/usr/bin/env python3
"""ReviewerLifecycle.close_case を呼び出す薄い CLI ラッパー。"""
import argparse
import json
import sys
from pathlib import Path

from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def main():
    parser = argparse.ArgumentParser(description="Close review case (Thin wrapper)")
    parser.add_argument("case_id")
    parser.add_argument("--terminal-status", default="accepted")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--qa-root", default="docs/ADR/QA")
    args = parser.parse_args()

    lifecycle = ReviewerLifecycle(qa_root=args.qa_root, role="reviewer")
    res = lifecycle.close_case(
        case_id=args.case_id,
        terminal_status=args.terminal_status,
        rationale=args.rationale,
    )
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
