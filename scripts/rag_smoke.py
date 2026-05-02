#!/usr/bin/env python3

import os
from pathlib import Path

from src.rag.generate import generate_answer


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get(
        "SCM_QUERY",
        "What is the recommended IFA supplementation schedule in pregnancy? Answer in 4 bullets.",
    )
    out = generate_answer(q, index_dir=index_dir, num_predict=180, temperature=0.1)
    print(out.answer)
    print("\nCitations:\n" + out.citations)


if __name__ == "__main__":
    main()

