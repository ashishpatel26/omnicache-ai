"""Semantic cache layer — the core differentiator of omnicache-ai."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import numpy as np

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER

if TYPE_CHECKING:
    from omnicache_ai.backends.base import CacheBackend, VectorBackend
    from omnicache_ai.core.key_builder import CacheKeyBuilder
    from omnicache_ai.core.serializer import Serializer


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two 1D float32 vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class SemanticCache:
    """Two-tier cache: exact key match first, then vector similarity fallback.

    This is the core differentiator. Semantically equivalent queries that
    differ in wording (e.g. "What's the capital of France?" vs "Capital of
    France?") can be served from cache without a model call.

    Lookup flow:
        1. Build exact key from query text.
        2. Check ``exact_backend`` — return on hit.
        3. Embed query using ``embed_fn``.
        4. Search ``vector_backend`` for nearest neighbor.
        5. If cosine similarity >= ``threshold``, return stored value.
        6. Return None (full miss).

    Storage flow:
        1. Build exact key and store in ``exact_backend``.
        2. Embed query and add (vector, key) to ``vector_backend``.

    Args:
        exact_backend: Backend for exact-match key-value lookups.
        vector_backend: Backend for approximate nearest-neighbour search.
        embed_fn: Callable that converts a query string to a float32 numpy array.
        threshold: Minimum cosine similarity to accept a semantic match (default: 0.95).
        key_builder: Optional key builder; if None, a default is created.
        serializer: Serializer for encoding/decoding values (default: pickle).
    """

    def __init__(
        self,
        exact_backend: "CacheBackend",
        vector_backend: "VectorBackend",
        embed_fn: Callable[[str], np.ndarray],
        threshold: float = 0.95,
        key_builder: "CacheKeyBuilder | None" = None,
        serializer: "Serializer | None" = None,
    ) -> None:
        from omnicache_ai.core.key_builder import CacheKeyBuilder

        self._exact = exact_backend
        self._vector = vector_backend
        self._embed_fn = embed_fn
        self._threshold = threshold
        self._kb = key_builder or CacheKeyBuilder()
        self._serializer = serializer or DEFAULT_SERIALIZER

    def get(self, query: str) -> Any | None:
        """Retrieve value using exact then semantic lookup."""
        key = self._kb.build("response", query)

        # 1. Exact hit
        raw = self._exact.get(key)
        if raw is not None:
            return self._serializer.loads(raw)

        # 2. Semantic hit
        vector = self._embed_fn(query).astype(np.float32)
        results = self._vector.search(vector, top_k=1)
        if results:
            best_key, score = results[0]
            if score >= self._threshold:
                stored_raw = self._exact.get(best_key)
                if stored_raw is not None:
                    return self._serializer.loads(stored_raw)

        return None

    def set(self, query: str, value: Any, ttl: int | None = None) -> None:
        """Store value with exact and vector indexing."""
        key = self._kb.build("response", query)
        payload = self._serializer.dumps(value)
        self._exact.set(key, payload, ttl)
        vector = self._embed_fn(query).astype(np.float32)
        self._vector.add(key, vector, {"value": value})

    def delete(self, query: str) -> None:
        """Remove a cached query from both backends."""
        key = self._kb.build("response", query)
        self._exact.delete(key)
        self._vector.delete(key)

    def clear(self) -> None:
        """Flush both backends."""
        self._exact.clear()
        self._vector.clear()
