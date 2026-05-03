"""Cactus backend — HTTP to an Ollama-compatible on-device bridge.

Cactus ships as native Android / Kotlin Multiplatform / Flutter SDKs; there is
no supported ``pip install`` Python binding for this repo. Phase 3 therefore
uses a **thin HTTP companion** that exposes the same JSON contract as Ollama's
``/api/generate`` and ``/api/chat`` (vision uses ``/api/chat`` with ``images``),
implemented on the phone with libcactus / ``CactusLM`` and reachable from the
desktop demo via ``adb reverse`` or LAN.

Environment
-----------
``SCM_CACTUS_HTTP_BASE``
    Base URL only (no path suffix), e.g. ``http://127.0.0.1:18765``. The
    companion must serve Ollama-compatible routes: ``/api/generate`` and
    ``/api/chat`` under this base.

``SCM_BACKEND=cactus``
    Selects this backend (see :func:`llm.backend.get_backend`).

Embedding / FAISS / BM25 ports remain on the Python side until a later phase;
this module only swaps **LLM inference** transport. See ADR-0001 Phase 3–4.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from .backend import ChatMessage, ChatResponse, GenerateOptions
from .ollama import OllamaBackend

_MISSING_BASE = (
    "SCM_BACKEND=cactus requires SCM_CACTUS_HTTP_BASE (e.g. http://127.0.0.1:18765) "
    "pointing at an Ollama-compatible HTTP bridge backed by Cactus on-device. "
    "See docs/adr/0001-runtime-architecture-edge-deployment.md (Phase 3)."
)


class CactusBackend:
    """LLM inference via Cactus, using the same wire format as :class:`OllamaBackend`.

    Delegates to :class:`OllamaBackend` with ``base_url=SCM_CACTUS_HTTP_BASE`` so
    the Python moat (RAG, gate, tool schema) stays identical; only the host
    changes from ``OLLAMA_BASE_URL`` to the bridge.
    """

    def __init__(self, *, base_url: str | None = None) -> None:
        raw = (base_url or os.environ.get("SCM_CACTUS_HTTP_BASE", "")).strip().rstrip("/")
        if not raw:
            raise RuntimeError(_MISSING_BASE)
        self._http = OllamaBackend(base_url=raw)

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        return self._http.generate(prompt, model=model, options=options, timeout=timeout)

    def chat(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        tools: List[Dict[str, Any]] | None = None,
        options: GenerateOptions | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        return self._http.chat(
            messages,
            model=model,
            tools=tools,
            options=options,
            timeout=timeout,
        )

    def vision(
        self,
        image_b64: str,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        return self._http.vision(
            image_b64,
            prompt,
            model=model,
            options=options,
            timeout=timeout,
        )
