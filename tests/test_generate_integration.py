"""generate_answer behavior with retrieve() and requests.post() mocked.

Covers the two non-Ollama branches:
- gate blocks weak retrieval → returns fixed escalation copy, no HTTP call
- gate passes → POST is made with expected payload shape; response parsed

These tests do NOT touch FAISS, sentence-transformers, or Ollama.
"""

from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path


def _stub_query_module(monkeypatch) -> None:
    """Install a minimal `rag.query` stub before importing `rag.generate`.

    The real `rag.query` imports torch/sentence-transformers/faiss, which the
    test environment may lack. The stub provides only the symbols `generate.py`
    re-exports / uses at import time.

    Uses monkeypatch so the stub is removed from sys.modules after each test,
    preventing pollution of tests that check the real rag.query module.
    """

    @dataclass
    class RetrievedChunk:
        chunk_id: str
        source_file: str
        page: int
        score: float
        text: str
        semantic_score: float

    def format_citations(chunks):
        return "\n".join(
            f"[{i}] {c.source_file} p.{c.page} (sim={c.semantic_score:.3f})"
            for i, c in enumerate(chunks, start=1)
        )

    def retrieve(query, *, index_dir, top_k=5):
        raise AssertionError("retrieve() must be patched per test")

    mod = types.ModuleType("rag.query")
    mod.RetrievedChunk = RetrievedChunk
    mod.format_citations = format_citations
    mod.retrieve = retrieve
    monkeypatch.setitem(sys.modules, "rag.query", mod)


def _import_generate(monkeypatch):
    _stub_query_module(monkeypatch)
    if "rag.generate" in sys.modules:
        return importlib.reload(sys.modules["rag.generate"])
    return importlib.import_module("rag.generate")


def test_generate_answer_normalises_asr_before_retrieve(monkeypatch, tmp_path):
    """generate_answer must pass normalised+expanded text to retrieve(), not raw user query."""
    gen = _import_generate(monkeypatch)

    captured = {}

    def fake_retrieve(query, *, index_dir, top_k=5):
        captured["query"] = query
        return []

    monkeypatch.setattr(gen, "retrieve", fake_retrieve)
    monkeypatch.setenv("SCM_CONFIDENCE_GATE", "0")

    gen.generate_answer(
        "आईरन और कल्शीम की कमी के लिए क्या करें?",
        index_dir=tmp_path,
    )

    retrieval_q = captured.get("query", "")
    assert "iron" in retrieval_q, (
        f"'iron' must appear in retrieval query; got: {retrieval_q!r}"
    )
    assert "calcium" in retrieval_q.lower(), (
        f"'calcium' must appear in retrieval query; got: {retrieval_q!r}"
    )


def test_gate_blocks_weak_retrieval_no_http(monkeypatch, tmp_path):
    gen = _import_generate(monkeypatch)

    def fake_retrieve(query, *, index_dir, top_k=5):
        return []

    monkeypatch.setattr(gen, "retrieve", fake_retrieve)

    called = {"posts": 0}

    def fake_post(*a, **kw):
        called["posts"] += 1
        raise AssertionError("Ollama must not be called when gate blocks")

    monkeypatch.setattr(gen.requests, "post", fake_post)
    monkeypatch.setenv("SCM_CONFIDENCE_GATE", "1")
    monkeypatch.setenv("SCM_RETRIEVAL_MIN_SIM", "0.7")

    out = gen.generate_answer("anything", index_dir=tmp_path)
    assert out.confidence_blocked is True
    assert called["posts"] == 0
    assert "No sufficiently confident match" in out.answer


def test_gate_passes_calls_ollama_and_parses(monkeypatch, tmp_path):
    gen = _import_generate(monkeypatch)
    rq = sys.modules["rag.query"]

    chunk = rq.RetrievedChunk(
        chunk_id="c1",
        source_file="MoHFW-IFA.pdf",
        page=12,
        score=0.91,
        text="Daily IFA tablet during ANC...",
        semantic_score=0.85,
    )
    monkeypatch.setattr(gen, "retrieve", lambda q, *, index_dir, top_k=5: [chunk])

    captured = {}

    class FakeResp:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResp({"response": "Take 1 IFA tablet daily during ANC."})

    monkeypatch.setattr(gen.requests, "post", fake_post)
    monkeypatch.delenv("SCM_CONFIDENCE_GATE", raising=False)
    monkeypatch.setenv("SCM_RETRIEVAL_MIN_SIM", "0.7")

    out = gen.generate_answer("IFA dose", index_dir=tmp_path, num_predict=64)

    assert out.confidence_blocked is False
    assert out.answer == "Take 1 IFA tablet daily during ANC."
    assert "MoHFW-IFA.pdf" in out.citations
    assert captured["url"].endswith("/api/generate")
    assert captured["json"]["think"] is False
    assert captured["json"]["options"]["num_predict"] == 64
    assert "Take 1 IFA tablet" not in captured["json"]["prompt"]
