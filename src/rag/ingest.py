from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

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

    model = SentenceTransformer(embedding_model)

    chunks: List[Chunk] = []
    for pdf in pdfs:
        for page_num, page_text in _iter_pdf_pages(pdf):
            for j, chunk_text in enumerate(_chunk_text(page_text, max_chars=max_chars, overlap_chars=overlap_chars)):
                chunk_id = f"{pdf.name}::p{page_num}::c{j}"
                chunks.append(
                    Chunk(id=chunk_id, source_file=pdf.name, page=page_num, text=chunk_text)
                )

    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype("float32"))

    out_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out_dir / "faiss.index"))
    with (out_dir / "chunks.json").open("w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in chunks], f, ensure_ascii=False, indent=2)

    meta = {
        "embedding_model": embedding_model,
        "chunking": {"max_chars": max_chars, "overlap_chars": overlap_chars},
        "num_pdfs": len(pdfs),
        "num_chunks": len(chunks),
    }
    with (out_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def main() -> None:
    corpus_dir = Path(os.environ.get("SCM_CORPUS_DIR", "data/health-corpus"))
    out_dir = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
    build_index(corpus_dir=corpus_dir, out_dir=out_dir)
    print(f"Built index at {out_dir} from {corpus_dir}")


if __name__ == "__main__":
    main()

