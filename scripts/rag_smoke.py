#!/usr/bin/env python3

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from rag.generate import generate_answer


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get(
        "SCM_QUERY",
        "What is the recommended IFA supplementation schedule in pregnancy? Answer in 4 bullets.",
    )
    out = generate_answer(q, index_dir=index_dir, num_predict=180, temperature=0.1)
    if out.confidence_blocked:
        print(
            "confidence_gate: blocked (top semantic_score below SCM_RETRIEVAL_MIN_SIM; Ollama skipped)",
            file=sys.stderr,
        )
    print(out.answer)
    print("\nCitations:\n" + out.citations)


if __name__ == "__main__":
    main()

