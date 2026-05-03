from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

_SRC_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = str(_SRC_ROOT)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from llm import GenerateOptions, get_backend
from rag.gate import should_skip_generation
from rag.intent import SupplementIntent, detect_supplement_intent
from rag.lang import expand_query_for_retrieval, normalise_asr_transcript
from rag.query import RetrievedChunk, format_citations, retrieve


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    citations: str
    retrieved: List[RetrievedChunk]
    confidence_blocked: bool = False


DEFAULT_MIN_SIM = 0.7


def _low_confidence_answer() -> str:
    return (
        "No sufficiently confident match was found in the indexed guidelines for this question. "
        "Do not guess clinical actions from weak retrieval. "
        "Escalate to the Medical Officer or follow your facility’s protocol."
    )


def _build_prompt(user_query: str, chunks: Sequence[RetrievedChunk]) -> str:
    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        context_blocks.append(f"[{i}] Source: {c.source_file} page {c.page}\n{c.text}")
    context = "\n\n".join(context_blocks) if context_blocks else "(no sources retrieved)"

    intent = detect_supplement_intent(user_query)
    focus = ""
    if intent == SupplementIntent.IRON_IFA:
        focus = (
            "Focus: iron / IFA supplementation. Prefer passages that mention IFA, iron, or ferrous; "
            "do not substitute calcium-only guidance unless the user asked about calcium.\n\n"
        )
    elif intent == SupplementIntent.CALCIUM:
        focus = (
            "Focus: calcium supplementation. Prefer passages that mention calcium; "
            "do not substitute IFA-only guidance unless the question spans both.\n\n"
        )
    elif intent == SupplementIntent.FOLIC_ACID:
        focus = (
            "Focus: folic acid (early pregnancy). Prefer passages about folic acid / first trimester.\n\n"
        )

    return (
        "You are Sub-Centre Mind, a clinical protocol assistant for ANMs.\n"
        "Rules:\n"
        "- Do NOT diagnose.\n"
        "- Do NOT prescribe medications.\n"
        "- If the question is diagnostic/prescriptive, refuse and recommend escalation.\n"
        "- If you answer, you MUST ground the response in the provided sources.\n"
        "- Keep the answer brief (3-6 bullet points).\n\n"
        f"{focus}"
        f"User question: {user_query}\n\n"
        f"Sources:\n{context}\n\n"
        "Answer now.\n"
    )


DEFAULT_NUM_PREDICT = 220


def generate_answer(
    user_query: str,
    *,
    index_dir: Path,
    model: str = "gemma4:latest",
    think: bool = False,
    top_k: int = 5,
    num_predict: int | None = None,
    temperature: float = 0.1,
) -> RAGAnswer:
    if num_predict is None:
        num_predict = int(os.environ.get("SCM_NUM_PREDICT", str(DEFAULT_NUM_PREDICT)))
    retrieval_q = expand_query_for_retrieval(normalise_asr_transcript(user_query))
    retrieved = retrieve(retrieval_q, index_dir=index_dir, top_k=top_k)

    gate_on = os.environ.get("SCM_CONFIDENCE_GATE", "1").strip().lower() not in ("0", "false", "no")
    min_sim = float(os.environ.get("SCM_RETRIEVAL_MIN_SIM", str(DEFAULT_MIN_SIM)))
    if should_skip_generation(retrieved, gate_on=gate_on, min_sim=min_sim):
        return RAGAnswer(
            answer=_low_confidence_answer(),
            citations="(generation skipped: top semantic similarity below threshold)",
            retrieved=list(retrieved),
            confidence_blocked=True,
        )

    prompt = _build_prompt(user_query, retrieved)

    timeout_s = float(os.environ.get("SCM_OLLAMA_TIMEOUT", "180"))
    backend = get_backend()
    answer_text = backend.generate(
        prompt,
        model=model,
        options=GenerateOptions(
            num_predict=num_predict,
            temperature=temperature,
            think=think,
        ),
        timeout=timeout_s,
    )

    return RAGAnswer(
        answer=answer_text,
        citations=format_citations(retrieved),
        retrieved=list(retrieved),
        confidence_blocked=False,
    )


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get("SCM_QUERY", "IFA tablet dose for pregnant women per MoHFW guidelines?")
    out = generate_answer(q, index_dir=index_dir)
    if out.confidence_blocked:
        print(
            "confidence_gate: blocked (top semantic_score below SCM_RETRIEVAL_MIN_SIM; Ollama skipped)",
            file=sys.stderr,
        )
    print(out.answer)
    print("\nCitations:\n" + out.citations)


if __name__ == "__main__":
    main()

