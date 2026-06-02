"""Tests for A2ACacheAdapter — no external dependencies needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from omnicache_ai.adapters.a2a_adapter import A2ACacheAdapter
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


@pytest.fixture
def adapter(manager: CacheManager) -> A2ACacheAdapter:
    return A2ACacheAdapter(manager, agent_id="planner")


def test_process_cache_miss(adapter: A2ACacheAdapter) -> None:
    handler = MagicMock(return_value={"status": "done"})

    result = adapter.process(handler, {"task": "summarize"})

    handler.assert_called_once_with({"task": "summarize"})
    assert result == {"status": "done"}


def test_process_cache_hit(adapter: A2ACacheAdapter) -> None:
    handler = MagicMock(return_value={"status": "done"})

    adapter.process(handler, {"task": "summarize"})
    result = adapter.process(handler, {"task": "summarize"})

    assert handler.call_count == 1
    assert result == {"status": "done"}


def test_different_payloads_produce_cache_miss(adapter: A2ACacheAdapter) -> None:
    handler = MagicMock(return_value={"status": "done"})

    adapter.process(handler, {"task": "summarize"})
    adapter.process(handler, {"task": "translate"})

    assert handler.call_count == 2


def test_different_agent_ids_independent(manager: CacheManager) -> None:
    handler = MagicMock(return_value="result")
    adapter_a = A2ACacheAdapter(manager, agent_id="planner")
    adapter_b = A2ACacheAdapter(manager, agent_id="executor")

    adapter_a.process(handler, "task")
    adapter_b.process(handler, "task")

    # Different agent IDs → different cache keys → handler called twice
    assert handler.call_count == 2


async def test_aprocess_cache_miss(adapter: A2ACacheAdapter) -> None:
    handler = AsyncMock(return_value={"status": "async done"})

    result = await adapter.aprocess(handler, {"task": "async_task"})

    assert result == {"status": "async done"}
    handler.assert_called_once_with({"task": "async_task"})


async def test_aprocess_cache_hit(adapter: A2ACacheAdapter) -> None:
    handler = AsyncMock(return_value={"status": "async done"})

    await adapter.aprocess(handler, {"task": "async_task"})
    await adapter.aprocess(handler, {"task": "async_task"})

    assert handler.call_count == 1


def test_wrap_decorator_caches(adapter: A2ACacheAdapter) -> None:
    call_count = 0

    @adapter.wrap
    def handle(payload: dict) -> dict:
        nonlocal call_count
        call_count += 1
        return {"result": "done"}

    handle({"task": "summarize"})
    handle({"task": "summarize"})

    assert call_count == 1


def test_wrap_preserves_function_metadata(adapter: A2ACacheAdapter) -> None:
    @adapter.wrap
    def handle_task(payload: dict) -> dict:
        """Handle a task."""
        return {}

    assert handle_task.__name__ == "handle_task"
    assert handle_task.__doc__ == "Handle a task."
