#!/usr/bin/env python3
"""
RAG end-to-end smoke: retrieve → confidence gate → optional Ollama /api/generate.

Prints structured gate metadata on stdout (Phase C — wire confidence_blocked for CLI/scripts).
"""

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

from rag.generate import DEFAULT_MIN_SIM, generate_answer


def _env_gate_on() -> bool:
    return os.environ.get("SCM_CONFIDENCE_GATE", "1").strip().lower() not in ("0", "false", "no")


def _env_min_sim() -> float:
    return float(os.environ.get("SCM_RETRIEVAL_MIN_SIM", str(DEFAULT_MIN_SIM)))


def _print_meta(out, *, min_sim: float, gate_on: bool) -> None:
    best = out.retrieved[0].semantic_score if out.retrieved else 0.0
    ollama_skipped = out.confidence_blocked
    print("--- RAG smoke ---")
    print(f"confidence_blocked: {out.confidence_blocked}")
    print(f"top_semantic_score: {best:.6f}")
    print(f"SCM_CONFIDENCE_GATE: {int(gate_on)}")
    print(f"SCM_RETRIEVAL_MIN_SIM: {min_sim}")
    print(f"ollama_skipped: {ollama_skipped}")
    print("---")


def main() -> None:
    default_q = (
        "What is the recommended IFA supplementation schedule in pregnancy? Answer in 4 bullets."
    )
    parser = argparse.ArgumentParser(
        description="Run generate_answer with optional query; prints gate metadata then answer.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Question (defaults to SCM_QUERY or built-in IFA prompt)",
    )
    parser.add_argument(
        "--index-dir",
        default=os.environ.get("SCM_INDEX_DIR", "data/index"),
        help="Index directory (default: data/index or SCM_INDEX_DIR)",
    )
    parser.add_argument(
        "--meta-only",
        action="store_true",
        help="Print only the --- RAG smoke --- metadata block (no answer body)",
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Do not print metadata block (legacy behavior: answer + citations only)",
    )
    parser.add_argument(
        "--exit-on-block",
        action="store_true",
        help="Exit with code 2 when the confidence gate blocks (optional CI hook)",
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=None,
        help="Override Ollama num_predict (else uses SCM_NUM_PREDICT or 220)",
    )
    args = parser.parse_args()

    q = (args.query or os.environ.get("SCM_QUERY") or default_q).strip()
    index_dir = Path(args.index_dir)

    gate_on = _env_gate_on()
    min_sim = _env_min_sim()

    out = generate_answer(
        q,
        index_dir=index_dir,
        num_predict=args.num_predict,
        temperature=0.1,
    )

    audit_log = os.environ.get("SCM_AUDIT_LOG")
    if audit_log:
        from audit.schema import append_event, new_event
        from rag.lang import detect_language

        best = out.retrieved[0].semantic_score if out.retrieved else 0.0
        query_lang = detect_language(q)
        if out.confidence_blocked:
            append_event(
                Path(audit_log),
                new_event(
                    "confidence_gate_blocked",
                    top_sim=best,
                    query_preview=q[:160],
                    query_lang=query_lang,
                ),
            )
        else:
            append_event(
                Path(audit_log),
                new_event(
                    "rag_answer",
                    top_sim=best,
                    confidence_blocked=False,
                    query_preview=q[:160],
                    query_lang=query_lang,
                ),
            )

    if out.confidence_blocked and not args.no_meta:
        print(
            "confidence_gate: blocked (top semantic_score below SCM_RETRIEVAL_MIN_SIM; Ollama skipped)",
            file=sys.stderr,
        )

    if not args.no_meta:
        _print_meta(out, min_sim=min_sim, gate_on=gate_on)

    if not args.meta_only:
        print(out.answer)
        print("\nCitations:\n" + out.citations)

    if args.exit_on_block and out.confidence_blocked:
        sys.exit(2)


if __name__ == "__main__":
    main()
