"""Tests for GeminiCacheAdapter — mocked, no real Google Gemini SDK needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.invalidation import InvalidationEngine
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _fake_response():
    return SimpleNamespace(text="Paris", candidates=[])


def _make_adapter(model: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.gemini_adapter._GEMINI_AVAILABLE", True):
        from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

        return GeminiCacheAdapter(model, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="t"),
        invalidation_engine=InvalidationEngine(InMemoryBackend()),
    )


@pytest.fixture
def mock_model() -> MagicMock:
    model = MagicMock()
    model.model_name = "gemini-2.0-flash"
    model.generate_content.return_value = _fake_response()
    return model


def test_generate_content_cache_miss(manager: CacheManager, mock_model: MagicMock) -> None:
    adapter = _make_adapter(mock_model, manager)

    result = adapter.generate_content("What is the capital of France?")

    mock_model.generate_content.assert_called_once_with("What is the capital of France?")
    assert result is not None


def test_generate_content_cache_hit(manager: CacheManager, mock_model: MagicMock) -> None:
    adapter = _make_adapter(mock_model, manager)

    adapter.generate_content("What is the capital of France?")
    adapter.generate_content("What is the capital of France?")

    assert mock_model.generate_content.call_count == 1


def test_different_prompts_produce_cache_miss(manager: CacheManager, mock_model: MagicMock) -> None:
    adapter = _make_adapter(mock_model, manager)

    adapter.generate_content("What is the capital of France?")
    adapter.generate_content("What is the capital of Germany?")

    assert mock_model.generate_content.call_count == 2


def test_list_contents_keyed_correctly(manager: CacheManager, mock_model: MagicMock) -> None:
    adapter = _make_adapter(mock_model, manager)

    contents = [{"role": "user", "parts": ["Hello"]}]
    adapter.generate_content(contents)
    adapter.generate_content(contents)

    assert mock_model.generate_content.call_count == 1


async def test_agenerate_content_cache_miss(manager: CacheManager, mock_model: MagicMock) -> None:
    mock_model.generate_content_async = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(mock_model, manager)

    result = await adapter.agenerate_content("What is the capital of France?")

    assert result is not None
    mock_model.generate_content_async.assert_called_once()


async def test_agenerate_content_cache_hit(manager: CacheManager, mock_model: MagicMock) -> None:
    mock_model.generate_content_async = AsyncMock(return_value=_fake_response())
    adapter = _make_adapter(mock_model, manager)

    await adapter.agenerate_content("What is the capital of France?")
    await adapter.agenerate_content("What is the capital of France?")

    assert mock_model.generate_content_async.call_count == 1


def test_invalidate_model(manager: CacheManager, mock_model: MagicMock) -> None:
    adapter = _make_adapter(mock_model, manager)

    adapter.generate_content("What is the capital of France?")
    adapter.invalidate_model()
    adapter.generate_content("What is the capital of France?")

    assert mock_model.generate_content.call_count == 2


def test_getattr_delegates_to_model(manager: CacheManager, mock_model: MagicMock) -> None:
    mock_model.some_attr = "value"
    adapter = _make_adapter(mock_model, manager)

    assert adapter.some_attr == "value"


def test_import_error_without_gemini(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.gemini_adapter._GEMINI_AVAILABLE", False):
        from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

        with pytest.raises(ImportError, match="google-generativeai"):
            GeminiCacheAdapter(MagicMock(), manager)
