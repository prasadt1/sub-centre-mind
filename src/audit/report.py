"""Aggregation + draft summary helpers for the audit JSONL log.

Pure functions (no Streamlit / no CLI) so they can be reused from the script
and the Streamlit app.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .schema import iter_events


def aggregate(path: Path) -> dict[str, Any]:
    """Compute headline counters from an audit JSONL file."""
    kinds: Counter[str] = Counter()
    langs: Counter[str] = Counter()
    sims: list[float] = []
    blocked = 0
    for ev in iter_events(path):
        kinds[ev.kind] += 1
        if ev.kind == "confidence_gate_blocked":
            blocked += 1
        if ev.detail.get("query_lang"):
            langs[str(ev.detail["query_lang"])] += 1
        ts = ev.detail.get("top_sim")
        if isinstance(ts, (int, float)):
            sims.append(float(ts))
    return {
        "source_log": str(path),
        "total_events": sum(kinds.values()),
        "by_kind": dict(kinds),
        "confidence_gate_blocked_count": blocked,
        "queries_by_language": dict(langs),
        "top_sim_samples_count": len(sims),
        "top_sim_avg": round(sum(sims) / len(sims), 4) if sims else None,
    }


def template_summary(stats: dict[str, Any]) -> str:
    """Plain-text supervisor draft (no LLM call)."""
    lines = [
        "Draft — Sub-Centre activity summary (for supervisor review; not an HMIS submission)",
        "",
        f"Events recorded: {stats['total_events']}",
        f"By type: {json.dumps(stats['by_kind'], ensure_ascii=False)}",
        f"Confidence gate blocked (no LLM call): {stats['confidence_gate_blocked_count']}",
        f"Queries by language code: {json.dumps(stats['queries_by_language'], ensure_ascii=False)}",
    ]
    if stats.get("top_sim_avg") is not None:
        lines.append(f"Average top retrieval similarity (where logged): {stats['top_sim_avg']}")
    lines.extend(
        [
            "",
            "Notes:",
            "- Link each narrative claim to event_id in the JSONL source.",
            "- Replace synthetic refs before any operational use.",
        ]
    )
    return "\n".join(lines)


def llm_narrative(stats: dict[str, Any], *, model: str, timeout: float = 120.0) -> str:
    """Optional Gemma narrative over the aggregate stats."""
    import requests  # local import keeps this module import-light for tests

    prompt = (
        "You are drafting an internal monthly summary for a rural sub-centre in India.\n"
        "Use ONLY the statistics below. Do not invent patient counts or diagnoses.\n"
        "Output 4 short bullet points + one line disclaimer that this is not an official HMIS report.\n\n"
        f"Statistics JSON:\n{json.dumps(stats, indent=2)}\n"
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "think": False,
        "stream": False,
        "options": {"num_predict": 220, "temperature": 0.2},
    }
    r = requests.post(
        os.environ.get("OLLAMA_GENERATE_URL", "http://localhost:11434/api/generate"),
        json=payload,
        timeout=timeout,
    )
    r.raise_for_status()
    return (r.json().get("response") or "").strip()
