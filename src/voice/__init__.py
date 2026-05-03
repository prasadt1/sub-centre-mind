"""Voice (ASR) module — local Whisper for Hindi/Marathi/English speech input.

Gemma 4 lists an `audio` capability but Ollama 0.22.x does not yet expose it
through a stable API field. We use faster-whisper locally to keep the
"all reasoning on device" story intact: speech → text → existing RAG/tool path.
"""

from .asr import (  # noqa: F401
    ASRError,
    ASRUnavailable,
    TranscriptionResult,
    transcribe,
    transcribe_with_hindi_fallback,
)
