"""Tests for CrewAICacheAdapter — mocked, no real CrewAI SDK needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _make_adapter(crew: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.crewai_adapter._CREWAI_AVAILABLE", True):
        from omnicache_ai.adapters.crewai_adapter import CrewAICacheAdapter

        return CrewAICacheAdapter(crew, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


@pytest.fixture
def mock_crew() -> MagicMock:
    crew = MagicMock()
    crew.kickoff.return_value = "research output"
    return crew


def test_kickoff_cache_miss(manager: CacheManager, mock_crew: MagicMock) -> None:
    adapter = _make_adapter(mock_crew, manager)

    result = adapter.kickoff(inputs={"topic": "AI"})

    mock_crew.kickoff.assert_called_once_with(inputs={"topic": "AI"})
    assert result == "research output"


def test_kickoff_cache_hit(manager: CacheManager, mock_crew: MagicMock) -> None:
    adapter = _make_adapter(mock_crew, manager)

    adapter.kickoff(inputs={"topic": "AI"})
    result = adapter.kickoff(inputs={"topic": "AI"})

    assert mock_crew.kickoff.call_count == 1
    assert result == "research output"


def test_different_inputs_produce_cache_miss(manager: CacheManager, mock_crew: MagicMock) -> None:
    adapter = _make_adapter(mock_crew, manager)

    adapter.kickoff(inputs={"topic": "AI"})
    adapter.kickoff(inputs={"topic": "ML"})

    assert mock_crew.kickoff.call_count == 2


def test_kickoff_none_inputs(manager: CacheManager, mock_crew: MagicMock) -> None:
    adapter = _make_adapter(mock_crew, manager)

    adapter.kickoff(inputs=None)
    adapter.kickoff(inputs=None)

    assert mock_crew.kickoff.call_count == 1


async def test_kickoff_async_cache_miss(manager: CacheManager) -> None:
    crew = MagicMock()
    crew.kickoff_async = AsyncMock(return_value="async output")
    adapter = _make_adapter(crew, manager)

    result = await adapter.kickoff_async(inputs={"topic": "AI"})

    assert result == "async output"
    crew.kickoff_async.assert_called_once_with(inputs={"topic": "AI"})


async def test_kickoff_async_cache_hit(manager: CacheManager) -> None:
    crew = MagicMock()
    crew.kickoff_async = AsyncMock(return_value="async output")
    adapter = _make_adapter(crew, manager)

    await adapter.kickoff_async(inputs={"topic": "AI"})
    await adapter.kickoff_async(inputs={"topic": "AI"})

    assert crew.kickoff_async.call_count == 1


def test_getattr_delegates_to_crew(manager: CacheManager, mock_crew: MagicMock) -> None:
    mock_crew.agents = ["agent1", "agent2"]
    adapter = _make_adapter(mock_crew, manager)

    assert adapter.agents == ["agent1", "agent2"]


def test_import_error_without_crewai(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.crewai_adapter._CREWAI_AVAILABLE", False):
        from omnicache_ai.adapters.crewai_adapter import CrewAICacheAdapter

        with pytest.raises(ImportError, match="crewai"):
            CrewAICacheAdapter(MagicMock(), manager)
