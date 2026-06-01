"""In-memory cache backend with LRU eviction and TTL support."""

from __future__ import annotations

import time
from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from omnicache_ai.core.policies import EvictionPolicy


class InMemoryBackend:
    """Thread-safe in-memory cache with LRU eviction and per-entry TTL.

    Uses an OrderedDict to maintain LRU order. When max_size is exceeded,
    the least-recently-used entry is evicted. TTL is tracked via
    time.monotonic() stored alongside each value.

    Args:
        max_size: Maximum number of entries before LRU eviction. Overridden by
                  eviction_policy.max_entries when an EvictionPolicy is supplied.
        eviction_policy: Optional policy object controlling strategy and limits.
        on_evict: Optional callback fired with the evicted key on each eviction.
    """

    def __init__(
        self,
        max_size: int = 10_000,
        eviction_policy: "EvictionPolicy | None" = None,
        on_evict: Callable[[str], None] | None = None,
    ) -> None:
        if eviction_policy is not None and eviction_policy.max_entries is not None:
            max_size = eviction_policy.max_entries
        self._store: OrderedDict[str, tuple[Any, float | None]] = OrderedDict()
        self._max_size = max_size
        self._eviction_policy = eviction_policy
        self._on_evict = on_evict
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            if expires_at is not None and time.monotonic() >= expires_at:
                del self._store[key]
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + ttl if ttl is not None else None
        strategy = "lru"
        if self._eviction_policy is not None:
            strategy = self._eviction_policy.strategy
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expires_at)
            if strategy != "ttl_only" and len(self._store) > self._max_size:
                evicted_key, _ = self._store.popitem(last=False)
                if self._on_evict is not None:
                    self._on_evict(evicted_key)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def close(self) -> None:
        self.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
