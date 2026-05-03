"""Tests for audit aggregate + draft summary (no Ollama)."""

import json
from pathlib import Path

from audit.report import aggregate, template_summary
from audit.schema import append_event, new_event


def _seed(path: Path) -> None:
    append_event(path, new_event("rag_answer", top_sim=0.82, query_lang="en"))
    append_event(path, new_event("rag_answer", top_sim=0.78, query_lang="mr"))
    append_event(path, new_event("confidence_gate_blocked", top_sim=0.31))
    append_event(path, new_event("tool_refusal", urgency="high"))


def test_aggregate_counts_kinds_and_languages(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    _seed(p)
    stats = aggregate(p)
    assert stats["total_events"] == 4
    assert stats["by_kind"] == {
        "rag_answer": 2,
        "confidence_gate_blocked": 1,
        "tool_refusal": 1,
    }
    assert stats["confidence_gate_blocked_count"] == 1
    assert stats["queries_by_language"] == {"en": 1, "mr": 1}
    assert stats["top_sim_samples_count"] == 3
    assert isinstance(stats["top_sim_avg"], float)


def test_template_summary_mentions_counts(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    _seed(p)
    text = template_summary(aggregate(p))
    assert "Events recorded: 4" in text
    assert "rag_answer" in text
    assert "confidence_gate_blocked" in text


def test_aggregate_empty_file_is_zero(tmp_path: Path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    stats = aggregate(p)
    assert stats["total_events"] == 0
    assert stats["confidence_gate_blocked_count"] == 0
    assert stats["top_sim_avg"] is None


def test_aggregate_skips_blank_lines_and_invalid(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    _seed(p)
    with p.open("a", encoding="utf-8") as f:
        f.write("\n\n")
    stats = aggregate(p)
    assert stats["total_events"] == 4
