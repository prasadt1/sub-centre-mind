"""LLM backend abstraction — swap Ollama / Cactus / LiteRT without touching the moat.

Usage:
    from llm import get_backend
    backend = get_backend()           # reads SCM_BACKEND env (default: "ollama")
    text = backend.generate(...)
    msg  = backend.chat(...)
    text = backend.vision(...)
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
