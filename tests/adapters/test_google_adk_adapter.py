"""Tests for GoogleADKCacheAdapter — mocked, no real Google ADK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _fake_result(text: str = "Summary of report") -> SimpleNamespace:
    return SimpleNamespace(text=text)


def _make_adapter(agent: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.google_adk_adapter._ADK_AVAILABLE", True):
        from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

        return GoogleADKCacheAdapter(agent, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock()
    agent.name = "my_agent"
    agent.run.return_value = _fake_result()
    return agent


def test_run_cache_miss(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    result = adapter.run("Summarise the quarterly report")

    mock_agent.run.assert_called_once_with("Summarise the quarterly report")
    assert result is not None


def test_run_cache_hit(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("Summarise the quarterly report")
    adapter.run("Summarise the quarterly report")

    assert mock_agent.run.call_count == 1


def test_different_tasks_produce_cache_miss(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("Task A")
    adapter.run("Task B")

    assert mock_agent.run.call_count == 2


async def test_arun_uses_run_async_when_available(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.name = "async_agent"
    agent.run_async = AsyncMock(return_value=_fake_result("async result"))
    adapter = _make_adapter(agent, manager)

    result = await adapter.arun("Task")

    assert result is not None
    agent.run_async.assert_called_once_with("Task")


async def test_arun_falls_back_to_run(manager: CacheManager) -> None:
    agent = MagicMock(spec=["name", "run"])
    agent.name = "sync_agent"
    agent.run.return_value = _fake_result("sync result")
    adapter = _make_adapter(agent, manager)

    result = await adapter.arun("Task")

    assert result is not None
    agent.run.assert_called_once_with("Task")


async def test_arun_cache_hit(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.name = "async_agent"
    agent.run_async = AsyncMock(return_value=_fake_result("async result"))
    adapter = _make_adapter(agent, manager)

    await adapter.arun("Task")
    await adapter.arun("Task")

    assert agent.run_async.call_count == 1


def test_invalidate_agent(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("Summarise the quarterly report")
    adapter.invalidate_agent()
    adapter.run("Summarise the quarterly report")

    assert mock_agent.run.call_count == 2


def test_none_result_not_cached(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.name = "agent"
    agent.run.return_value = None
    adapter = _make_adapter(agent, manager)

    adapter.run("Task")
    adapter.run("Task")

    assert agent.run.call_count == 2


def test_getattr_delegates_to_agent(manager: CacheManager, mock_agent: MagicMock) -> None:
    mock_agent.model = "gemini-2.0-flash"
    adapter = _make_adapter(mock_agent, manager)

    assert adapter.model == "gemini-2.0-flash"


def test_import_error_without_adk(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.google_adk_adapter._ADK_AVAILABLE", False):
        from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

        with pytest.raises(ImportError, match="google-adk"):
            GoogleADKCacheAdapter(MagicMock(), manager)
