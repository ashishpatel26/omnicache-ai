"""Tests for OpenAIAgentsCacheAdapter — mocked, no real OpenAI Agents SDK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _fake_result() -> SimpleNamespace:
    return SimpleNamespace(final_output="4")


def _manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


def _mock_agent() -> MagicMock:
    agent = MagicMock()
    agent.name = "assistant"
    agent.model = "gpt-4o"
    return agent


def test_run_cache_miss() -> None:
    runner = MagicMock()
    runner.run_sync.return_value = _fake_result()
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            result = adapter.run(agent, "What is 2+2?")

    runner.run_sync.assert_called_once_with(agent, "What is 2+2?")
    assert result is not None


def test_run_cache_hit() -> None:
    runner = MagicMock()
    runner.run_sync.return_value = _fake_result()
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            adapter.run(agent, "What is 2+2?")
            adapter.run(agent, "What is 2+2?")

    assert runner.run_sync.call_count == 1


def test_different_inputs_produce_cache_miss() -> None:
    runner = MagicMock()
    runner.run_sync.return_value = _fake_result()
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            adapter.run(agent, "What is 2+2?")
            adapter.run(agent, "What is 3+3?")

    assert runner.run_sync.call_count == 2


async def test_arun_cache_miss() -> None:
    runner = MagicMock()
    runner.run = AsyncMock(return_value=_fake_result())
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            result = await adapter.arun(agent, "What is 2+2?")

    assert result is not None
    runner.run.assert_called_once_with(agent, "What is 2+2?")


async def test_arun_cache_hit() -> None:
    runner = MagicMock()
    runner.run = AsyncMock(return_value=_fake_result())
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            await adapter.arun(agent, "What is 2+2?")
            await adapter.arun(agent, "What is 2+2?")

    assert runner.run.call_count == 1


def test_invalidate_agent() -> None:
    runner = MagicMock()
    runner.run_sync.return_value = _fake_result()
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            adapter.run(agent, "What is 2+2?")
            adapter.invalidate_agent(agent)
            adapter.run(agent, "What is 2+2?")

    assert runner.run_sync.call_count == 2


def test_none_result_not_cached() -> None:
    runner = MagicMock()
    runner.run_sync.return_value = None
    agent = _mock_agent()
    manager = _manager()

    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", True):
        with patch("omnicache_ai.adapters.openai_agents_adapter._Runner", runner):
            from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

            adapter = OpenAIAgentsCacheAdapter(manager)
            adapter.run(agent, "Task")
            adapter.run(agent, "Task")

    assert runner.run_sync.call_count == 2


def test_import_error_without_openai_agents() -> None:
    manager = _manager()
    with patch("omnicache_ai.adapters.openai_agents_adapter._OPENAI_AGENTS_AVAILABLE", False):
        from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

        with pytest.raises(ImportError, match="openai-agents"):
            OpenAIAgentsCacheAdapter(manager)
