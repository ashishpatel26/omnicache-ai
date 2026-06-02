"""FAISS document index with OmniCache-AI RetrievalCache.

FAISS index is created lazily on first ingest — dim auto-detected
from the first embedding call (no hardcoded dimension needed).
"""

from __future__ import annotations

import json
import pickle
import time
from pathlib import Path

import numpy as np
from rich.console import Console

from omnicache_ai.layers.retrieval_cache import RetrievalCache

from .embedder import CachedEmbedder

console = Console()

_CACHE_DIR = Path.home() / ".cache" / "rag-openrouter"
_INDEX_PATH = _CACHE_DIR / "faiss_index.pkl"
_DOCS_PATH = _CACHE_DIR / "documents.json"
_DIM_PATH = _CACHE_DIR / "embed_dim.json"

RETRIEVER_ID = "faiss-openrouter"


def _chunk(texts: list[str], size: int = 400) -> list[str]:
    chunks: list[str] = []
    for text in texts:
        words = text.split()
        for i in range(0, len(words), size):
            chunk = " ".join(words[i : i + size])
            if chunk.strip():
                chunks.append(chunk)
    return chunks


class DocumentIndex:
    """FAISS document store with cached retrieval."""

    def __init__(self, embedder: CachedEmbedder, retrieval_cache: RetrievalCache) -> None:
        try:
            import faiss as _faiss

            self._faiss = _faiss
        except ImportError as e:
            raise ImportError("Install faiss-cpu: pip install 'omnicache-ai[vector-faiss]'") from e

        self._embedder = embedder
        self._cache = retrieval_cache
        self._index = None  # built lazily on first ingest
        self._documents: list[str] = []
        self._dim: int | None = None
        self._load_persisted()

    # ------------------------------------------------------------------

    def _load_persisted(self) -> None:
        if _INDEX_PATH.exists() and _DOCS_PATH.exists() and _DIM_PATH.exists():
            with open(_INDEX_PATH, "rb") as f:
                self._index = pickle.load(f)  # noqa: S301
            with open(_DOCS_PATH) as f:
                self._documents = json.load(f)
            with open(_DIM_PATH) as f:
                self._dim = json.load(f)["dim"]
            # sync embedder dim so it knows after load
            self._embedder._dim = self._dim  # noqa: SLF001
            console.print(
                f"  [dim]Loaded {len(self._documents)} docs (dim={self._dim}) from disk[/dim]"
            )

    def _persist(self) -> None:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_INDEX_PATH, "wb") as f:
            pickle.dump(self._index, f)
        with open(_DOCS_PATH, "w") as f:
            json.dump(self._documents, f)
        with open(_DIM_PATH, "w") as f:
            json.dump({"dim": self._dim}, f)

    def is_empty(self) -> bool:
        return len(self._documents) == 0

    # ------------------------------------------------------------------

    def ingest(self, texts: list[str]) -> int:
        chunks = _chunk(texts)
        console.print(f"\n[bold]Embedding {len(chunks)} chunks...[/bold]")

        vecs = self._embedder.embed_batch(chunks)

        # Build FAISS index lazily — dim known after first embed
        if self._index is None:
            self._dim = self._embedder.dim
            self._index = self._faiss.IndexFlatIP(self._dim)

        matrix = np.vstack(vecs)
        self._index.add(matrix)
        self._documents.extend(chunks)
        self._persist()
        console.print(f"  [green]OK[/green] {len(chunks)} chunks indexed -> persisted")
        return len(chunks)

    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = 4) -> list[str]:
        cached = self._cache.get(query, retriever_id=RETRIEVER_ID, top_k=top_k)
        if cached is not None:
            console.print(f"  [green]RETRIEVAL HIT[/green] '{query[:70]}'")
            return cached

        t0 = time.perf_counter()
        qvec = self._embedder.embed(query)

        assert self._index is not None, "Call ingest() first"
        _, indices = self._index.search(qvec.reshape(1, -1), top_k)
        docs = [self._documents[i] for i in indices[0] if 0 <= i < len(self._documents)]
        elapsed = time.perf_counter() - t0

        # RetrievalCache.set(query, documents, retriever_id, top_k)
        self._cache.set(query, docs, retriever_id=RETRIEVER_ID, top_k=top_k)
        console.print(
            f"  [yellow]RETRIEVAL MISS[/yellow] '{query[:70]}' -> {elapsed:.3f}s ({len(docs)} docs)"
        )
        return docs
