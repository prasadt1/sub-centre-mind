from __future__ import annotations

import json
import os
import pickle
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

# Support `python src/rag/query.py` from repo root (no package context).
_SRC_DIR = str(Path(__file__).resolve().parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "1")))

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer

from rag.intent import SupplementIntent, adjust_score, detect_supplement_intent, intent_label
from rag.text_tokenize import tokenize_bm25


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source_file: str
    page: int
    score: float  # reranked score used for ordering (≤ ~1.35 × cosine when intent rerank on)
    text: str
    semantic_score: float  # raw cosine similarity from FAISS


def _load_chunks(index_dir: Path) -> list[dict]:
    chunks_path = index_dir / "chunks.json"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing chunks file: {chunks_path}")
    return json.loads(chunks_path.read_text(encoding="utf-8"))


def _load_bm25(index_dir: Path):
    p = index_dir / "bm25.pkl"
    if not p.is_file():
        return None
    with p.open("rb") as f:
        return pickle.load(f)


# Cache heavy artifacts so subsequent retrieve() calls don't re-load
# SentenceTransformer / FAISS / chunks / BM25 from disk.
_ARTIFACTS_CACHE: Dict[tuple, tuple] = {}
_BM25_CACHE: Dict[str, object] = {}


def _get_artifacts(index_dir: Path, embedding_model: str):
    key = (str(Path(index_dir).resolve()), embedding_model)
    cached = _ARTIFACTS_CACHE.get(key)
    if cached is not None:
        return cached
    model = SentenceTransformer(embedding_model, device="cpu")
    index = faiss.read_index(str(index_dir / "faiss.index"))
    chunks = _load_chunks(index_dir)
    _ARTIFACTS_CACHE[key] = (model, index, chunks)
    return _ARTIFACTS_CACHE[key]


def _get_bm25_cached(index_dir: Path):
    key = str(Path(index_dir).resolve())
    if key in _BM25_CACHE:
        return _BM25_CACHE[key]
    bm25 = _load_bm25(index_dir)
    _BM25_CACHE[key] = bm25
    return bm25


def clear_caches() -> None:
    """Drop cached embedder/index/BM25 (used by tests)."""
    _ARTIFACTS_CACHE.clear()
    _BM25_CACHE.clear()


def _semantic_sim_for_idx(index, idx: int, q_emb_row: np.ndarray) -> float:
    vec = np.asarray(index.reconstruct(int(idx)), dtype=np.float32)
    return float(np.dot(vec, q_emb_row.astype(np.float32)))


def _reciprocal_rank_fusion(
    *,
    sem_ids: np.ndarray,
    bm25_scores: np.ndarray,
    rrf_k: int,
    bm25_depth: int,
) -> Dict[int, float]:
    """RRF scores for chunk indices; higher is better."""
    scores: Dict[int, float] = defaultdict(float)
    for rank, idx in enumerate(sem_ids.tolist(), start=1):
        if idx < 0:
            continue
        scores[int(idx)] += 1.0 / (rrf_k + rank)
    order = np.argsort(-bm25_scores)
    for rank in range(1, min(bm25_depth, len(order)) + 1):
        idx = int(order[rank - 1])
        scores[idx] += 1.0 / (rrf_k + rank)
    return scores


def retrieve(
    query: str,
    *,
    index_dir: Path,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    top_k: int = 5,
    intent_rerank: bool | None = None,
) -> List[RetrievedChunk]:
    if not query.strip():
        return []

    index_path = index_dir / "faiss.index"
    if not index_path.exists():
        raise FileNotFoundError(f"Missing FAISS index: {index_path}")

    use_rerank = (
        intent_rerank
        if intent_rerank is not None
        else os.environ.get("SCM_INTENT_RERANK", "1").strip().lower() not in ("0", "false", "no")
    )

    model, index, chunks = _get_artifacts(index_dir, embedding_model)

    ntotal = int(index.ntotal)
    intent = detect_supplement_intent(query) if use_rerank else SupplementIntent.GENERIC

    use_hybrid = os.environ.get("SCM_HYBRID", "1").strip().lower() not in ("0", "false", "no")
    bm25 = _get_bm25_cached(index_dir) if use_hybrid else None

    # Larger pool so rerank can rescue strong cue chunks (e.g. MCP IFA bullets) that embed slightly lower.
    default_pool = min(ntotal, max(top_k * 10, 48))
    candidate_k = min(
        ntotal,
        max(top_k, int(os.environ.get("SCM_RETRIEVE_CANDIDATES", str(default_pool)))),
    )

    q_emb = model.encode([query], normalize_embeddings=True, device="cpu").astype("float32")
    scores, ids = index.search(q_emb, candidate_k)
    q_row = q_emb[0]

    sem_ids = ids[0]
    idx_to_sim: Dict[int, float] = {}
    for sim, idx in zip(scores[0].tolist(), sem_ids.tolist()):
        if idx >= 0:
            idx_to_sim[int(idx)] = float(sim)

    ranked: List[tuple[float, float, dict]] = []

    if bm25 is not None:
        q_tokens = tokenize_bm25(query)
        bm25_scores = np.asarray(bm25.get_scores(q_tokens), dtype=np.float64)
        rrf_k = int(os.environ.get("SCM_RRF_K", "60"))
        bm25_depth = int(os.environ.get("SCM_BM25_DEPTH", "50"))
        merge_cap = int(os.environ.get("SCM_HYBRID_MERGE_CAP", "64"))
        rrf_map = _reciprocal_rank_fusion(
            sem_ids=sem_ids,
            bm25_scores=bm25_scores,
            rrf_k=rrf_k,
            bm25_depth=min(bm25_depth, ntotal),
        )
        # Prefer chunks that appear in either semantic shortlist or strong BM25 hits.
        hybrid_candidates = sorted(rrf_map.keys(), key=lambda i: rrf_map[i], reverse=True)[:merge_cap]

        for idx in hybrid_candidates:
            c = chunks[idx]
            sim_f = idx_to_sim.get(idx)
            if sim_f is None:
                sim_f = _semantic_sim_for_idx(index, idx, q_row)
            if use_rerank:
                adj = adjust_score(sim_f, intent=intent, chunk_text=c["text"], source_file=c["source_file"])
            else:
                adj = sim_f
            ranked.append((adj, sim_f, c))
        ranked.sort(key=lambda x: x[0], reverse=True)
    else:
        for sim, idx in zip(scores[0].tolist(), sem_ids.tolist()):
            if idx < 0:
                continue
            c = chunks[idx]
            sim_f = float(sim)
            if use_rerank:
                adj = adjust_score(sim_f, intent=intent, chunk_text=c["text"], source_file=c["source_file"])
            else:
                adj = sim_f
            ranked.append((adj, sim_f, c))
        ranked.sort(key=lambda x: x[0], reverse=True)

    dedup_pages = os.environ.get("SCM_DEDUP_BY_PAGE", "1").strip().lower() not in ("0", "false", "no")
    results = _pick_top_k(ranked, top_k=top_k, dedup_pages=dedup_pages)
    return results


def _pick_top_k(
    ranked: List[tuple[float, float, dict]],
    *,
    top_k: int,
    dedup_pages: bool,
) -> List[RetrievedChunk]:
    """ranked: list of (adjusted_score, semantic_score, chunk_dict) sorted by adjusted desc."""
    out: List[RetrievedChunk] = []
    seen_page: set[tuple[str, int]] = set()
    selected_ids: set[str] = set()

    def append_from(pool: List[tuple[float, float, dict]], use_dedup: bool) -> None:
        for adj, sim_f, c in pool:
            if len(out) >= top_k:
                return
            cid = c["id"]
            if cid in selected_ids:
                continue
            key = (c["source_file"], int(c["page"]))
            if use_dedup and key in seen_page:
                continue
            if use_dedup:
                seen_page.add(key)
            selected_ids.add(cid)
            out.append(
                RetrievedChunk(
                    chunk_id=c["id"],
                    source_file=c["source_file"],
                    page=int(c["page"]),
                    score=float(adj),
                    text=c["text"],
                    semantic_score=float(sim_f),
                )
            )

    if dedup_pages:
        append_from(ranked, True)
        if len(out) < top_k:
            append_from(ranked, False)
    else:
        append_from(ranked, False)

    return out[:top_k]


def format_citations(chunks: Sequence[RetrievedChunk]) -> str:
    # Keep citations lightweight: filename + page + rerank vs raw similarity.
    lines = []
    for i, c in enumerate(chunks, start=1):
        if abs(c.score - c.semantic_score) > 1e-4:
            lines.append(
                f"[{i}] {c.source_file} p.{c.page} "
                f"(rank={c.score:.3f} sim={c.semantic_score:.3f})"
            )
        else:
            lines.append(f"[{i}] {c.source_file} p.{c.page} (sim={c.semantic_score:.3f})")
    return "\n".join(lines)


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get("SCM_QUERY", "IFA tablet dose for pregnant women per MoHFW guidelines?")
    intent = detect_supplement_intent(q)
    if os.environ.get("SCM_INTENT_RERANK", "1").strip().lower() not in ("0", "false", "no"):
        print(f"(intent: {intent_label(intent)})", flush=True)
    chunks = retrieve(q, index_dir=index_dir, top_k=5)
    print(format_citations(chunks))
    print()
    if chunks:
        print(chunks[0].text[:500])


if __name__ == "__main__":
    main()

