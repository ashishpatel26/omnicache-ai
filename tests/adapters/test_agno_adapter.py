"""Tests for AgnoCacheAdapter — mocked, no real Agno SDK needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _make_adapter(agent: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.agno_adapter._AGNO_AVAILABLE", True):
        from omnicache_ai.adapters.agno_adapter import AgnoCacheAdapter

        return AgnoCacheAdapter(agent, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock()
    agent.run.return_value = "AI is cool"
    return agent


def test_run_cache_miss(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    result = adapter.run("What is AI?")

    mock_agent.run.assert_called_once_with("What is AI?")
    assert result == "AI is cool"


def test_run_cache_hit(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("What is AI?")
    result = adapter.run("What is AI?")

    assert mock_agent.run.call_count == 1
    assert result == "AI is cool"


def test_run_different_messages_produce_cache_miss(
    manager: CacheManager, mock_agent: MagicMock
) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("What is AI?")
    adapter.run("What is ML?")

    assert mock_agent.run.call_count == 2


async def test_arun_cache_miss(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.arun = AsyncMock(return_value="async result")
    adapter = _make_adapter(agent, manager)

    result = await adapter.arun("What is AI?")

    assert result == "async result"
    agent.arun.assert_called_once_with("What is AI?")


async def test_arun_cache_hit(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.arun = AsyncMock(return_value="async result")
    adapter = _make_adapter(agent, manager)

    await adapter.arun("What is AI?")
    await adapter.arun("What is AI?")

    assert agent.arun.call_count == 1


def test_getattr_delegates_to_agent(manager: CacheManager, mock_agent: MagicMock) -> None:
    mock_agent.model_name = "gpt-4o"
    adapter = _make_adapter(mock_agent, manager)

    assert adapter.model_name == "gpt-4o"


def test_import_error_without_agno(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.agno_adapter._AGNO_AVAILABLE", False):
        from omnicache_ai.adapters.agno_adapter import AgnoCacheAdapter

        with pytest.raises(ImportError, match="agno"):
            AgnoCacheAdapter(MagicMock(), manager)
