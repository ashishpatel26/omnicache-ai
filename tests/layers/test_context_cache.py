"""Tests for ContextCache."""

from __future__ import annotations

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder
from omnicache_ai.layers.context_cache import ContextCache


@pytest.fixture
def cache() -> ContextCache:
    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )
    return ContextCache(manager)


MESSAGES = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]


def test_get_miss(cache: ContextCache) -> None:
    assert cache.get("session-1") is None


def test_set_and_get_roundtrip(cache: ContextCache) -> None:
    cache.set("session-1", MESSAGES)
    result = cache.get("session-1")
    assert result == MESSAGES


def test_set_and_get_with_turn_index(cache: ContextCache) -> None:
    cache.set("session-2", MESSAGES, turn_index=3)
    result = cache.get("session-2", turn_index=3)
    assert result == MESSAGES


def test_turn_index_differentiates_keys(cache: ContextCache) -> None:
    cache.set("session-3", MESSAGES, turn_index=1)
    cache.set("session-3", [{"role": "user", "content": "New"}], turn_index=2)

    assert cache.get("session-3", turn_index=1) == MESSAGES
    assert cache.get("session-3", turn_index=2) == [{"role": "user", "content": "New"}]


def test_different_sessions_independent(cache: ContextCache) -> None:
    cache.set("session-A", MESSAGES)
    cache.set("session-B", [{"role": "user", "content": "Different"}])

    assert cache.get("session-A") == MESSAGES
    assert cache.get("session-B") == [{"role": "user", "content": "Different"}]


def test_invalidate_session(cache: ContextCache) -> None:
    cache.set("session-4", MESSAGES)
    assert cache.get("session-4") == MESSAGES

    cache.invalidate_session("session-4")

    assert cache.get("session-4") is None


def test_empty_messages_list(cache: ContextCache) -> None:
    cache.set("session-5", [])
    result = cache.get("session-5")
    assert result == []


def test_overwrite_same_session(cache: ContextCache) -> None:
    cache.set("session-6", MESSAGES)
    new_messages = [{"role": "user", "content": "Updated"}]
    cache.set("session-6", new_messages)
    assert cache.get("session-6") == new_messages
