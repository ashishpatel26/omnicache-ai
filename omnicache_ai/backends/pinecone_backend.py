"""Pinecone vector backend for semantic caching."""

from __future__ import annotations

import uuid
from typing import Any

import numpy as np

try:
    from pinecone import Pinecone as _Pinecone  # type: ignore[import-untyped]
    from pinecone import ServerlessSpec  # type: ignore[import-untyped]

    _PINECONE_AVAILABLE = True
except ImportError:
    _Pinecone = None  # type: ignore[assignment]
    ServerlessSpec = None  # type: ignore[assignment]
    _PINECONE_AVAILABLE = False


class PineconeBackend:
    """Pinecone vector similarity backend for semantic caching.

    Uses a Pinecone index for approximate nearest-neighbour search.
    Stores the cache key as vector metadata for retrieval on hit.

    Usage::

        from omnicache_ai.backends.pinecone_backend import PineconeBackend
        from omnicache_ai.backends.memory_backend import InMemoryBackend
        from omnicache_ai.layers.semantic_cache import SemanticCache

        vector = PineconeBackend(
            api_key="pc-...",
            index_name="omnicache-semantic",
            dim=1536,
        )
        exact = InMemoryBackend()
        cache = SemanticCache(exact, vector, embed_fn=my_embed)

    Install with: pip install 'omnicache-ai[vector-pinecone]'

    Args:
        api_key: Pinecone API key.
        index_name: Name of the Pinecone index to use (created if absent).
        dim: Embedding dimension (must match the index).
        cloud: Cloud provider for new index creation (default: "aws").
        region: Region for new index creation (default: "us-east-1").
        top_k: Number of candidates to fetch on search (default: 1).
    """

    def __init__(
        self,
        api_key: str,
        index_name: str,
        dim: int,
        cloud: str = "aws",
        region: str = "us-east-1",
        top_k: int = 1,
    ) -> None:
        if not _PINECONE_AVAILABLE:
            raise ImportError(
                "PineconeBackend requires 'pinecone-client'. "
                "Install with: pip install 'omnicache-ai[vector-pinecone]'"
            )
        self._top_k = top_k
        self._dim = dim

        pc = _Pinecone(api_key=api_key)
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=dim,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
        self._index = pc.Index(index_name)

    def add(self, key: str, vector: np.ndarray, metadata: dict[str, Any]) -> None:
        """Index a vector with its cache key stored as metadata."""
        v = vector.astype(np.float32).tolist()
        self._index.upsert(
            vectors=[
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                    "values": v,
                    "metadata": {"key": key},
                }
            ]
        )

    def search(self, vector: np.ndarray, top_k: int = 1) -> list[tuple[str, float]]:
        """Return (key, score) pairs for the nearest neighbours."""
        v = vector.astype(np.float32).tolist()
        results = self._index.query(vector=v, top_k=top_k or self._top_k, include_metadata=True)
        matches = results.get("matches") or []
        return [(m["metadata"]["key"], float(m["score"])) for m in matches if "metadata" in m]

    def delete(self, key: str) -> None:
        """Remove a vector by its cache key."""
        self._index.delete(ids=[str(uuid.uuid5(uuid.NAMESPACE_URL, key))])

    def clear(self) -> None:
        """Delete all vectors in the index."""
        self._index.delete(delete_all=True)

    def close(self) -> None:
        pass
