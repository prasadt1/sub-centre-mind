from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source_file: str
    page: int
    score: float
    text: str


def _load_chunks(index_dir: Path) -> list[dict]:
    chunks_path = index_dir / "chunks.json"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing chunks file: {chunks_path}")
    return json.loads(chunks_path.read_text(encoding="utf-8"))


def retrieve(
    query: str,
    *,
    index_dir: Path,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    top_k: int = 5,
) -> List[RetrievedChunk]:
    if not query.strip():
        return []

    index_path = index_dir / "faiss.index"
    if not index_path.exists():
        raise FileNotFoundError(f"Missing FAISS index: {index_path}")

    model = SentenceTransformer(embedding_model)
    index = faiss.read_index(str(index_path))
    chunks = _load_chunks(index_dir)

    q_emb = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(q_emb, top_k)

    results: List[RetrievedChunk] = []
    for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
        if idx < 0:
            continue
        c = chunks[idx]
        results.append(
            RetrievedChunk(
                chunk_id=c["id"],
                source_file=c["source_file"],
                page=int(c["page"]),
                score=float(score),
                text=c["text"],
            )
        )
    return results


def format_citations(chunks: Sequence[RetrievedChunk]) -> str:
    # Keep citations lightweight: filename + page.
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(f"[{i}] {c.source_file} p.{c.page} (score={c.score:.3f})")
    return "\n".join(lines)


def main() -> None:
    index_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    q = os.environ.get("SCM_QUERY", "IFA tablet dose for pregnant women per MoHFW guidelines?")
    chunks = retrieve(q, index_dir=index_dir, top_k=5)
    print(format_citations(chunks))
    print()
    if chunks:
        print(chunks[0].text[:500])


if __name__ == "__main__":
    main()

