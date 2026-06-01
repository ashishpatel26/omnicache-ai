"""Tiered (multi-level) cache backend: fast L1 with persistent L2 fallback."""

from __future__ import annotations

from typing import Any

from omnicache_ai.backends.base import CacheBackend


class TieredBackend:
    """Two-level cache: check L1 (fast) first, fall back to L2 (persistent).

    On a miss in L1 but hit in L2, the value is promoted to L1 with a
    shorter TTL so subsequent reads stay fast.

    Typical setup: L1 = InMemoryBackend, L2 = RedisBackend or DiskBackend.

    Usage::

        from omnicache_ai import InMemoryBackend, CacheManager, CacheKeyBuilder
        from omnicache_ai.backends.redis_backend import RedisBackend
        from omnicache_ai.backends.tiered_backend import TieredBackend

        backend = TieredBackend(
            l1=InMemoryBackend(max_size=1000),
            l2=RedisBackend(url="redis://localhost:6379/0"),
            l1_ttl=300,  # 5-min local copy
        )
        manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())

    Args:
        l1: Fast primary backend (typically in-memory).
        l2: Slower persistent backend (Redis, disk).
        l1_ttl: TTL in seconds for values promoted from L2 → L1. None = no expiry.
    """

    def __init__(
        self,
        l1: CacheBackend,
        l2: CacheBackend,
        l1_ttl: int | None = 300,
    ) -> None:
        self._l1 = l1
        self._l2 = l2
        self._l1_ttl = l1_ttl

    def get(self, key: str) -> Any | None:
        value = self._l1.get(key)
        if value is not None:
            return value
        value = self._l2.get(key)
        if value is not None:
            self._l1.set(key, value, self._l1_ttl)
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        l1_ttl = min(self._l1_ttl, ttl) if (self._l1_ttl and ttl) else (self._l1_ttl or ttl)
        self._l1.set(key, value, l1_ttl)
        self._l2.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self._l1.delete(key)
        self._l2.delete(key)

    def exists(self, key: str) -> bool:
        return self._l1.exists(key) or self._l2.exists(key)

    def clear(self) -> None:
        self._l1.clear()
        self._l2.clear()

    def close(self) -> None:
        self._l1.close()
        self._l2.close()
