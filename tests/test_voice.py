"""ASR module tests — faster-whisper is mocked, no audio dependencies needed."""

from __future__ import annotations

import sys
import types

import pytest

from voice import asr as asr_module
from voice.asr import ASRUnavailable, transcribe


def _install_fake_faster_whisper(monkeypatch):
    """Provide a stand-in `faster_whisper` module so transcribe() succeeds."""
    fake_mod = types.ModuleType("faster_whisper")

    class _FakeSegment:
        def __init__(self, text):
            self.text = text

    class _FakeInfo:
        language = "en"
        language_probability = 0.95
        duration = 1.5

    class _FakeWhisperModel:
        def __init__(self, *a, **kw):
            self.args = (a, kw)

        def transcribe(self, path, language=None, vad_filter=False, beam_size=1):
            segments = [_FakeSegment("Take iron and folic acid daily.")]
            return iter(segments), _FakeInfo()

    fake_mod.WhisperModel = _FakeWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_mod)
    asr_module._MODEL_CACHE.clear()


def test_transcribe_returns_clean_text(monkeypatch):
    _install_fake_faster_whisper(monkeypatch)
    out = transcribe(b"RIFF....WAVE....", model_name="tiny", language="en")
    assert out.text == "Take iron and folic acid daily."
    assert out.language == "en"
    assert out.language_probability > 0.9
    assert out.duration_s > 0
    assert out.model_name == "tiny"


def test_transcribe_when_faster_whisper_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)  # forces ImportError on import
    asr_module._MODEL_CACHE.clear()
    with pytest.raises(ASRUnavailable):
        transcribe(b"RIFF", model_name="tiny")


def test_model_cache_reused(monkeypatch):
    _install_fake_faster_whisper(monkeypatch)
    transcribe(b"a", model_name="tiny")
    transcribe(b"b", model_name="tiny")
    assert "tiny" in asr_module._MODEL_CACHE
