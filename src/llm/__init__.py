"""LLM backend abstraction — swap Ollama / Cactus without touching the moat.

Usage:
    from llm import get_backend
    backend = get_backend()           # reads SCM_BACKEND env (default: "ollama")
    text = backend.generate(...)
    msg  = backend.chat(...)
    text = backend.vision(...)

``SCM_BACKEND=cactus`` requires ``SCM_CACTUS_HTTP_BASE`` (Ollama-compatible HTTP
bridge to on-device Cactus). See ``src/llm/cactus.py`` and ADR-0001 Phase 3.
"""

from .backend import (
    ChatMessage,
    ChatResponse,
    GenerateOptions,
    LLMBackend,
    get_backend,
)

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "GenerateOptions",
    "LLMBackend",
    "get_backend",
]
