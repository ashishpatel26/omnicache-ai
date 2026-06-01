"""Vector similarity backends: FAISSBackend and ChromaBackend (both optional)."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import faiss as _faiss

    _FAISS_AVAILABLE = True
except ImportError:
    _faiss = None  # type: ignore[assignment]
    _FAISS_AVAILABLE = False

try:
    import chromadb as _chromadb

    _CHROMA_AVAILABLE = True
except ImportError:
    _chromadb = None  # type: ignore[assignment]
    _CHROMA_AVAILABLE = False


class FAISSBackend:
    """FAISS-based vector similarity backend.

    Uses IndexIDMap2 wrapping IndexFlatIP — supports both cosine similarity
    (on L2-normalised vectors) and true in-place deletion via FAISS native IDs.

    Install with: pip install 'omnicache-ai[vector-faiss]'

    Args:
        dim: Embedding dimension.
        normalize: If True, L2-normalise all vectors before indexing/searching.
    """

    def __init__(self, dim: int, normalize: bool = True) -> None:
        if not _FAISS_AVAILABLE:
            raise ImportError(
                "FAISSBackend requires 'faiss-cpu'. "
                "Install with: pip install 'omnicache-ai[vector-faiss]'"
            )
        self._dim = dim
        self._normalize = normalize
        # IndexIDMap2 wraps a flat index and supports remove_ids()
        self._index = _faiss.IndexIDMap2(_faiss.IndexFlatIP(dim))  # type: ignore[union-attr]
        self._id_to_key: dict[int, str] = {}
        self._key_to_id: dict[str, int] = {}
        self._id_to_value: dict[int, Any] = {}
        self._next_id: int = 0

    def _prep(self, vector: np.ndarray) -> np.ndarray:
        v = vector.astype(np.float32).reshape(1, -1)
        if self._normalize:
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
        return v

    def add(self, key: str, vector: np.ndarray, metadata: dict[str, Any]) -> None:
        if key in self._key_to_id:
            self.delete(key)
        v = self._prep(vector)
        faiss_id = self._next_id
        self._next_id += 1
        self._index.add_with_ids(v, np.array([faiss_id], dtype=np.int64))
        self._id_to_key[faiss_id] = key
        self._key_to_id[key] = faiss_id
        self._id_to_value[faiss_id] = metadata.get("value")

    def search(self, vector: np.ndarray, top_k: int = 1) -> list[tuple[str, float]]:
        if self._index.ntotal == 0:
            return []
        v = self._prep(vector)
        k = min(top_k, self._index.ntotal)
        scores, ids = self._index.search(v, k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            key = self._id_to_key.get(int(idx))
            if key is not None:
                results.append((key, float(score)))
        return results

    def get_value(self, key: str) -> Any | None:
        faiss_id = self._key_to_id.get(key)
        return self._id_to_value.get(faiss_id) if faiss_id is not None else None

    def delete(self, key: str) -> None:
        faiss_id = self._key_to_id.pop(key, None)
        if faiss_id is not None:
            self._index.remove_ids(np.array([faiss_id], dtype=np.int64))
            self._id_to_key.pop(faiss_id, None)
            self._id_to_value.pop(faiss_id, None)

    def clear(self) -> None:
        self._index.reset()
        self._id_to_key.clear()
        self._key_to_id.clear()
        self._id_to_value.clear()
        self._next_id = 0

    def close(self) -> None:
        self.clear()


class ChromaBackend:
    """ChromaDB-based vector similarity backend.

    Handles both vectors and metadata natively. Supports persistence.

    Install with: pip install 'omnicache-ai[vector-chroma]'

    Args:
        collection_name: Name of the Chroma collection to use.
        persist_directory: If set, data is persisted to disk at this path.
    """

    def __init__(
        self,
        collection_name: str = "omnicache",
        persist_directory: str | None = None,
    ) -> None:
        if not _CHROMA_AVAILABLE:
            raise ImportError(
                "ChromaBackend requires 'chromadb'. "
                "Install with: pip install 'omnicache-ai[vector-chroma]'"
            )
        if persist_directory:
            client = _chromadb.PersistentClient(path=persist_directory)
        else:
            client = _chromadb.EphemeralClient()
        self._collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, key: str, vector: np.ndarray, metadata: dict[str, Any]) -> None:
        self._collection.upsert(
            ids=[key],
            embeddings=[vector.astype(np.float32).tolist()],
            metadatas=[{k: str(v) for k, v in metadata.items()}],
        )

    def search(self, vector: np.ndarray, top_k: int = 1) -> list[tuple[str, float]]:
        results = self._collection.query(
            query_embeddings=[vector.astype(np.float32).tolist()],
            n_results=top_k,
        )
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        # Chroma cosine distance → similarity: similarity = 1 - distance
        return [(id_, 1.0 - dist) for id_, dist in zip(ids, distances)]

    def get_value(self, key: str) -> Any | None:
        result = self._collection.get(ids=[key], include=["metadatas"])
        metadatas = result.get("metadatas", [])
        return metadatas[0].get("value") if metadatas else None

    def delete(self, key: str) -> None:
        self._collection.delete(ids=[key])

    def clear(self) -> None:
        self._collection.delete(where={"_id": {"$ne": ""}})

    def close(self) -> None:
        pass
