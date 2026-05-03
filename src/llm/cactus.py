"""Cactus backend — on-device inference via the Cactus SDK.

Stub implementation. All methods raise NotImplementedError until
the Cactus SDK integration is built (ADR-0001, Phase 3).

Switch to this backend with: SCM_BACKEND=cactus
"""

from __future__ import annotations

from typing import Any, Dict, List

from .backend import ChatMessage, ChatResponse, GenerateOptions

_NOT_IMPL = (
    "CactusBackend is not yet implemented. "
    "Set SCM_BACKEND=ollama to use the verified Gate 1 path, "
    "or see docs/adr/0001-runtime-architecture-edge-deployment.md for the migration plan."
)


class CactusBackend:
    """Placeholder for Cactus on-device inference (ADR-0001, Option B)."""

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        raise NotImplementedError(_NOT_IMPL)

    def chat(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        tools: List[Dict[str, Any]] | None = None,
        options: GenerateOptions | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        raise NotImplementedError(_NOT_IMPL)

    def vision(
        self,
        image_b64: str,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        raise NotImplementedError(_NOT_IMPL)
