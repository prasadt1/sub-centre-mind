"""Unit tests for confidence gate (no FAISS/torch)."""

from dataclasses import dataclass

from rag.gate import should_skip_generation, top_semantic_score


@dataclass
class _FakeChunk:
    semantic_score: float


def test_top_semantic_score_empty():
    assert top_semantic_score([]) == 0.0


def test_should_skip_when_gate_off():
    chunks = [_FakeChunk(0.1)]
    assert should_skip_generation(chunks, gate_on=False, min_sim=0.7) is False


def test_should_skip_when_no_chunks_gate_on():
    assert should_skip_generation([], gate_on=True, min_sim=0.7) is True


def test_should_skip_when_below_threshold():
    chunks = [_FakeChunk(0.5)]
    assert should_skip_generation(chunks, gate_on=True, min_sim=0.7) is True


def test_should_not_skip_when_above_threshold():
    chunks = [_FakeChunk(0.85)]
    assert should_skip_generation(chunks, gate_on=True, min_sim=0.7) is False
