"""Tests for AdaptiveSemanticCache."""

from __future__ import annotations

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache
from tests.conftest import mock_embed


@pytest.fixture
def cache() -> AdaptiveSemanticCache:
    pytest.importorskip("faiss", reason="faiss-cpu not installed")
    exact = InMemoryBackend()
    vector = FAISSBackend(dim=1536)
    return AdaptiveSemanticCache(
        exact_backend=exact,
        vector_backend=vector,
        embed_fn=mock_embed,
        threshold=0.90,
        target_hit_rate=0.35,
        adjustment_interval=10,
    )


def test_get_miss(cache: AdaptiveSemanticCache) -> None:
    assert cache.get("What is AI?") is None


def test_set_and_exact_get(cache: AdaptiveSemanticCache) -> None:
    cache.set("What is AI?", "Artificial Intelligence")
    result = cache.get("What is AI?")
    assert result == "Artificial Intelligence"


def test_initial_threshold(cache: AdaptiveSemanticCache) -> None:
    assert cache.current_threshold == 0.90


def test_max_turn_count_guard_skips_semantic(cache: AdaptiveSemanticCache) -> None:
    cache.set("What is AI?", "Artificial Intelligence")
    # Turn count exceeds max_turn_count (default 10) — skips semantic search
    result = cache.get("What is AI?", turn_count=11)
    # Still gets exact hit (exact backend is checked even with guard)
    assert result is not None


def test_max_turn_count_guard_within_limit(cache: AdaptiveSemanticCache) -> None:
    cache.set("What is AI?", "Artificial Intelligence")
    result = cache.get("What is AI?", turn_count=5)
    assert result == "Artificial Intelligence"


def test_threshold_adjusts_down_on_low_hit_rate(cache: AdaptiveSemanticCache) -> None:
    initial = cache.current_threshold

    # Simulate all misses to trigger downward adjustment
    for i in range(10):
        cache.get(f"unique query {i} no match")

    # After adjustment interval, threshold should decrease (or stay at min)
    assert cache.current_threshold <= initial


def test_threshold_adjusts_up_on_high_hit_rate() -> None:
    pytest.importorskip("faiss", reason="faiss-cpu not installed")
    exact = InMemoryBackend()
    vector = FAISSBackend(dim=1536)
    cache = AdaptiveSemanticCache(
        exact_backend=exact,
        vector_backend=vector,
        embed_fn=mock_embed,
        threshold=0.75,
        target_hit_rate=0.30,
        adjustment_interval=5,
    )

    # Seed cache
    cache.set("query", "answer")

    # All hits → actual rate > target + 0.05 → threshold increases
    for _ in range(5):
        cache.get("query")

    assert cache.current_threshold >= 0.75


def test_threshold_bounded_by_min_max() -> None:
    pytest.importorskip("faiss", reason="faiss-cpu not installed")
    exact = InMemoryBackend()
    vector = FAISSBackend(dim=1536)
    cache = AdaptiveSemanticCache(
        exact_backend=exact,
        vector_backend=vector,
        embed_fn=mock_embed,
        threshold=0.70,
        target_hit_rate=0.99,  # very high target — forces upward adjustment
        adjustment_interval=5,
        threshold_min=0.70,
        threshold_max=0.99,
        adjustment_step=0.10,
    )

    # Trigger many adjustments
    cache.set("q", "a")
    for _ in range(50):
        cache.get("q")

    assert cache.current_threshold <= 0.99
    assert cache.current_threshold >= 0.70
