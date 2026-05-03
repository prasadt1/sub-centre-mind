#!/usr/bin/env python3
"""
Aggregate JSONL audit events and emit a draft monthly-style summary for ANM review.

Does not submit to HMIS — human-in-the-loop only. Use synthetic / de-identified logs in demos.

  python scripts/report_from_logs.py
  python scripts/report_from_logs.py --log data/logs/my_events.jsonl --json-out /tmp/summary.json
  python scripts/report_from_logs.py --llm   # optional Ollama narrative (requires local Ollama)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from audit.report import aggregate, llm_narrative, template_summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Draft summary from audit JSONL")
    ap.add_argument(
        "--log",
        type=Path,
        default=Path(os.environ.get("SCM_AUDIT_LOG", "data/logs/sample_events.jsonl")),
    )
    ap.add_argument("--json-out", type=Path, default=None, help="Write aggregate stats JSON")
    ap.add_argument(
        "--llm",
        action="store_true",
        help="Append Gemma narrative via Ollama /api/generate",
    )
    ap.add_argument("--model", default=os.environ.get("SCM_MODEL", "gemma4:latest"))
    args = ap.parse_args()

    if not args.log.is_file():
        print(f"Log file not found: {args.log}", file=sys.stderr)
        sys.exit(2)

    stats = aggregate(args.log)
    text = template_summary(stats)

    if args.json_out:
        args.json_out.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(text)

    if args.llm:
        print("\n--- LLM narrative (optional) ---\n")
        try:
            print(llm_narrative(stats, model=args.model))
        except Exception as e:
            print(f"(LLM skipped: {e})", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
