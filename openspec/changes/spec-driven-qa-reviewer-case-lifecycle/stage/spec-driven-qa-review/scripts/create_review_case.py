#!/usr/bin/env python3
"""ReviewerLifecycle.init_case を呼び出す薄い CLI ラッパー。"""
import argparse
import json
import sys
from pathlib import Path

from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def main():
    parser = argparse.ArgumentParser(description="Create review case (Thin wrapper)")
    parser.add_argument("case_id")
    parser.add_argument("--target", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--profile", default="standard")
    parser.add_argument("--title", default="QA Review Case")
    parser.add_argument("--qa-root", default="docs/ADR/QA")
    args = parser.parse_args()

    lifecycle = ReviewerLifecycle(qa_root=args.qa_root, role="reviewer")
    res = lifecycle.init_case(
        case_id=args.case_id,
        target=args.target,
        purpose=args.purpose,
        profile=args.profile,
        title=args.title,
    )
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
