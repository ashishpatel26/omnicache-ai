"""Tests for AutoGenCacheAdapter — mocked, no real AutoGen SDK needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


MESSAGES = [{"role": "user", "content": "What is 2+2?"}]


def _make_adapter(agent: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.autogen_adapter._AUTOGEN_AVAILABLE", True):
        from omnicache_ai.adapters.autogen_adapter import AutoGenCacheAdapter

        return AutoGenCacheAdapter(agent, manager)


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
    agent.name = "assistant"
    agent.generate_reply.return_value = "4"
    agent.run.return_value = "run result"  # must be picklable
    return agent


def test_generate_reply_cache_miss(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    result = adapter.generate_reply(messages=MESSAGES)

    mock_agent.generate_reply.assert_called_once_with(messages=MESSAGES, sender=None)
    assert result == "4"


def test_generate_reply_cache_hit(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.generate_reply(messages=MESSAGES)
    result = adapter.generate_reply(messages=MESSAGES)

    assert mock_agent.generate_reply.call_count == 1
    assert result == "4"


def test_generate_reply_different_messages_miss(
    manager: CacheManager, mock_agent: MagicMock
) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.generate_reply(messages=MESSAGES)
    adapter.generate_reply(messages=[{"role": "user", "content": "What is 3+3?"}])

    assert mock_agent.generate_reply.call_count == 2


def test_run_cache_miss(manager: CacheManager, mock_agent: MagicMock) -> None:
    # MagicMock has `run` attr so adapter calls agent.run(task=...)
    adapter = _make_adapter(mock_agent, manager)

    result = adapter.run("Hello")

    assert result == "run result"


def test_run_cache_hit(manager: CacheManager, mock_agent: MagicMock) -> None:
    adapter = _make_adapter(mock_agent, manager)

    adapter.run("Hello")
    adapter.run("Hello")

    assert mock_agent.run.call_count == 1


def test_run_without_run_attr_uses_generate_reply(manager: CacheManager) -> None:
    # Agent without `run` attribute → adapter falls back to generate_reply
    agent = MagicMock(spec=["name", "generate_reply"])
    agent.name = "assistant"
    agent.generate_reply.return_value = "fallback"
    adapter = _make_adapter(agent, manager)

    result = adapter.run("Hello")

    assert result == "fallback"
    agent.generate_reply.assert_called_once()


async def test_arun_cache_miss(manager: CacheManager) -> None:
    # arun without agent.run → calls generate_reply
    agent = MagicMock(spec=["name", "generate_reply"])
    agent.name = "assistant"
    agent.generate_reply.return_value = "async result"
    adapter = _make_adapter(agent, manager)

    result = await adapter.arun("Hello async")

    assert result == "async result"


async def test_arun_cache_hit(manager: CacheManager) -> None:
    agent = MagicMock(spec=["name", "generate_reply"])
    agent.name = "assistant"
    agent.generate_reply.return_value = "async result"
    adapter = _make_adapter(agent, manager)

    await adapter.arun("Hello async")
    await adapter.arun("Hello async")

    assert agent.generate_reply.call_count == 1


async def test_arun_uses_agent_run_when_available(manager: CacheManager) -> None:
    agent = MagicMock()
    agent.name = "assistant"
    agent.run = AsyncMock(return_value="run_result")

    with patch("omnicache_ai.adapters.autogen_adapter._AUTOGEN_AVAILABLE", True):
        with patch("omnicache_ai.adapters.autogen_adapter._AUTOGEN_V2", True):
            with patch("omnicache_ai.adapters.autogen_adapter.AssistantAgent", None):
                from omnicache_ai.adapters.autogen_adapter import AutoGenCacheAdapter

                adapter = AutoGenCacheAdapter(agent, manager)
                result = await adapter.arun("task message")

    assert result == "run_result"
    agent.run.assert_called_once_with(task="task message")


def test_getattr_delegates_to_agent(manager: CacheManager, mock_agent: MagicMock) -> None:
    mock_agent.some_custom_attr = "hello"
    adapter = _make_adapter(mock_agent, manager)

    assert adapter.some_custom_attr == "hello"


def test_import_error_without_autogen(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.autogen_adapter._AUTOGEN_AVAILABLE", False):
        from omnicache_ai.adapters.autogen_adapter import AutoGenCacheAdapter

        with pytest.raises(ImportError, match="autogen"):
            AutoGenCacheAdapter(MagicMock(), manager)
