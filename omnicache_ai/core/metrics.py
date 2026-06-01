"""Cache hit/miss/eviction metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class CacheMetrics:
    """Thread-safe counters for cache operations.

    Attributes:
        hits: Exact or semantic cache hits served without calling the model.
        misses: Cache misses that required a downstream call.
        evictions: LRU evictions performed by InMemoryBackend.
        sets: Total cache writes.
        provider_cache_hits: Server-side prompt cache hits (Anthropic/OpenAI).
        estimated_tokens_saved: Tokens saved via provider-level prompt caching.
        estimated_cost_saved_usd: Estimated USD saved via provider caching.
    """

    hits: int = field(default=0)
    misses: int = field(default=0)
    evictions: int = field(default=0)
    sets: int = field(default=0)
    provider_cache_hits: int = field(default=0)
    estimated_tokens_saved: int = field(default=0)
    estimated_cost_saved_usd: float = field(default=0.0)
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
            self.provider_cache_hits = 0
            self.estimated_tokens_saved = 0
            self.estimated_cost_saved_usd = 0.0

    def snapshot(self) -> dict[str, Any]:
        """Return a plain-dict snapshot safe for logging/serialization."""
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "sets": self.sets,
                "hit_rate": round(self.hit_rate, 4),
                "miss_rate": round(self.miss_rate, 4),
                "provider_cache_hits": self.provider_cache_hits,
                "estimated_tokens_saved": self.estimated_tokens_saved,
                "estimated_cost_saved_usd": round(self.estimated_cost_saved_usd, 6),
            }
