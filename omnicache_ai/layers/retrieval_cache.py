"""Retrieval cache layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager
    from omnicache_ai.core.serializer import Serializer


class RetrievalCache:
    """Cache layer for retriever results (e.g. RAG document chunks).

    Key discriminators: query text, retriever ID, and top_k count.
    This ensures that the same query with different top_k values produces
    different cache entries.

    Args:
        manager: Underlying CacheManager instance.
        serializer: Serializer for encoding/decoding values (default: pickle).
    """

    def __init__(
        self,
        manager: "CacheManager",
        serializer: "Serializer | None" = None,
    ) -> None:
        self._manager = manager
        self._serializer = serializer or DEFAULT_SERIALIZER

    def get(
        self,
        query: str,
        retriever_id: str = "default",
        top_k: int = 5,
    ) -> list[Any] | None:
        """Return cached retrieval results, or None on miss."""
        key = self._manager.key_builder.build(
            "retrieval", query, extra={"retriever": retriever_id, "top_k": top_k}
        )
        raw = self._manager.get(key)
        return cast(list[Any], self._serializer.loads(raw)) if raw is not None else None

    def set(
        self,
        query: str,
        documents: list[Any],
        retriever_id: str = "default",
        top_k: int = 5,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Store retrieval results in the cache."""
        key = self._manager.key_builder.build(
            "retrieval", query, extra={"retriever": retriever_id, "top_k": top_k}
        )
        self._manager.set(
            key,
            self._serializer.dumps(documents),
            ttl=ttl,
            cache_type="retrieval",
            tags=tags,
        )

    def get_or_retrieve(
        self,
        query: str,
        retrieve_fn: Callable[[str, int], list[Any]],
        retriever_id: str = "default",
        top_k: int = 5,
        ttl: int | None = None,
    ) -> list[Any]:
        """Return cached documents or call retrieve_fn, cache, and return."""
        cached = self.get(query, retriever_id, top_k)
        if cached is not None:
            return cached
        docs = retrieve_fn(query, top_k)
        self.set(query, docs, retriever_id, top_k, ttl)
        return docs
