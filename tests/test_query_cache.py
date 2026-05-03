"""Tests for the artifact cache used by retrieve()."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def test_cache_module_has_clear_and_dicts() -> None:
    """Smoke: confirm the cache surface exists. Skips when torch is unavailable."""
    import importlib.util

    if importlib.util.find_spec("torch") is None:
        import pytest

        pytest.skip("torch not installed in this env; cache lives inside rag.query")

    from rag import query as q

    assert hasattr(q, "_ARTIFACTS_CACHE")
    assert hasattr(q, "_BM25_CACHE")
    assert hasattr(q, "clear_caches")
    assert isinstance(q._ARTIFACTS_CACHE, dict)
    assert isinstance(q._BM25_CACHE, dict)

    q._ARTIFACTS_CACHE[("k", "m")] = ("model", "index", [])
    q._BM25_CACHE["k"] = "bm25"
    q.clear_caches()
    assert q._ARTIFACTS_CACHE == {}
    assert q._BM25_CACHE == {}
