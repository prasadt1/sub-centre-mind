"""CactusBackend — Ollama-compatible HTTP bridge (ADR-0001 Phase 3a)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from llm import GenerateOptions, get_backend
from llm.backend import ChatMessage, ChatResponse
from llm.cactus import CactusBackend


def test_cactus_backend_requires_http_base() -> None:
    with pytest.raises(RuntimeError, match="SCM_CACTUS_HTTP_BASE"):
        CactusBackend(base_url="")


def test_cactus_backend_delegates_to_inner_http(monkeypatch) -> None:
    inner = MagicMock()
    inner.generate.return_value = "generated"
    inner.chat.return_value = ChatResponse(content="hi", tool_calls=[])
    inner.vision.return_value = "seen"

    monkeypatch.setattr("llm.cactus.OllamaBackend", lambda base_url: inner)

    b = CactusBackend(base_url="http://bridge.test:9")
    assert b.generate("p", model="m") == "generated"
    inner.generate.assert_called_once_with(
        "p", model="m", options=None, timeout=180.0
    )

    msgs = [ChatMessage(role="user", content="q")]
    assert b.chat(msgs, model="m", tools=None).content == "hi"
    inner.chat.assert_called_once()

    assert b.vision("b64", "prompt", model="m") == "seen"
    inner.vision.assert_called_once()

    opts = GenerateOptions(num_predict=10, temperature=0.5, think=True)
    b.generate("x", model="y", options=opts, timeout=30.0)
    inner.generate.assert_called_with("x", model="y", options=opts, timeout=30.0)


def test_get_backend_cactus_requires_env(monkeypatch) -> None:
    monkeypatch.setenv("SCM_BACKEND", "cactus")
    monkeypatch.delenv("SCM_CACTUS_HTTP_BASE", raising=False)
    with pytest.raises(RuntimeError, match="SCM_CACTUS_HTTP_BASE"):
        get_backend()
