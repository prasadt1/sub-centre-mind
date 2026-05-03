"""Tests for the vision client — Ollama HTTP is fully mocked."""

from __future__ import annotations

import base64

import pytest

from vision import client as vc
from vision.client import (
    MEDICINE_PACKET_PROMPT,
    PRINTED_TEXT_PROMPT,
    REGISTER_ROW_PROMPT,
    analyze_image,
    describe_medicine_packet,
    read_printed_text,
    read_register_row,
)


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _patch_post(monkeypatch, captured: dict, content: str):
    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResp({"message": {"content": content}})

    monkeypatch.setattr(vc.requests, "post", fake_post)


def test_analyze_image_passes_base64_and_returns_text(monkeypatch):
    captured: dict = {}
    _patch_post(monkeypatch, captured, content=" hello world ")
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
    j = captured["json"]
    assert j["model"] == "gemma4:latest"
    assert j["think"] is False
    assert j["stream"] is False
    msg = j["messages"][0]
    assert msg["role"] == "user"
    assert msg["content"] == "Describe."
    decoded = base64.b64decode(msg["images"][0])
    assert decoded == b"\x89PNG\r\nfake"
    assert j["options"]["num_predict"] == 64


def test_printed_text_uses_strict_prompt(monkeypatch):
    captured: dict = {}
    _patch_post(monkeypatch, captured, content="IFA: 100 tablets")
    out = read_printed_text(b"img")
    assert out.use_case == "printed_text"
    assert "Vision OCR only" in out.boundary_note
    assert captured["json"]["messages"][0]["content"] == PRINTED_TEXT_PROMPT


def test_medicine_packet_always_signals_escalation_in_boundary(monkeypatch):
    captured: dict = {}
    _patch_post(monkeypatch, captured, content="Brand: X")
    out = describe_medicine_packet(b"img")
    assert out.use_case == "medicine_packet"
    assert "Medical Officer" in out.boundary_note
    assert captured["json"]["messages"][0]["content"] == MEDICINE_PACKET_PROMPT


def test_register_row_uses_register_prompt(monkeypatch):
    captured: dict = {}
    _patch_post(monkeypatch, captured, content="Date: 2026-05-03\nHb: 11")
    out = read_register_row(b"img")
    assert out.use_case == "register_row"
    assert captured["json"]["messages"][0]["content"] == REGISTER_ROW_PROMPT


def test_ollama_error_payload_raises(monkeypatch):
    def fake_post(url, json, timeout):
        return _FakeResp({"error": "model not found"})

    monkeypatch.setattr(vc.requests, "post", fake_post)
    with pytest.raises(RuntimeError, match="model not found"):
        analyze_image(b"x", prompt="p")
