"""Async cache backend protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncCacheBackend(Protocol):
    """Structural interface for async key-value cache backends.

    Implement this when the backend has native async I/O (e.g. redis.asyncio,
    aiofiles) to avoid blocking the event loop from async frameworks like
    FastAPI or async LangGraph.
    """

    async def get(self, key: str) -> Any | None:
        """Return cached value, or None if missing/expired."""
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store value under key. ttl is seconds; None means no expiry."""
        ...

    async def delete(self, key: str) -> None:
        """Remove key. No-op if not present."""
        ...

    async def exists(self, key: str) -> bool:
        """Return True if key is present and not expired."""
        ...

    async def clear(self) -> None:
        """Flush all entries."""
        ...

    async def close(self) -> None:
        """Release resources."""
        ...
