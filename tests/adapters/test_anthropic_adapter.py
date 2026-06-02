"""Tests for AnthropicCacheAdapter — mocked, no real Anthropic SDK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


MESSAGES = [{"role": "user", "content": "Hello"}]
MODEL = "claude-sonnet-4-6"


def _fake_response():
    return SimpleNamespace(content=[SimpleNamespace(text="Hi!")])


def _make_adapter(client: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.anthropic_adapter._ANTHROPIC_AVAILABLE", True):
        from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

        return AnthropicCacheAdapter(client, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


def test_cache_miss_calls_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    result = adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)

    client.messages.create.assert_called_once_with(model=MODEL, max_tokens=100, messages=MESSAGES)
    assert result is not None


def test_cache_hit_skips_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)
    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)

    assert client.messages.create.call_count == 1


def test_different_system_prompts_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES, system="You are A")
    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES, system="You are B")

    assert client.messages.create.call_count == 2


def test_different_models_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)
    adapter.messages_create(model="claude-opus-4-8", max_tokens=100, messages=MESSAGES)

    assert client.messages.create.call_count == 2


def test_different_messages_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)
    adapter.messages_create(
        model=MODEL, max_tokens=100, messages=[{"role": "user", "content": "Bye"}]
    )

    assert client.messages.create.call_count == 2


async def test_amessages_create_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    result = await adapter.amessages_create(model=MODEL, max_tokens=100, messages=MESSAGES)

    assert result is not None
    client.messages.create.assert_called_once()


async def test_amessages_create_cache_hit(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    await adapter.amessages_create(model=MODEL, max_tokens=100, messages=MESSAGES)
    await adapter.amessages_create(model=MODEL, max_tokens=100, messages=MESSAGES)

    assert client.messages.create.call_count == 1


def test_invalidate_model_forces_api_call(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)
    adapter.invalidate_model(MODEL)
    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES)

    assert client.messages.create.call_count == 2


def test_stream_param_excluded_from_cache_key(manager: CacheManager) -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES, stream=False)
    adapter.messages_create(model=MODEL, max_tokens=100, messages=MESSAGES, stream=True)

    assert client.messages.create.call_count == 1


def test_import_error_without_anthropic(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.anthropic_adapter._ANTHROPIC_AVAILABLE", False):
        from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

        with pytest.raises(ImportError, match="anthropic"):
            AnthropicCacheAdapter(MagicMock(), manager)
