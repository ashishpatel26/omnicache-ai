"""Async in-memory cache backend wrapping InMemoryBackend with asyncio.Lock."""

from __future__ import annotations

import asyncio
from typing import Any

from omnicache_ai.backends.memory_backend import InMemoryBackend


class AsyncInMemoryBackend:
    """Async wrapper around InMemoryBackend using asyncio.Lock.

    Suitable for use in async frameworks (FastAPI, async LangGraph) without
    blocking the event loop. All operations delegate to InMemoryBackend under
    an asyncio.Lock.

    Args:
        max_size: Maximum number of entries before LRU eviction.
    """

    def __init__(self, max_size: int = 10_000) -> None:
        self._inner = InMemoryBackend(max_size=max_size)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            return self._inner.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            self._inner.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._inner.delete(key)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return self._inner.exists(key)

    async def clear(self) -> None:
        async with self._lock:
            self._inner.clear()

    async def close(self) -> None:
        async with self._lock:
            self._inner.close()
