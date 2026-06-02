"""Tests for TieredBackend (L1 + L2 composition)."""

from __future__ import annotations

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.tiered_backend import TieredBackend


@pytest.fixture
def tiered() -> TieredBackend:
    return TieredBackend(l1=InMemoryBackend(), l2=InMemoryBackend(), l1_ttl=300)


def test_set_writes_to_both_layers(tiered: TieredBackend) -> None:
    tiered.set("key", b"value")
    assert tiered._l1.get("key") == b"value"
    assert tiered._l2.get("key") == b"value"


def test_get_returns_l1_on_hit(tiered: TieredBackend) -> None:
    tiered._l1.set("key", b"from-l1")
    tiered._l2.set("key", b"from-l2")

    assert tiered.get("key") == b"from-l1"


def test_get_promotes_l2_to_l1_on_l1_miss() -> None:
    l1 = InMemoryBackend()
    l2 = InMemoryBackend()
    backend = TieredBackend(l1=l1, l2=l2, l1_ttl=60)

    l2.set("key", b"from-l2")
    result = backend.get("key")

    assert result == b"from-l2"
    assert l1.get("key") == b"from-l2"


def test_get_returns_none_on_total_miss(tiered: TieredBackend) -> None:
    assert tiered.get("nonexistent") is None


def test_delete_removes_from_both_layers(tiered: TieredBackend) -> None:
    tiered.set("key", b"value")
    tiered.delete("key")

    assert tiered._l1.get("key") is None
    assert tiered._l2.get("key") is None


def test_exists_true_when_in_l1(tiered: TieredBackend) -> None:
    tiered._l1.set("key", b"v")
    assert tiered.exists("key") is True


def test_exists_true_when_only_in_l2(tiered: TieredBackend) -> None:
    tiered._l2.set("key", b"v")
    assert tiered.exists("key") is True


def test_exists_false_on_miss(tiered: TieredBackend) -> None:
    assert tiered.exists("nonexistent") is False


def test_clear_clears_both_layers(tiered: TieredBackend) -> None:
    tiered.set("a", b"1")
    tiered.set("b", b"2")
    tiered.clear()

    assert tiered.get("a") is None
    assert tiered.get("b") is None


def test_close_does_not_raise(tiered: TieredBackend) -> None:
    tiered.close()


def test_l1_ttl_none_no_min(tiered: TieredBackend) -> None:
    backend = TieredBackend(l1=InMemoryBackend(), l2=InMemoryBackend(), l1_ttl=None)
    backend.set("key", b"value", ttl=60)
    assert backend.get("key") == b"value"
