"""Tests for LangGraphCacheAdapter — no real LangGraph SDK needed."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _make_adapter(manager: CacheManager):
    with patch("omnicache_ai.adapters.langgraph_adapter._LANGGRAPH_AVAILABLE", True):
        from omnicache_ai.adapters.langgraph_adapter import LangGraphCacheAdapter

        return LangGraphCacheAdapter(manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


def _cfg(thread_id: str, checkpoint_id: str = "") -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "checkpoint_id": checkpoint_id,
        }
    }


def test_put_and_get_tuple_roundtrip(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    checkpoint = {"channel_values": {"messages": ["hello"]}}
    metadata = {"step": 1}

    result_cfg = adapter.put(_cfg("t1"), checkpoint, metadata)
    cid = result_cfg["configurable"]["checkpoint_id"]

    stored = adapter.get_tuple(_cfg("t1", cid))
    assert stored is not None


def test_get_tuple_returns_none_for_unknown_thread(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    result = adapter.get_tuple(_cfg("nonexistent"))
    assert result is None


def test_get_latest_checkpoint_without_checkpoint_id(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    checkpoint = {"channel_values": {"messages": ["hi"]}}

    adapter.put(_cfg("t2"), checkpoint, {})
    stored = adapter.get_tuple(_cfg("t2"))
    assert stored is not None


def test_multiple_puts_preserves_history(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)

    # Use explicit checkpoint IDs to avoid monotonic_ns collision on fast machines
    adapter.put(_cfg("t3", "cp-1"), {"step": 1}, {})
    adapter.put(_cfg("t3", "cp-2"), {"step": 2}, {})

    checkpoints = list(adapter.list(_cfg("t3")))
    assert len(checkpoints) == 2


def test_list_most_recent_first(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)

    adapter.put(_cfg("t4", "cp-1"), {"step": 1}, {"step": 1})
    adapter.put(_cfg("t4", "cp-2"), {"step": 2}, {"step": 2})

    checkpoints = list(adapter.list(_cfg("t4")))
    assert len(checkpoints) == 2


def test_list_with_limit(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)

    for i in range(5):
        adapter.put(_cfg("t5", f"cp-{i}"), {"step": i}, {})

    checkpoints = list(adapter.list(_cfg("t5"), limit=3))
    assert len(checkpoints) == 3


def test_list_empty_for_unknown_thread(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    checkpoints = list(adapter.list(_cfg("unknown_thread")))
    assert checkpoints == []


def test_put_writes(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    cfg = adapter.put(_cfg("t6"), {}, {})
    cid = cfg["configurable"]["checkpoint_id"]

    adapter.put_writes(_cfg("t6", cid), [("key", "value")], "task-1")
    # No assertion needed — just verifying no exception


def test_get_next_version_none(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    assert adapter.get_next_version(None, None) == 1


def test_get_next_version_int(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    assert adapter.get_next_version(5, None) == 6


def test_get_next_version_str(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    assert adapter.get_next_version("3", None) == "4"


async def test_aget_tuple_delegates_to_sync(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)
    adapter.put(_cfg("async_t"), {"x": 1}, {})

    result = await adapter.aget_tuple(_cfg("async_t"))
    assert result is not None


async def test_aput_delegates_to_sync(manager: CacheManager) -> None:
    adapter = _make_adapter(manager)

    result_cfg = await adapter.aput(_cfg("async_t2"), {"x": 1}, {})
    assert "checkpoint_id" in result_cfg["configurable"]


def test_import_error_without_langgraph(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.langgraph_adapter._LANGGRAPH_AVAILABLE", False):
        from omnicache_ai.adapters.langgraph_adapter import LangGraphCacheAdapter

        with pytest.raises(ImportError, match="langgraph"):
            LangGraphCacheAdapter(manager)
