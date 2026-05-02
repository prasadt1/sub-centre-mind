from __future__ import annotations

# Must run before Hugging Face / tokenizers import: avoids fork/thread issues on macOS
# and reduces OpenMP clashes between PyTorch, numpy, and faiss (segfault 11 on Apple Silicon).
import os
import pickle
import sys
from pathlib import Path

_SRC_ROOT = str(Path(__file__).resolve().parent.parent)
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import json
from dataclasses import asdict, dataclass
from typing import Iterable, List, Tuple

from rag.text_tokenize import tokenize_bm25

import torch

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "1")))

import faiss  # type: ignore
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class Chunk:
    id: str
    source_file: str
    page: int
    text: str


def _iter_pdf_pages(pdf_path: Path) -> Iterable[Tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())
        if text:
            yield i, text


def _chunk_text(text: str, *, max_chars: int = 1200, overlap_chars: int = 150) -> List[str]:
    # Simple, deterministic chunker. We can replace with token-based chunking later if needed.
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks


def build_index(
    *,
    corpus_dir: Path,
    out_dir: Path,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> None:
    pdfs = sorted([p for p in corpus_dir.glob("*.pdf") if p.is_file()])
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in {corpus_dir}")

    # Force CPU: MPS / default device selection has triggered segfault 11 after HF downloads on some Macs.
    model = SentenceTransformer(embedding_model, device="cpu")

    chunks: List[Chunk] = []
    for pdf in pdfs:
        for page_num, page_text in _iter_pdf_pages(pdf):
            for j, chunk_text in enumerate(_chunk_text(page_text, max_chars=max_chars, overlap_chars=overlap_chars)):
                chunk_id = f"{pdf.name}::p{page_num}::c{j}"
                chunks.append(
                    Chunk(id=chunk_id, source_file=pdf.name, page=page_num, text=chunk_text)
                )

    texts = [c.text for c in chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=int(os.environ.get("SCM_ENCODE_BATCH", "32")),
        device="cpu",
    )
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype("float32"))

    out_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out_dir / "faiss.index"))
    with (out_dir / "chunks.json").open("w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in chunks], f, ensure_ascii=False, indent=2)

    try:
        from rank_bm25 import BM25Okapi

        tok_corpus = [tokenize_bm25(t) for t in texts]
        bm25 = BM25Okapi(tok_corpus)
        with (out_dir / "bm25.pkl").open("wb") as f:
            pickle.dump(bm25, f)
        bm25_built = True
    except ImportError:
        bm25_built = False

    meta = {
        "embedding_model": embedding_model,
        "chunking": {"max_chars": max_chars, "overlap_chars": overlap_chars},
        "num_pdfs": len(pdfs),
        "num_chunks": len(chunks),
        "bm25_hybrid_index": bm25_built,
    }
    with (out_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def main() -> None:
    corpus_dir = Path(os.environ.get("SCM_CORPUS_DIR", "data/health-corpus"))
    out_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    max_chars = int(os.environ.get("SCM_CHUNK_MAX_CHARS", "900"))
    overlap_chars = int(os.environ.get("SCM_CHUNK_OVERLAP", "120"))
    build_index(
        corpus_dir=corpus_dir,
        out_dir=out_dir,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )
    print(f"Built index at {out_dir} from {corpus_dir}")


if __name__ == "__main__":
    main()

