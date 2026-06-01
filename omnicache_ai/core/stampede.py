"""Cache stampede protection via per-key locking."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Generator


class StampedeShield:
    """Per-key mutex to prevent cache stampede under concurrency.

    When multiple threads simultaneously miss the same cache key, only the
    first thread proceeds to compute the value; the rest wait and then read
    the result from cache once the lock is released.

    Usage::

        shield = StampedeShield()

        with shield.lock("omnicache:resp:abc123"):
            cached = cache.get(key)
            if cached is None:
                cached = expensive_llm_call()
                cache.set(key, cached)

    Args:
        timeout: Seconds to wait for a lock before raising TimeoutError.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._locks: dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def _get_lock(self, key: str) -> threading.Lock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def _release_lock(self, key: str) -> None:
        with self._meta_lock:
            self._locks.pop(key, None)

    @contextmanager
    def lock(self, key: str) -> Generator[bool, None, None]:
        """Acquire the per-key lock.

        Yields:
            True if this thread is the first to acquire (should compute).
            False if another thread held the lock first (should re-read cache).

        Raises:
            TimeoutError: If the lock cannot be acquired within ``timeout`` seconds.
        """
        lock = self._get_lock(key)
        acquired = lock.acquire(timeout=self._timeout)
        if not acquired:
            raise TimeoutError(f"StampedeShield: timed out waiting for key '{key}'")
        first = True
        try:
            yield first
        finally:
            lock.release()
            self._release_lock(key)
