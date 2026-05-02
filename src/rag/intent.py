"""
Multilingual supplement-intent hints for reranking retrieval.

Embeddings alone confuse iron (IFA) vs calcium; we rescore candidates using
lightweight keyword signals (English + Hindi + Marathi Devanagari).
"""

from __future__ import annotations

import re
from enum import Enum
class SupplementIntent(Enum):
    IRON_IFA = "iron_ifa"
    CALCIUM = "calcium"
    FOLIC_ACID = "folic_acid"
    GENERIC = "generic"


# Query-side keywords (lowercased ASCII + Devanagari literals).
_IRON_QUERY_EN = (
    r"\bifa\b",
    r"\biron\b",
    r"ferrous",
    r"\banemia\b",
    r"\banaemia\b",
)
_IRON_QUERY_DEV = ("आयरन", "आयर्न", "लौह", "आयरनचे", "आयर्नचे", "आयरन की", "अनेमिया")

_CALCIUM_QUERY_DEV = ("कैल्शियम", "कॅल्शियम", "कॅल्शिअम")

_FOLIC_QUERY_EN = (r"\bfolic\b",)
_FOLIC_QUERY_DEV = ("फोलिक", "फ़ोलिक")


def detect_supplement_intent(query: str) -> SupplementIntent:
    if not query or not query.strip():
        return SupplementIntent.GENERIC

    q_ascii = query.lower()

    iron = 0
    for p in _IRON_QUERY_EN:
        if re.search(p, q_ascii, re.I):
            iron += 2
    for s in _IRON_QUERY_DEV:
        if s in query:
            iron += 3

    calcium = 0
    if re.search(r"\bcalcium\b", q_ascii, re.I):
        calcium += 3
    for s in _CALCIUM_QUERY_DEV:
        if s in query:
            calcium += 3

    folic = 0
    for p in _FOLIC_QUERY_EN:
        if re.search(p, q_ascii, re.I):
            folic += 2
    for s in _FOLIC_QUERY_DEV:
        if s in query:
            folic += 3

    # IFA in Latin counts strongly for iron.
    if "ifa" in q_ascii:
        iron += 2

    scores = [
        (iron, SupplementIntent.IRON_IFA),
        (calcium, SupplementIntent.CALCIUM),
        (folic, SupplementIntent.FOLIC_ACID),
    ]
    scores.sort(key=lambda x: x[0], reverse=True)
    best_score, best_intent = scores[0]
    second_score = scores[1][0]

    if best_score == 0:
        return SupplementIntent.GENERIC
    # Require a margin so "pregnancy" alone doesn't trigger.
    if best_score == second_score and second_score > 0:
        return SupplementIntent.GENERIC
    return best_intent


def _lower(text: str) -> str:
    return text.lower()


def chunk_supports_iron(text: str) -> bool:
    t = text
    tl = _lower(t)
    if any(s in t for s in ("आयरन", "आयर्न", "लौह")):
        return True
    if re.search(r"\b(ifa|iron|ferrous)\b", tl, re.I):
        return True
    if "iron and folic" in tl or "iron folic" in tl or "ifa tablet" in tl:
        return True
    return False


def chunk_has_ifa_schedule_cues(text: str) -> bool:
    """Passages that actually describe IFA / iron supplementation schedules (vs anemia indicators only)."""
    tl = _lower(text)
    if "ifa" in tl:
        return True
    if "iron and folic" in tl or "iron folic" in tl:
        return True
    if "daily iron" in tl and "supplementation" in tl:
        return True
    if "one tablet" in tl and ("iron" in tl or "ifa" in tl or "folic acid" in tl):
        return True
    if "two tablets" in tl and "ifa" in tl:
        return True
    return False


def chunk_is_hmis_indicator_noise(text: str) -> bool:
    """HMIS reporting rows dominate embedding similarity but are wrong for 'how much IFA' questions."""
    tl = _lower(text)
    if tl.count("hmis") >= 2:
        return True
    if "hmis" in tl and "percentage" in tl:
        return True
    if re.search(r"\bhmis\s+[\d.]+\s*:", tl):
        return True
    return False


def chunk_is_family_planning_noise(text: str) -> bool:
    """Family-planning / contraception sections share 'pregnancy/maternal' wording but are wrong for IFA dose."""
    if chunk_has_ifa_schedule_cues(text):
        return False
    tl = _lower(text)
    if "family planning" in tl:
        return True
    # Continuation chunks on FP pages (weak contraceptive keywords).
    if ("unwanted pregnancies" in tl or "unwanted pregnancy" in tl) and "ifa" not in tl:
        return True
    hits = 0
    for kw in (
        "contraceptive",
        "iucd",
        "sterilization",
        "vasectomy",
        "spacing method",
        "permanent method",
        "oral contraceptive",
    ):
        if kw in tl:
            hits += 1
    return hits >= 2


def chunk_supports_calcium(text: str) -> bool:
    if "कैल्शियम" in text or "कॅल्शियम" in text or "कॅल्शिअम" in text:
        return True
    return "calcium" in _lower(text)


def chunk_supports_folic(text: str) -> bool:
    tl = _lower(text)
    if "फोलिक" in text or "फ़ोलिक" in text:
        return True
    return "folic acid" in tl or "folic" in tl


def _calcium_only_filename(source_file: str) -> bool:
    n = source_file.lower()
    return "calcium" in n and "ifa" not in n and "iron" not in n


def _iron_only_filename(source_file: str) -> bool:
    n = source_file.lower()
    if "calcium" in n:
        return False
    return "ifa" in n or "iron" in n or "iron and folic" in n


def rerank_multiplier(
    *,
    intent: SupplementIntent,
    chunk_text: str,
    source_file: str,
) -> float:
    """Positive multiplicative factor applied to cosine similarity for ordering."""
    m = 1.0
    ct = chunk_text
    sf = source_file

    if intent == SupplementIntent.IRON_IFA:
        if chunk_supports_iron(ct):
            m *= 1.18
        elif chunk_supports_folic(ct) and not chunk_supports_iron(ct):
            m *= 0.92
        if chunk_supports_calcium(ct) and not chunk_supports_iron(ct):
            m *= 0.55
        if _calcium_only_filename(sf) and not chunk_supports_iron(ct):
            m *= 0.22
        # Down-rank HMIS dashboard/metrics chunks unless they include IFA schedule language.
        if chunk_is_hmis_indicator_noise(ct) and not chunk_has_ifa_schedule_cues(ct):
            m *= 0.26
        # Down-rank family-planning chapters (often page-adjacent noise vs antenatal supplementation).
        elif chunk_is_family_planning_noise(ct):
            m *= 0.30
        elif chunk_has_ifa_schedule_cues(ct):
            m *= 1.12
        return min(m, 1.35)

    if intent == SupplementIntent.CALCIUM:
        if chunk_supports_calcium(ct):
            m *= 1.18
        if chunk_supports_iron(ct) and not chunk_supports_calcium(ct):
            m *= 0.6
        if _iron_only_filename(sf) and not chunk_supports_calcium(ct):
            m *= 0.35
        return min(m, 1.35)

    if intent == SupplementIntent.FOLIC_ACID:
        if chunk_supports_folic(ct):
            m *= 1.15
        if chunk_supports_iron(ct) and not chunk_supports_folic(ct):
            m *= 0.85
        return min(m, 1.3)

    return 1.0


def adjust_score(semantic_score: float, *, intent: SupplementIntent, chunk_text: str, source_file: str) -> float:
    """Final ranking score (still on cosine scale but rescaled for ordering)."""
    return float(semantic_score) * rerank_multiplier(
        intent=intent, chunk_text=chunk_text, source_file=source_file
    )


def intent_label(intent: SupplementIntent) -> str:
    return {
        SupplementIntent.IRON_IFA: "iron/IFA",
        SupplementIntent.CALCIUM: "calcium",
        SupplementIntent.FOLIC_ACID: "folic acid",
        SupplementIntent.GENERIC: "general",
    }[intent]
