"""Lightweight tokenization for BM25 (Latin + Devanagari word chars)."""

from __future__ import annotations

import re
from typing import List

_TOKEN_RE = re.compile(r"[\w\u0900-\u0dff]+", re.UNICODE)


def tokenize_bm25(text: str) -> List[str]:
    if not text or not text.strip():
        return ["empty"]
    toks = _TOKEN_RE.findall(text.lower())
    return toks if toks else ["empty"]
