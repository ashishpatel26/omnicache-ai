"""Tests for ClaudeAgentCacheAdapter — mocked, no real Claude Code SDK needed."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


async def _async_gen(*items):
    for item in items:
        yield item


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


async def test_query_cache_miss_yields_messages(manager: CacheManager) -> None:
    mock_sdk = MagicMock()
    mock_sdk.query.return_value = _async_gen("msg1", "msg2", "msg3")

    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", mock_sdk):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)
            messages = []
            async for msg in adapter.query("Fix the bug"):
                messages.append(msg)

    assert messages == ["msg1", "msg2", "msg3"]
    mock_sdk.query.assert_called_once_with(prompt="Fix the bug")


async def test_query_cache_hit_replays_messages(manager: CacheManager) -> None:
    call_count = 0

    async def fresh_gen(**kwargs):
        nonlocal call_count
        call_count += 1
        yield "msg1"
        yield "msg2"

    mock_sdk = MagicMock()
    mock_sdk.query.side_effect = fresh_gen

    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", mock_sdk):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)

            msgs1 = [m async for m in adapter.query("Fix the bug")]
            msgs2 = [m async for m in adapter.query("Fix the bug")]

    assert call_count == 1
    assert msgs1 == msgs2 == ["msg1", "msg2"]


async def test_different_prompts_produce_cache_miss(manager: CacheManager) -> None:
    call_count = 0

    async def fresh_gen(**kwargs):
        nonlocal call_count
        call_count += 1
        yield "msg"

    mock_sdk = MagicMock()
    mock_sdk.query.side_effect = fresh_gen

    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", mock_sdk):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)
            async for _ in adapter.query("Fix bug A"):
                pass
            async for _ in adapter.query("Fix bug B"):
                pass

    assert call_count == 2


async def test_empty_result_not_cached(manager: CacheManager) -> None:
    call_count = 0

    async def empty_gen(**kwargs):
        nonlocal call_count
        call_count += 1
        return
        yield  # make it an async generator

    mock_sdk = MagicMock()
    mock_sdk.query.side_effect = empty_gen

    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", mock_sdk):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)
            async for _ in adapter.query("Empty task"):
                pass
            async for _ in adapter.query("Empty task"):
                pass

    assert call_count == 2


async def test_query_with_options(manager: CacheManager) -> None:
    from types import SimpleNamespace

    mock_sdk = MagicMock()
    mock_sdk.query.return_value = _async_gen("msg1", "msg2", "msg3")
    options = SimpleNamespace(max_tokens=100)

    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", mock_sdk):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)
            messages = [m async for m in adapter.query("Fix the bug", options=options)]

    assert len(messages) == 3
    mock_sdk.query.assert_called_once_with(prompt="Fix the bug", options=options)


def test_invalidate_all(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", True):
        with patch("omnicache_ai.adapters.claude_agent_adapter._sdk", MagicMock()):
            from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

            adapter = ClaudeAgentCacheAdapter(manager)
            adapter.invalidate_all()  # should not raise


def test_import_error_without_sdk(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.claude_agent_adapter._CLAUDE_SDK_AVAILABLE", False):
        from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

        with pytest.raises(ImportError, match="claude-code-sdk"):
            ClaudeAgentCacheAdapter(manager)
