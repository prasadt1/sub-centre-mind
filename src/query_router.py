"""
Single-path orchestration: hybrid retrieval + Ollama /api/chat with Gate 1 tools.

Use this for demos and judging instead of running g1_checks.sh and rag_smoke.py separately.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import requests

from rag.lang import expand_query_for_retrieval
from rag.query import RetrievedChunk, format_citations, retrieve

OLLAMA_CHAT_URL = os.environ.get("OLLAMA_CHAT_URL", "http://localhost:11434/api/chat")

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "refuse_and_escalate",
            "description": (
                "Refuse diagnostic/prescribing requests and escalate to a human Medical Officer."
            ),
            "parameters": {
                "type": "object",
                "required": ["reason", "escalation_target", "urgency", "case_summary"],
                "properties": {
                    "reason": {"type": "string"},
                    "escalation_target": {"type": "string"},
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "case_summary": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer_protocol_question",
            "description": (
                "Answer a non-diagnostic protocol question using only the guideline excerpts "
                "provided in the system message."
            ),
            "parameters": {
                "type": "object",
                "required": ["answer", "source", "confidence"],
                "properties": {
                    "answer": {"type": "string"},
                    "source": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
    },
]


def _system_instructions(*, retrieved: Sequence[RetrievedChunk], retrieval_weak: bool) -> str:
    base = (
        "You are Sub-Centre Mind, assisting ANMs at Indian sub-centres.\n"
        "You MUST respond by calling exactly one tool. Do not send a plain-text assistant reply.\n\n"
        "Use refuse_and_escalate for: diagnosis, prescribing, medication dosing, interpreting "
        "vitals/labs, danger signs, or any question that needs clinical judgment beyond printed protocols.\n"
        "Use answer_protocol_question only for protocol-only questions (IFA schedules, ANC visits, "
        "immunization schedules, counselling norms) and only when grounded in the excerpts below.\n"
    )
    if retrieval_weak:
        return (
            base
            + "\nRetrieval status: NO confident guideline match was found in the local index "
            "(similarity below threshold). Do NOT invent clinical detail. "
            "Prefer refuse_and_escalate unless the question is clearly non-clinical.\n"
        )

    blocks = []
    for i, c in enumerate(retrieved, start=1):
        blocks.append(f"[{i}] Source: {c.source_file} page {c.page}\n{c.text}")
    ctx = "\n\n".join(blocks) if blocks else "(no excerpts)"
    return base + "\nGuideline excerpts (ground truth):\n\n" + ctx


def _parse_tool_call(tc: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
    fn = tc.get("function") or {}
    name = fn.get("name")
    raw = fn.get("arguments")
    if raw is None:
        return name, {}
    if isinstance(raw, str):
        try:
            return name, json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return name, {}
    if isinstance(raw, dict):
        return name, raw
    return name, {}


@dataclass(frozen=True)
class OrchestratorResult:
    """Outcome of one orchestrated Ollama /api/chat call with tools."""

    retrieved: List[RetrievedChunk]
    top_semantic_score: float
    retrieval_weak: bool
    tool_name: Optional[str]
    tool_arguments: Dict[str, Any]
    raw_message_content: str


def orchestrate_query(
    user_query: str,
    *,
    index_dir: Path,
    model: Optional[str] = None,
    top_k: int = 5,
    think: bool = False,
    timeout: float = 120.0,
) -> OrchestratorResult:
    """
    Retrieve chunks, then call Ollama chat with Gate 1 tools (same contract as scripts/g1_checks.sh).
    """
    q = (user_query or "").strip()
    retrieval_q = expand_query_for_retrieval(q) if q else q
    retrieved = retrieve(retrieval_q, index_dir=index_dir, top_k=top_k) if q else []

    gate_on = os.environ.get("SCM_CONFIDENCE_GATE", "1").strip().lower() not in ("0", "false", "no")
    min_sim = float(os.environ.get("SCM_RETRIEVAL_MIN_SIM", "0.7"))
    best = retrieved[0].semantic_score if retrieved else 0.0
    retrieval_weak = gate_on and (not retrieved or best < min_sim)

    system_content = _system_instructions(retrieved=retrieved, retrieval_weak=retrieval_weak)
    mdl = model or os.environ.get("SCM_MODEL", "gemma4:latest")

    payload: Dict[str, Any] = {
        "model": mdl,
        "think": think,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": q or "(empty query)"},
        ],
        "tools": TOOLS,
    }

    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    msg = data.get("message") or {}
    tool_calls = msg.get("tool_calls") or []
    text = (msg.get("content") or "").strip()

    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = {}
    if tool_calls:
        tc0 = tool_calls[0]
        tool_name, tool_args = _parse_tool_call(tc0)

    return OrchestratorResult(
        retrieved=list(retrieved),
        top_semantic_score=float(best),
        retrieval_weak=retrieval_weak,
        tool_name=tool_name,
        tool_arguments=tool_args,
        raw_message_content=text,
    )


def format_orchestrator_print(r: OrchestratorResult) -> str:
    """Human-readable lines for CLI / logs (not JSON-primary UX)."""
    lines: List[str] = []
    lines.append(f"(top semantic similarity: {r.top_semantic_score:.3f}; weak_retrieval={r.retrieval_weak})")
    lines.append("")
    if r.tool_name == "refuse_and_escalate":
        a = r.tool_arguments
        lines.append("— Escalation —")
        lines.append(f"Reason: {a.get('reason', '')}")
        lines.append(f"Urgency: {a.get('urgency', '')}")
        lines.append(f"Escalate to: {a.get('escalation_target', '')}")
        lines.append(f"Case summary: {a.get('case_summary', '')}")
    elif r.tool_name == "answer_protocol_question":
        a = r.tool_arguments
        lines.append("— Protocol answer —")
        lines.append(a.get("answer", "").strip())
        lines.append("")
        lines.append(f"Source (model): {a.get('source', '')}")
        lines.append(f"Confidence: {a.get('confidence', '')}")
        if r.retrieved:
            lines.append("")
            lines.append("Index citations:")
            lines.append(format_citations(r.retrieved))
    else:
        lines.append("(No tool call returned.)")
        if r.raw_message_content:
            lines.append(r.raw_message_content)
    return "\n".join(lines)


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get(
        "SCM_QUERY",
        "IFA tablet dose for pregnant women per MoHFW guidelines?",
    )
    r = orchestrate_query(q, index_dir=index_dir)
    print(format_orchestrator_print(r))


if __name__ == "__main__":
    main()
