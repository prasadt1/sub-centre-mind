#!/usr/bin/env python3
"""Unified ask: retrieval + Ollama chat + Gate 1 tools (see src/query_router.py)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from query_router import format_orchestrator_print, orchestrate_query


def main() -> None:
    p = argparse.ArgumentParser(description="Sub-Centre Mind — one-shot query with RAG + tools")
    p.add_argument("query", nargs="?", default=os.environ.get("SCM_QUERY", ""), help="User question")
    p.add_argument(
        "--index-dir",
        default=os.environ.get("SCM_INDEX_DIR", "data/index"),
        help="FAISS index directory",
    )
    p.add_argument("--model", default=os.environ.get("SCM_MODEL"), help="Ollama model tag")
    args = p.parse_args()
    q = (args.query or "").strip()
    if not q:
        p.error("Provide a query argument or set SCM_QUERY")

    index_dir = Path(args.index_dir)
    if not index_dir.is_dir():
        print(f"Index directory not found: {index_dir}", file=sys.stderr)
        sys.exit(2)

    r = orchestrate_query(q, index_dir=index_dir, model=args.model)
    print(format_orchestrator_print(r))
    if not r.tool_name:
        sys.exit(1)


if __name__ == "__main__":
    main()
