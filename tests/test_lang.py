"""Tests for src/rag/lang.py — heuristic language detection."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from rag.lang import detect_language, expand_query_for_retrieval, normalise_asr_transcript


def test_empty_returns_unknown() -> None:
    assert detect_language("") == "unknown"
    assert detect_language("   \t\n") == "unknown"


def test_english_query() -> None:
    assert detect_language("IFA schedule in pregnancy") == "en"
    assert detect_language("How much iron should ANM give?") == "en"


def test_marathi_query() -> None:
    # 'गर्भवती महिलांसाठी लोह आणि फॉलिक अॅसिड कधी द्यावे?'
    text = "गर्भवती महिलांसाठी लोह आणि फॉलिक अॅसिड कधी द्यावे आहे?"
    assert detect_language(text) == "mr"


def test_hindi_query() -> None:
    # 'गर्भवती महिलाओं के लिए IFA की खुराक क्या है?'
    text = "गर्भवती महिलाओं के लिए लोह की खुराक क्या है?"
    assert detect_language(text) == "hi"


def test_devanagari_only_no_hints_defaults_to_hindi() -> None:
    # No clear marathi/hindi function-word hits — heuristic falls back to 'hi'.
    assert detect_language("लोह कब") == "hi"


def test_mixed_script_treats_devanagari_as_indic() -> None:
    # Even when an English drug/term appears, the surrounding Devanagari
    # signals the user is asking in Hindi/Marathi.
    assert detect_language("मां को IFA की खुराक") == "hi"
    assert detect_language("IFA dose गर्भवती महिलांसाठी आहे") == "mr"


def test_pure_punctuation_unknown() -> None:
    assert detect_language("?!?? ...") == "unknown"


# --- expand_query_for_retrieval ---

def test_expand_query_english_unchanged() -> None:
    q = "IFA schedule in pregnancy"
    assert expand_query_for_retrieval(q) == q


def test_expand_query_hindi_expanded() -> None:
    q = "गर्भवती महिलाओं के लिए IFA खुराक क्या है?"
    expanded = expand_query_for_retrieval(q)
    assert expanded != q, "Hindi query must be expanded"
    assert expanded.startswith(q), "original Hindi text must be the prefix"
    assert any(kw in expanded.lower() for kw in ("pregnancy", "ifa", "supplementation", "anc"))


def test_expand_query_marathi_preserves_original_as_prefix() -> None:
    q = "गर्भवती महिलांसाठी IFA डोस काय आहे?"
    expanded = expand_query_for_retrieval(q)
    assert expanded.startswith(q), "original Marathi text must be the prefix"


def test_expand_query_marathi_appends_english_clinical_terms() -> None:
    q = "गर्भवती महिलांसाठी IFA डोस काय आहे?"
    expanded = expand_query_for_retrieval(q)
    assert expanded != q, "Marathi query must be expanded"
    # Expanded text should contain English clinical keywords that exist in the corpus.
    lowered = expanded.lower()
    assert any(kw in lowered for kw in ("pregnancy", "ifa", "supplementation", "anc")), (
        f"Expected clinical English keywords in expansion, got: {expanded!r}"
    )


def test_expand_query_unknown_lang_unchanged() -> None:
    q = "?!?? ..."
    assert expand_query_for_retrieval(q) == q


# --- normalise_asr_transcript ---

def test_normalise_phonetic_iron() -> None:
    assert "iron" in normalise_asr_transcript("आईरन की कमी")


def test_normalise_calcium_variant_kalachhim() -> None:
    result = normalise_asr_transcript("कल्छिम की जांच करें")
    assert "calcium" in result.lower()


def test_normalise_calcium_variant_kalshiyam() -> None:
    result = normalise_asr_transcript("कल्शियम टेबलेट लें")
    assert "calcium" in result.lower()


def test_normalise_real_failing_query() -> None:
    q = "आईरन और कल्छिम की कमी के लिए क्या करें?"
    result = normalise_asr_transcript(q)
    assert "iron" in result
    assert "calcium" in result.lower()
    assert "कमी" in result, "non-phonetic Hindi words must be preserved"


def test_normalise_no_phonetic_terms_unchanged() -> None:
    q = "गर्भवती महिलाओं के लिए IFA खुराक क्या है?"
    assert normalise_asr_transcript(q) == q


def test_normalise_empty_unchanged() -> None:
    assert normalise_asr_transcript("") == ""


def test_normalise_english_unchanged() -> None:
    q = "IFA schedule in pregnancy"
    assert normalise_asr_transcript(q) == q
