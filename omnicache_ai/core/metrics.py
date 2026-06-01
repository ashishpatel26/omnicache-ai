"""Cache hit/miss/eviction metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class CacheMetrics:
    """Thread-safe counters for cache operations.

    Attributes:
        hits: Exact or semantic cache hits served without calling the model.
        misses: Cache misses that required a downstream call.
        evictions: LRU evictions performed by InMemoryBackend.
        sets: Total cache writes.
    """

    hits: int = field(default=0)
    misses: int = field(default=0)
    evictions: int = field(default=0)
    sets: int = field(default=0)
    _lock: Lock = field(default_factory=Lock, repr=False, compare=False)

    @property
    def hit_rate(self) -> float:
        """Fraction of lookups that were cache hits (0.0–1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate

    def record_hit(self) -> None:
        with self._lock:
            self.hits += 1

    def record_miss(self) -> None:
        with self._lock:
            self.misses += 1

    def record_eviction(self) -> None:
        with self._lock:
            self.evictions += 1

    def record_set(self) -> None:
        with self._lock:
            self.sets += 1

    def reset(self) -> None:
        with self._lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0
            self.sets = 0

    def snapshot(self) -> dict[str, object]:
        """Return a plain-dict snapshot safe for logging/serialization."""
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "sets": self.sets,
                "hit_rate": round(self.hit_rate, 4),
                "miss_rate": round(self.miss_rate, 4),
            }
