"""Tests for MistralCacheAdapter — mocked, no real Mistral SDK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


MESSAGES = [{"role": "user", "content": "Hello"}]
MODEL = "mistral-large-latest"


def _fake_response():
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Bonjour!"))])


def _make_adapter(client: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.mistral_adapter._MISTRAL_AVAILABLE", True):
        from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

        return MistralCacheAdapter(client, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


def test_cache_miss_calls_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    result = adapter.chat_complete(model=MODEL, messages=MESSAGES)

    client.chat.complete.assert_called_once_with(model=MODEL, messages=MESSAGES)
    assert result is not None


def test_cache_hit_skips_api(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_complete(model=MODEL, messages=MESSAGES)
    adapter.chat_complete(model=MODEL, messages=MESSAGES)

    assert client.chat.complete.call_count == 1


def test_different_messages_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_complete(model=MODEL, messages=MESSAGES)
    adapter.chat_complete(model=MODEL, messages=[{"role": "user", "content": "Bye"}])

    assert client.chat.complete.call_count == 2


def test_different_models_produce_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_complete(model=MODEL, messages=MESSAGES)
    adapter.chat_complete(model="mistral-small-latest", messages=MESSAGES)

    assert client.chat.complete.call_count == 2


async def test_achat_complete_cache_miss(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete_async = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    result = await adapter.achat_complete(model=MODEL, messages=MESSAGES)

    assert result is not None
    client.chat.complete_async.assert_called_once()


async def test_achat_complete_cache_hit(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete_async = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(client, manager)

    await adapter.achat_complete(model=MODEL, messages=MESSAGES)
    await adapter.achat_complete(model=MODEL, messages=MESSAGES)

    assert client.chat.complete_async.call_count == 1


def test_stream_excluded_from_cache_key(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_complete(model=MODEL, messages=MESSAGES, stream=False)
    adapter.chat_complete(model=MODEL, messages=MESSAGES, stream=True)

    assert client.chat.complete.call_count == 1


def test_invalidate_model_forces_api_call(manager: CacheManager) -> None:
    client = MagicMock()
    client.chat.complete.return_value = _fake_response()
    adapter = _make_adapter(client, manager)

    adapter.chat_complete(model=MODEL, messages=MESSAGES)
    adapter.invalidate_model(MODEL)
    adapter.chat_complete(model=MODEL, messages=MESSAGES)

    assert client.chat.complete.call_count == 2


def test_import_error_without_mistral(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.mistral_adapter._MISTRAL_AVAILABLE", False):
        from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

        with pytest.raises(ImportError, match="mistralai"):
            MistralCacheAdapter(MagicMock(), manager)
