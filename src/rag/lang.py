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


# Phonetic Devanagari renderings that Whisper produces for common clinical
# English terms. Whisper often writes loan-words phonetically rather than
# using the standard Hindi/Marathi spelling or the original English.
# Keys are Devanagari phonetic forms; values are the canonical English term
# that exists in the MoHFW/WHO corpus.
_ASR_NORMALISE_MAP: dict[str, str] = {
    "आईरन":      "iron",        # "iron" spoken in Hindi context
    "आयरन":      "iron",        # alternative phonetic form
    "कल्छिम":    "calcium",     # "calcium" — common Whisper mis-transcription
    "कल्शियम":   "calcium",     # closer phonetic form
    "कैल्शियम":  "calcium",     # standard Hindi spelling → normalise to English
    "हेमोग्लोबिन": "haemoglobin",
    "एनीमिया":   "anaemia",
    "अनीमिया":   "anaemia",
    "विटामिन":   "vitamin",
    "प्रोटीन":   "protein",
    "सप्लीमेंट": "supplement",
    "फोलिक":     "folic",       # "folic acid" partial
    "एसिड":      "acid",        # paired with फोलिक
    "टेबलेट":    "tablet",
    "डोज":       "dose",
    "जिंक":      "zinc",
}


def normalise_asr_transcript(text: str) -> str:
    """Replace known phonetic Devanagari mis-transcriptions with English equivalents.

    Whisper (and other ASR systems) often transcribe clinical loan-words
    phonetically into Devanagari (e.g. "कल्छिम" for "calcium"). These forms
    do not appear in the MoHFW corpus, so FAISS similarity suffers. This
    function maps them back to the English terms that *do* appear in the index.

    The surrounding Hindi/Marathi sentence structure is preserved — only the
    known phonetic tokens are replaced. Safe to call on any text; strings with
    no known phonetic tokens are returned unchanged.
    """
    if not text:
        return text
    result = text
    for phonetic, canonical in _ASR_NORMALISE_MAP.items():
        result = result.replace(phonetic, canonical)
    return result


_INDIC_CORPUS_EXPANSION = (
    "pregnancy maternal health IFA iron folic acid supplementation "
    "ANC antenatal care immunization guidelines dose schedule"
)


def expand_query_for_retrieval(text: str) -> str:
    """Return a retrieval-optimised version of *text*.

    The FAISS index is built from English/Hindi clinical corpus chunks.
    The multilingual MiniLM embedder produces lower similarities for
    Hindi and Marathi queries against an English-primary corpus.

    For Hindi and Marathi queries we append a short English clinical domain
    phrase so the joint embedding aligns better with corpus vectors. The
    original text is always the prefix — Ollama still receives the user's
    own language for generation.
    """
    if detect_language(text) in ("mr", "hi"):
        return f"{text} {_INDIC_CORPUS_EXPANSION}"
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
