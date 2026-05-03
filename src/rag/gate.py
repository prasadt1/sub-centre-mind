"""Pure confidence-gate logic (unit-testable without loading embeddings)."""

from __future__ import annotations

from typing import Any, Sequence


def top_semantic_score(retrieved: Sequence[Any]) -> float:
    if not retrieved:
        return 0.0
    first = retrieved[0]
    return float(getattr(first, "semantic_score", 0.0))


def should_skip_generation(
    retrieved: Sequence[Any],
    *,
    gate_on: bool,
    min_sim: float,
) -> bool:
    """
    If True, caller must not invoke Ollama: weak or empty retrieval under active gate.
    """
    if not gate_on:
        return False
    if not retrieved:
        return True
    return top_semantic_score(retrieved) < min_sim
