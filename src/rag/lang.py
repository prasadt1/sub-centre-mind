"""Lightweight language detection for query logging.

Heuristic-only — no ML models, no external service. Returns ISO 639-1
codes used by the audit log: 'en', 'hi', 'mr', or 'unknown'.

This is *not* a substitute for proper language ID; it's good enough to
populate `query_lang` in the report and to drive small UI hints. ASR
results from Whisper carry their own language code which should be
preferred over this heuristic.
"""

from __future__ import annotations

import re

_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")
_LATIN_LETTER = re.compile(r"[A-Za-z]")

# Common Marathi-only function words / inflections (rough — overlaps exist).
_MARATHI_HINTS = (
    "आहे",
    "आहेत",
    "करतो",
    "करते",
    "करतात",
    "मध्ये",
    "साठी",
    "नाही",
    "होते",
    "त्यांना",
    "तुम्ही",
    "गर्भवती",
    "महिलांसाठी",
    "महिलांना",
)

# Common Hindi-only markers.
_HINDI_HINTS = (
    "है",
    "हैं",
    "करता",
    "करती",
    "करते",
    "में",
    "लिए",
    "नहीं",
    "थे",
    "उन्हें",
    "आप",
    "गर्भवती",
    "महिलाओं",
)


_MARATHI_CORPUS_EXPANSION = (
    "pregnancy maternal health IFA iron folic acid supplementation "
    "ANC antenatal care immunization guidelines dose schedule"
)


def expand_query_for_retrieval(text: str) -> str:
    """Return a retrieval-optimised version of *text*.

    The FAISS index is built from English/Hindi clinical corpus chunks.
    The multilingual MiniLM embedder handles those languages better than
    Marathi, so short Marathi queries can fall below the 0.7 similarity
    threshold even when semantically correct.

    For Marathi queries we append a short English domain phrase so the
    joint embedding aligns better with corpus vectors. The original text
    is always the prefix — Ollama still receives the user's own language.
    """
    if detect_language(text) == "mr":
        return f"{text} {_MARATHI_CORPUS_EXPANSION}"
    return text


def detect_language(text: str) -> str:
    """Return one of: 'en', 'hi', 'mr', 'unknown'."""
    if not text:
        return "unknown"
    s = text.strip()
    if not s:
        return "unknown"

    has_dev = bool(_DEVANAGARI_RANGE.search(s))
    has_latin = bool(_LATIN_LETTER.search(s))

    # Any Devanagari → treat as Indic; embedded Latin drug/term names don't
    # change the user's spoken / typed language. Disambiguate hi vs mr.
    if has_dev:
        mr_hits = sum(1 for w in _MARATHI_HINTS if w in s)
        hi_hits = sum(1 for w in _HINDI_HINTS if w in s)
        if mr_hits > hi_hits:
            return "mr"
        return "hi"

    if has_latin:
        return "en"

    return "unknown"
