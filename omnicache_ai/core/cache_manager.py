"""Central cache orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from omnicache_ai.backends.base import CacheBackend, VectorBackend
from omnicache_ai.core.compressor import DEFAULT_COMPRESSOR, Compressor
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder
from omnicache_ai.core.metrics import CacheMetrics
from omnicache_ai.core.policies import EvictionPolicy, TTLPolicy

if TYPE_CHECKING:
    from omnicache_ai.config.settings import OmnicacheSettings


class CacheManager:
    """Central orchestrator wiring backend, key builder, TTL policy, and vector backend.

    Usage (simple)::

        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder

        manager = CacheManager(
            backend=InMemoryBackend(),
            key_builder=CacheKeyBuilder(),
        )
        manager.set("mykey", {"answer": 42}, ttl=60)
        value = manager.get("mykey")

    Usage (from settings)::

        from omnicache_ai import CacheManager, OmnicacheSettings

        manager = CacheManager.from_settings(OmnicacheSettings(backend="disk"))

    Args:
        backend: Primary key-value cache backend.
        key_builder: Key construction helper.
        ttl_policy: TTL rules per cache type (optional).
        vector_backend: Optional vector similarity backend for semantic search.
        invalidation_engine: Optional tag-based invalidation engine.
        semantic_threshold: Minimum cosine similarity for a semantic cache hit.
    """

    def __init__(
        self,
        backend: CacheBackend,
        key_builder: CacheKeyBuilder,
        ttl_policy: TTLPolicy | None = None,
        eviction_policy: EvictionPolicy | None = None,
        vector_backend: VectorBackend | None = None,
        invalidation_engine: InvalidationEngine | None = None,
        semantic_threshold: float = 0.95,
        compressor: Compressor | None = None,
    ) -> None:
        self._backend = backend
        self._key_builder = key_builder
        self._ttl_policy = ttl_policy or TTLPolicy()
        self._eviction_policy = eviction_policy
        self._vector_backend = vector_backend
        self._invalidation = invalidation_engine
        self._threshold = semantic_threshold
        self._compressor = compressor or DEFAULT_COMPRESSOR
        self._metrics = CacheMetrics()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self,
        key: str,
        semantic: bool = False,
        vector: np.ndarray | None = None,
    ) -> Any | None:
        """Retrieve a cached value.

        Args:
            key: Cache key (pre-built or raw — used for exact lookup).
            semantic: If True and vector_backend is configured, attempt a
                      nearest-neighbour lookup instead of an exact hit.
            vector: Query embedding for semantic lookup (required when semantic=True).

        Returns:
            Cached value or None on miss.
        """
        if semantic and self._vector_backend is not None and vector is not None:
            results = self._vector_backend.search(vector, top_k=1)
            if results:
                best_key, score = results[0]
                if score >= self._threshold:
                    value = self._backend.get(best_key)
                    if value is not None:
                        self._metrics.record_hit()
                        return value
            self._metrics.record_miss()
            return None
        value = self._backend.get(key)
        if value is not None:
            self._metrics.record_hit()
            return self._compressor.decompress(value) if isinstance(value, bytes) else value
        self._metrics.record_miss()
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        vector: np.ndarray | None = None,
        tags: list[str] | None = None,
        cache_type: str = "response",
    ) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to store.
            ttl: Time-to-live in seconds. Falls back to TTLPolicy default.
            vector: If provided, also indexes the vector in vector_backend.
            tags: Invalidation tags to associate with this key.
            cache_type: Used to resolve TTL from TTLPolicy when ttl is None.
        """
        effective_ttl = ttl if ttl is not None else self._ttl_policy.ttl_for(cache_type)
        stored = self._compressor.compress(value) if isinstance(value, bytes) else value
        self._backend.set(key, stored, effective_ttl)
        self._metrics.record_set()
        if vector is not None and self._vector_backend is not None:
            self._vector_backend.add(key, vector, {"value": value})
        if tags and self._invalidation is not None:
            self._invalidation.register(key, tags)

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        self._backend.delete(key)
        if self._vector_backend is not None:
            self._vector_backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return self._backend.exists(key)

    def invalidate(self, tag: str) -> int:
        """Invalidate all keys associated with a tag.

        Returns:
            Number of keys removed.
        """
        if self._invalidation is None:
            return 0
        return self._invalidation.invalidate_tag(tag, self._backend)

    def clear(self) -> None:
        """Flush all cache entries."""
        self._backend.clear()
        if self._vector_backend is not None:
            self._vector_backend.clear()

    def close(self) -> None:
        """Release all resources."""
        self._backend.close()
        if self._vector_backend is not None:
            self._vector_backend.close()

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def key_builder(self) -> CacheKeyBuilder:
        return self._key_builder

    @property
    def ttl_policy(self) -> TTLPolicy:
        return self._ttl_policy

    def for_tenant(self, tenant_id: str) -> "CacheManager":
        """Return a scoped CacheManager that prefixes all keys with tenant_id.

        All cache operations are isolated per tenant while sharing the same
        backend pool, invalidation engine, and TTL policy.

        Usage::

            manager = CacheManager.from_settings(settings)
            tenant_cache = manager.for_tenant("customer-42")
            tenant_cache.set("key", value)
            # stored as: omnicache:customer-42:resp:<hash>

        Args:
            tenant_id: Tenant identifier appended to the namespace.

        Returns:
            A new CacheManager scoped to this tenant.
        """
        scoped_kb = CacheKeyBuilder(
            namespace=f"{self._key_builder._namespace}:{tenant_id}",
            algo=self._key_builder._algo,
        )
        scoped = CacheManager(
            backend=self._backend,
            key_builder=scoped_kb,
            ttl_policy=self._ttl_policy,
            eviction_policy=self._eviction_policy,
            vector_backend=self._vector_backend,
            invalidation_engine=self._invalidation,
            semantic_threshold=self._threshold,
            compressor=self._compressor,
        )
        scoped._metrics = self._metrics
        return scoped

    @property
    def metrics(self) -> CacheMetrics:
        """Live hit/miss/eviction counters."""
        return self._metrics

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_settings(cls, settings: "OmnicacheSettings") -> "CacheManager":
        """Construct a CacheManager from an OmnicacheSettings instance.

        Selects the correct backend and wires everything together.
        """
        from omnicache_ai.backends.memory_backend import InMemoryBackend
        from omnicache_ai.backends.disk_backend import DiskBackend

        metrics = CacheMetrics()
        eviction_policy = EvictionPolicy(
            strategy=getattr(settings, "eviction_strategy", "lru"),
            max_entries=settings.max_memory_entries,
        )

        if settings.backend == "redis":
            from omnicache_ai.backends.redis_backend import RedisBackend

            backend: CacheBackend = RedisBackend(url=settings.redis_url)
        elif settings.backend == "disk":
            backend = DiskBackend(directory=settings.disk_path)
        else:
            backend = InMemoryBackend(
                max_size=settings.max_memory_entries,
                eviction_policy=eviction_policy,
                on_evict=lambda _key: metrics.record_eviction(),
            )

        vector_backend: VectorBackend | None = None
        if settings.vector_backend == "faiss":
            from omnicache_ai.backends.vector_backend import FAISSBackend

            vector_backend = FAISSBackend(dim=settings.embedding_dim)
        elif settings.vector_backend == "chroma":
            from omnicache_ai.backends.vector_backend import ChromaBackend

            vector_backend = ChromaBackend()

        key_builder = CacheKeyBuilder(
            namespace=settings.namespace,
            algo=settings.key_hash_algo,
        )
        ttl_policy = TTLPolicy.from_settings(settings)

        tag_store = InMemoryBackend()
        invalidation_engine = InvalidationEngine(tag_store=tag_store)

        manager = cls(
            backend=backend,
            key_builder=key_builder,
            ttl_policy=ttl_policy,
            eviction_policy=eviction_policy,
            vector_backend=vector_backend,
            invalidation_engine=invalidation_engine,
            semantic_threshold=settings.semantic_threshold,
        )
        manager._metrics = metrics
        return manager
