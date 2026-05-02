from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import requests

from .query import RetrievedChunk, format_citations, retrieve


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    citations: str
    retrieved: List[RetrievedChunk]


def _build_prompt(user_query: str, chunks: Sequence[RetrievedChunk]) -> str:
    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        context_blocks.append(f"[{i}] Source: {c.source_file} page {c.page}\n{c.text}")
    context = "\n\n".join(context_blocks) if context_blocks else "(no sources retrieved)"

    return (
        "You are Sub-Centre Mind, a clinical protocol assistant for ANMs.\n"
        "Rules:\n"
        "- Do NOT diagnose.\n"
        "- Do NOT prescribe medications.\n"
        "- If the question is diagnostic/prescriptive, refuse and recommend escalation.\n"
        "- If you answer, you MUST ground the response in the provided sources.\n"
        "- Keep the answer brief (3-6 bullet points).\n\n"
        f"User question: {user_query}\n\n"
        f"Sources:\n{context}\n\n"
        "Answer now.\n"
    )


def generate_answer(
    user_query: str,
    *,
    index_dir: Path,
    model: str = "gemma4:latest",
    think: bool = False,
    top_k: int = 5,
    num_predict: int = 220,
    temperature: float = 0.1,
) -> RAGAnswer:
    retrieved = retrieve(user_query, index_dir=index_dir, top_k=top_k)
    prompt = _build_prompt(user_query, retrieved)

    payload = {
        "model": model,
        "prompt": prompt,
        "think": think,
        "stream": False,
        "options": {"num_predict": num_predict, "temperature": temperature},
    }

    resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    return RAGAnswer(
        answer=(data.get("response") or "").strip(),
        citations=format_citations(retrieved),
        retrieved=list(retrieved),
    )


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get("SCM_QUERY", "IFA tablet dose for pregnant women per MoHFW guidelines?")
    out = generate_answer(q, index_dir=index_dir)
    print(out.answer)
    print("\nCitations:\n" + out.citations)


if __name__ == "__main__":
    main()

