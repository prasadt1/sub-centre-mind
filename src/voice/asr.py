"""Local ASR via faster-whisper (CPU-friendly).

faster-whisper is loaded lazily so the rest of the codebase / tests do not
require it. If the package is missing, callers receive a clear ASRUnavailable
error with installation hints.

Model sizes (CPU, int8):
    tiny   ≈  75 MB, ~1.5x realtime
    base   ≈ 140 MB
    small  ≈ 460 MB  (recommended for Hindi/Marathi accuracy)

Set SCM_ASR_MODEL=small to upgrade.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


class ASRError(RuntimeError):
    """Generic ASR failure."""


class ASRUnavailable(ASRError):
    """faster-whisper / its dependencies are not installed."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    language_probability: float
    duration_s: float
    model_name: str


_MODEL_CACHE: dict[str, object] = {}


def _load_model(name: str):
    if name in _MODEL_CACHE:
        return _MODEL_CACHE[name]
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as e:
        raise ASRUnavailable(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from e
    model = WhisperModel(name, device="cpu", compute_type="int8")
    _MODEL_CACHE[name] = model
    return model


def transcribe_with_hindi_fallback(
    audio_bytes: bytes,
    *,
    model_name: Optional[str] = None,
    audio_suffix: str = ".wav",
) -> "TranscriptionResult":
    """Transcribe audio, retrying with language='hi' if Urdu script is detected.

    Whisper's `tiny` model frequently mis-classifies Hindi speech as Urdu (ISO
    639-1: `ur`) when confidence is low, producing Arabic/Nastaliq script output
    that cannot match the Devanagari/English corpus. This wrapper detects that
    case and retries with an explicit Hindi hint so the result is Devanagari.

    Falls through to the plain `transcribe()` result when no Arabic script is
    detected. Safe to call for all languages — non-Urdu outputs are returned
    unchanged.
    """
    from rag.lang import contains_arabic_script  # lazy to avoid circular import

    result = transcribe(audio_bytes, model_name=model_name, audio_suffix=audio_suffix)
    if contains_arabic_script(result.text):
        result = transcribe(
            audio_bytes,
            model_name=model_name,
            language="hi",
            audio_suffix=audio_suffix,
        )
    return result


def transcribe(
    audio_bytes: bytes,
    *,
    model_name: Optional[str] = None,
    language: Optional[str] = None,
    audio_suffix: str = ".wav",
) -> TranscriptionResult:
    """Transcribe an audio blob to text. Hindi/Marathi/English supported by Whisper.

    Args:
        audio_bytes: raw audio bytes (WAV/MP3/M4A/FLAC etc. supported by whisper.cpp).
        model_name:  whisper model size; defaults to SCM_ASR_MODEL or 'tiny'.
        language:    ISO 639-1 code ('hi', 'mr', 'en'). None = auto-detect.
        audio_suffix: file extension hint for the temp file written to disk.

    Returns:
        TranscriptionResult with `text`, detected language, and duration.

    Raises:
        ASRUnavailable: if faster-whisper / its deps are missing.
        ASRError:       for transcription failures.
    """
    name = model_name or os.environ.get("SCM_ASR_MODEL", "tiny")
    model = _load_model(name)

    with tempfile.NamedTemporaryFile(suffix=audio_suffix, delete=False) as f:
        f.write(audio_bytes)
        path = Path(f.name)
    try:
        segments, info = model.transcribe(  # type: ignore[attr-defined]
            str(path),
            language=language,
            vad_filter=False,
            beam_size=1,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", "") or "",
            language_probability=float(getattr(info, "language_probability", 0.0) or 0.0),
            duration_s=float(getattr(info, "duration", 0.0) or 0.0),
            model_name=name,
        )
    except Exception as e:  # noqa: BLE001
        raise ASRError(f"Transcription failed: {e}") from e
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
