"""Tests for the vision client — LLM backend is fully mocked."""

from __future__ import annotations

import base64

import pytest

import vision.client as vc
from vision.client import (
    MEDICINE_PACKET_PROMPT,
    PRINTED_TEXT_PROMPT,
    REGISTER_ROW_PROMPT,
    analyze_image,
    describe_medicine_packet,
    read_printed_text,
    read_register_row,
)


class _FakeBackend:
    """Records calls and returns a canned response."""

    def __init__(self, content: str):
        self.calls: list = []
        self._content = content

    def vision(self, image_b64, prompt, *, model, options=None, timeout=180.0):
        self.calls.append(
            {"image_b64": image_b64, "prompt": prompt, "model": model, "options": options, "timeout": timeout}
        )
        return self._content.strip()


def _patch_backend(monkeypatch, content: str) -> _FakeBackend:
    backend = _FakeBackend(content)
    monkeypatch.setattr(vc, "get_backend", lambda: backend)
    return backend


def test_analyze_image_passes_base64_and_returns_text(monkeypatch):
    backend = _patch_backend(monkeypatch, content=" hello world ")
    result = analyze_image(
        b"\x89PNG\r\nfake",
        prompt="Describe.",
        use_case="custom",
        model="gemma4:latest",
        num_predict=64,
        timeout=30.0,
    )
    assert result.text == "hello world"
    assert result.use_case == "custom"
    assert result.model == "gemma4:latest"
    call = backend.calls[0]
    assert call["model"] == "gemma4:latest"
    assert call["prompt"] == "Describe."
    decoded = base64.b64decode(call["image_b64"])
    assert decoded == b"\x89PNG\r\nfake"
    assert call["options"].num_predict == 64


def test_printed_text_uses_strict_prompt(monkeypatch):
    backend = _patch_backend(monkeypatch, content="IFA: 100 tablets")
    out = read_printed_text(b"img")
    assert out.use_case == "printed_text"
    assert "Vision OCR only" in out.boundary_note
    assert backend.calls[0]["prompt"] == PRINTED_TEXT_PROMPT


def test_medicine_packet_always_signals_escalation_in_boundary(monkeypatch):
    backend = _patch_backend(monkeypatch, content="Brand: X")
    out = describe_medicine_packet(b"img")
    assert out.use_case == "medicine_packet"
    assert "Medical Officer" in out.boundary_note
    assert backend.calls[0]["prompt"] == MEDICINE_PACKET_PROMPT


def test_register_row_uses_register_prompt(monkeypatch):
    backend = _patch_backend(monkeypatch, content="Date: 2026-05-03\nHb: 11")
    out = read_register_row(b"img")
    assert out.use_case == "register_row"
    assert backend.calls[0]["prompt"] == REGISTER_ROW_PROMPT


def test_backend_error_propagates(monkeypatch):
    class _ErrorBackend:
        def vision(self, *a, **kw):
            raise RuntimeError("model not found")

    monkeypatch.setattr(vc, "get_backend", lambda: _ErrorBackend())
    with pytest.raises(RuntimeError, match="model not found"):
        analyze_image(b"x", prompt="p")
