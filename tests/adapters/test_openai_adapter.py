"""Tests for OpenAICacheAdapter — mocked, no real OpenAI SDK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


MESSAGES = [{"role": "user", "content": "Hello"}]


def _fake_response():
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Hello!"))])


def _make_adapter(client: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.openai_adapter._OPENAI_AVAILABLE", True):
        from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

        return OpenAICacheAdapter(client, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


def test_cache_miss_calls_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    result = adapter.chat_create(model="gpt-4o", messages=MESSAGES)

    client.chat.completions.create.assert_called_once_with(model="gpt-4o", messages=MESSAGES)
    assert result is not None


def test_cache_hit_skips_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_create(model="gpt-4o", messages=MESSAGES)
    adapter.chat_create(model="gpt-4o", messages=MESSAGES)

    assert client.chat.completions.create.call_count == 1


def test_different_messages_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_create(model="gpt-4o", messages=MESSAGES)
    adapter.chat_create(model="gpt-4o", messages=[{"role": "user", "content": "Bye"}])

    assert client.chat.completions.create.call_count == 2


def test_different_models_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_create(model="gpt-4o", messages=MESSAGES)
    adapter.chat_create(model="gpt-3.5-turbo", messages=MESSAGES)

    assert client.chat.completions.create.call_count == 2


async def test_achat_create_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    result = await adapter.achat_create(model="gpt-4o", messages=MESSAGES)

    assert result is not None
    client.chat.completions.create.assert_called_once()


async def test_achat_create_cache_hit(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    await adapter.achat_create(model="gpt-4o", messages=MESSAGES)
    await adapter.achat_create(model="gpt-4o", messages=MESSAGES)

    assert client.chat.completions.create.call_count == 1


def test_invalidate_model_forces_api_call(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_create(model="gpt-4o", messages=MESSAGES)
    adapter.invalidate_model("gpt-4o")
    adapter.chat_create(model="gpt-4o", messages=MESSAGES)

    assert client.chat.completions.create.call_count == 2


def test_stream_param_excluded_from_cache_key(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_create(model="gpt-4o", messages=MESSAGES, stream=False)
    adapter.chat_create(model="gpt-4o", messages=MESSAGES, stream=True)

    assert client.chat.completions.create.call_count == 1


def test_import_error_without_openai(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.openai_adapter._OPENAI_AVAILABLE", False):
        from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

        with pytest.raises(ImportError, match="openai"):
            OpenAICacheAdapter(MagicMock(), manager)
