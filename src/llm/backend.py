"""LLMBackend Protocol and factory.

Three methods cover every LLM call site in Sub-Centre Mind:
    generate()  — prompt → text          (rag/generate.py, audit/report.py)
    chat()      — messages + tools → msg (query_router.py)
    vision()    — image + prompt → text  (vision/client.py)

Implementations live in sibling modules (ollama.py, cactus.py).
The active backend is selected by the SCM_BACKEND env var.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class GenerateOptions:
    """Common generation knobs shared across backends."""

    num_predict: int = 220
    temperature: float = 0.1
    think: bool = False


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str
    images: Optional[List[str]] = None  # base64-encoded, for vision


@dataclass(frozen=True)
class ChatResponse:
    """Normalised response from a chat-with-tools call."""

    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class LLMBackend(Protocol):
    """Minimal interface that every backend must satisfy."""

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        """Prompt-in, text-out (no chat history, no tools)."""
        ...

    def chat(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        tools: List[Dict[str, Any]] | None = None,
        options: GenerateOptions | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        """Multi-turn chat with optional tool definitions."""
        ...

    def vision(
        self,
        image_b64: str,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        """Single image (base64) + prompt → text."""
        ...


def get_backend(name: str | None = None) -> LLMBackend:
    """Return the backend selected by *name* or ``SCM_BACKEND`` env var.

    Supported values: ``ollama`` (default), ``cactus``.

    ``cactus`` requires ``SCM_CACTUS_HTTP_BASE`` (Ollama-compatible bridge URL).
    """
    backend_name = (name or os.environ.get("SCM_BACKEND", "ollama")).strip().lower()

    if backend_name == "ollama":
        from .ollama import OllamaBackend

        return OllamaBackend()

    if backend_name == "cactus":
        from .cactus import CactusBackend

        return CactusBackend()

    raise ValueError(
        f"Unknown LLM backend: {backend_name!r}. "
        f"Set SCM_BACKEND to 'ollama' or 'cactus'."
    )
