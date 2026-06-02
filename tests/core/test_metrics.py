"""Tests for CacheMetrics."""

from __future__ import annotations

import threading

import pytest

from omnicache_ai.core.metrics import CacheMetrics


@pytest.fixture
def metrics() -> CacheMetrics:
    return CacheMetrics()


def test_initial_values(metrics: CacheMetrics) -> None:
    assert metrics.hits == 0
    assert metrics.misses == 0
    assert metrics.evictions == 0
    assert metrics.sets == 0
    assert metrics.provider_cache_hits == 0
    assert metrics.estimated_tokens_saved == 0
    assert metrics.estimated_cost_saved_usd == 0.0


def test_hit_rate_zero_with_no_lookups(metrics: CacheMetrics) -> None:
    assert metrics.hit_rate == 0.0


def test_hit_rate_calculation(metrics: CacheMetrics) -> None:
    metrics.hits = 3
    metrics.misses = 1
    assert metrics.hit_rate == 0.75


def test_miss_rate_is_complement_of_hit_rate(metrics: CacheMetrics) -> None:
    metrics.hits = 3
    metrics.misses = 1
    assert abs(metrics.hit_rate + metrics.miss_rate - 1.0) < 1e-9


def test_record_hit_increments(metrics: CacheMetrics) -> None:
    metrics.record_hit()
    metrics.record_hit()
    assert metrics.hits == 2


def test_record_miss_increments(metrics: CacheMetrics) -> None:
    metrics.record_miss()
    assert metrics.misses == 1


def test_record_eviction_increments(metrics: CacheMetrics) -> None:
    metrics.record_eviction()
    assert metrics.evictions == 1


def test_record_set_increments(metrics: CacheMetrics) -> None:
    metrics.record_set()
    assert metrics.sets == 1


def test_reset_clears_all_fields(metrics: CacheMetrics) -> None:
    metrics.hits = 5
    metrics.misses = 3
    metrics.evictions = 2
    metrics.sets = 10
    metrics.provider_cache_hits = 1
    metrics.estimated_tokens_saved = 1000
    metrics.estimated_cost_saved_usd = 0.05

    metrics.reset()

    assert metrics.hits == 0
    assert metrics.misses == 0
    assert metrics.evictions == 0
    assert metrics.sets == 0
    assert metrics.provider_cache_hits == 0
    assert metrics.estimated_tokens_saved == 0
    assert metrics.estimated_cost_saved_usd == 0.0


def test_snapshot_returns_dict(metrics: CacheMetrics) -> None:
    metrics.record_hit()
    metrics.record_miss()
    snap = metrics.snapshot()

    assert isinstance(snap, dict)
    assert snap["hits"] == 1
    assert snap["misses"] == 1
    assert snap["hit_rate"] == 0.5
    assert snap["miss_rate"] == 0.5


def test_snapshot_includes_all_fields(metrics: CacheMetrics) -> None:
    snap = metrics.snapshot()
    expected_keys = {
        "hits",
        "misses",
        "evictions",
        "sets",
        "hit_rate",
        "miss_rate",
        "provider_cache_hits",
        "estimated_tokens_saved",
        "estimated_cost_saved_usd",
    }
    assert expected_keys.issubset(snap.keys())


def test_thread_safe_concurrent_hits(metrics: CacheMetrics) -> None:
    def record_many():
        for _ in range(100):
            metrics.record_hit()

    threads = [threading.Thread(target=record_many) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert metrics.hits == 1000
