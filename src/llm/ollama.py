"""Ollama backend — HTTP calls to localhost:11434.

This is the Gate 1 verified path. Refactored from inline requests.post()
calls in generate.py, query_router.py, vision/client.py, and report.py.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests

from .backend import ChatMessage, ChatResponse, GenerateOptions


class OllamaBackend:
    """LLMBackend implementation for Ollama's REST API."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
    ) -> None:
        base = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._generate_url = f"{base}/api/generate"
        self._chat_url = f"{base}/api/chat"

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        options: GenerateOptions | None = None,
        timeout: float = 180.0,
    ) -> str:
        opts = options or GenerateOptions()
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "think": opts.think,
            "stream": False,
            "options": {
                "num_predict": opts.num_predict,
                "temperature": opts.temperature,
            },
        }
        resp = requests.post(self._generate_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return (resp.json().get("response") or "").strip()

    def chat(
        self,
        messages: List[ChatMessage],
        *,
        model: str,
        tools: List[Dict[str, Any]] | None = None,
        options: GenerateOptions | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        opts = options or GenerateOptions()
        msg_dicts: List[Dict[str, Any]] = []
        for m in messages:
            d: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.images:
                d["images"] = m.images
            msg_dicts.append(d)

        payload: Dict[str, Any] = {
            "model": model,
            "think": opts.think,
            "stream": False,
            "messages": msg_dicts,
        }
        if tools:
            payload["tools"] = tools

        resp = requests.post(self._chat_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("error"):
            raise RuntimeError(f"Ollama chat error: {data['error']}")

        msg = data.get("message") or {}
        return ChatResponse(
            content=(msg.get("content") or "").strip(),
            tool_calls=msg.get("tool_calls") or [],
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
        opts = options or GenerateOptions()
        payload: Dict[str, Any] = {
            "model": model,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "user", "content": prompt, "images": [image_b64]},
            ],
            "options": {
                "num_predict": opts.num_predict,
                "temperature": opts.temperature,
            },
        }
        resp = requests.post(self._chat_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("error"):
            raise RuntimeError(f"Ollama vision error: {data['error']}")

        msg = data.get("message") or {}
        return (msg.get("content") or "").strip()
