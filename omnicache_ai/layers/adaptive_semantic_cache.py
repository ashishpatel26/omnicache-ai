"""Adaptive semantic cache — self-tuning similarity threshold."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Callable

import numpy as np

from omnicache_ai.layers.semantic_cache import SemanticCache

if TYPE_CHECKING:
    from omnicache_ai.backends.base import CacheBackend, VectorBackend
    from omnicache_ai.core.key_builder import CacheKeyBuilder
    from omnicache_ai.core.serializer import Serializer


class AdaptiveSemanticCache(SemanticCache):
    """SemanticCache that auto-tunes the similarity threshold to hit a target hit rate.

    Research shows production semantic caches hit 20–45% of traffic, not the
    95% that a 0.95 threshold implies. This class adjusts the threshold up or
    down every ``adjustment_interval`` lookups to approach ``target_hit_rate``.

    Also adds a ``max_turn_count`` guard: semantic lookup is skipped for
    multi-turn conversations longer than the configured limit (prevents false
    positives from semantically overlapping chat histories).

    Usage::

        from omnicache_ai.backends.memory_backend import InMemoryBackend
        from omnicache_ai.backends.vector_backend import FAISSBackend
        from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

        cache = AdaptiveSemanticCache(
            exact_backend=InMemoryBackend(),
            vector_backend=FAISSBackend(dim=1536),
            embed_fn=embed,
            target_hit_rate=0.35,    # aim for 35% hit rate
            adjustment_interval=50,  # re-tune every 50 calls
            max_turn_count=5,        # skip semantic for > 5-turn conversations
        )

    Args:
        target_hit_rate: Desired hit rate (0.0–1.0). Default: 0.35.
        adjustment_interval: Recalibrate threshold every N lookups. Default: 100.
        threshold_min: Minimum allowed threshold (floor). Default: 0.70.
        threshold_max: Maximum allowed threshold (ceiling). Default: 0.99.
        adjustment_step: How much to nudge threshold per recalibration. Default: 0.02.
        max_turn_count: Skip semantic lookup for conversations > N messages. Default: 10.
    """

    def __init__(
        self,
        exact_backend: "CacheBackend",
        vector_backend: "VectorBackend",
        embed_fn: Callable[[str], np.ndarray],
        threshold: float = 0.90,
        key_builder: "CacheKeyBuilder | None" = None,
        serializer: "Serializer | None" = None,
        target_hit_rate: float = 0.35,
        adjustment_interval: int = 100,
        threshold_min: float = 0.70,
        threshold_max: float = 0.99,
        adjustment_step: float = 0.02,
        max_turn_count: int = 10,
    ) -> None:
        super().__init__(
            exact_backend=exact_backend,
            vector_backend=vector_backend,
            embed_fn=embed_fn,
            threshold=threshold,
            key_builder=key_builder,
            serializer=serializer,
        )
        self._target_hit_rate = target_hit_rate
        self._interval = adjustment_interval
        self._min = threshold_min
        self._max = threshold_max
        self._step = adjustment_step
        self._max_turns = max_turn_count
        self._lock = threading.Lock()
        self._window_hits = 0
        self._window_total = 0

    def _maybe_adjust(self) -> None:
        if self._window_total < self._interval:
            return
        with self._lock:
            if self._window_total == 0:
                return
            actual = self._window_hits / self._window_total
            if actual < self._target_hit_rate:
                self._threshold = max(self._min, self._threshold - self._step)
            elif actual > self._target_hit_rate + 0.05:
                self._threshold = min(self._max, self._threshold + self._step)
            self._window_hits = 0
            self._window_total = 0

    def get(self, query: str, turn_count: int = 0) -> Any | None:
        """Retrieve with adaptive threshold and optional multi-turn guard.

        Args:
            query: Query text.
            turn_count: Number of turns in the current conversation.
                        If > max_turn_count, semantic lookup is skipped.
        """
        if turn_count > self._max_turns:
            key = self._kb.build("response", query)
            raw = self._exact.get(key)
            return self._serializer.loads(raw) if raw is not None else None

        result = super().get(query)
        with self._lock:
            self._window_total += 1
            if result is not None:
                self._window_hits += 1
        self._maybe_adjust()
        return result

    @property
    def current_threshold(self) -> float:
        return self._threshold
