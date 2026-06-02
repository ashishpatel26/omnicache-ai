"""Tests for LlamaIndex adapters — mocked, no real LlamaIndex needed."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder


def _fake_complete_response() -> SimpleNamespace:
    return SimpleNamespace(text="4")


def _fake_query_response() -> SimpleNamespace:
    return SimpleNamespace(response="RAG is retrieval-augmented generation")


def _make_llm_adapter(llm: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.llamaindex_adapter._LLAMAINDEX_AVAILABLE", True):
        with patch("omnicache_ai.adapters.llamaindex_adapter._LlamaLLM", object):
            from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

            return LlamaIndexLLMCacheAdapter(llm, manager)


def _make_query_adapter(engine: MagicMock, manager: CacheManager):
    with patch("omnicache_ai.adapters.llamaindex_adapter._LLAMAINDEX_AVAILABLE", True):
        from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

        return LlamaIndexQueryCacheAdapter(engine, manager)


@pytest.fixture
def manager() -> CacheManager:
    return CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))


# --- LLM adapter ---


def test_complete_cache_miss(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.complete.return_value = _fake_complete_response()
    adapter = _make_llm_adapter(llm, manager)

    result = adapter.complete("What is 2+2?")

    llm.complete.assert_called_once_with("What is 2+2?")
    assert result is not None


def test_complete_cache_hit(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.complete.return_value = _fake_complete_response()
    adapter = _make_llm_adapter(llm, manager)

    adapter.complete("What is 2+2?")
    adapter.complete("What is 2+2?")

    assert llm.complete.call_count == 1


def test_different_prompts_produce_cache_miss(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.complete.return_value = _fake_complete_response()
    adapter = _make_llm_adapter(llm, manager)

    adapter.complete("What is 2+2?")
    adapter.complete("What is 3+3?")

    assert llm.complete.call_count == 2


async def test_acomplete_cache_miss(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.acomplete = AsyncMock(return_value=_fake_complete_response())
    adapter = _make_llm_adapter(llm, manager)

    result = await adapter.acomplete("What is 2+2?")

    assert result is not None
    llm.acomplete.assert_called_once()


async def test_acomplete_cache_hit(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.acomplete = AsyncMock(return_value=_fake_complete_response())
    adapter = _make_llm_adapter(llm, manager)

    await adapter.acomplete("What is 2+2?")
    await adapter.acomplete("What is 2+2?")

    assert llm.acomplete.call_count == 1


def test_chat_cache_miss(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.chat.return_value = _fake_complete_response()
    adapter = _make_llm_adapter(llm, manager)

    adapter.chat(["Hello"])

    llm.chat.assert_called_once()


def test_chat_cache_hit(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.chat.return_value = _fake_complete_response()
    adapter = _make_llm_adapter(llm, manager)

    adapter.chat(["Hello"])
    adapter.chat(["Hello"])

    assert llm.chat.call_count == 1


def test_stream_complete_not_cached(manager: CacheManager) -> None:
    llm = MagicMock()
    llm.stream_complete.return_value = iter(["chunk1", "chunk2"])
    adapter = _make_llm_adapter(llm, manager)

    adapter.stream_complete("prompt")
    adapter.stream_complete("prompt")

    assert llm.stream_complete.call_count == 2


def test_llm_import_error(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.llamaindex_adapter._LLAMAINDEX_AVAILABLE", False):
        from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

        with pytest.raises(ImportError, match="llama-index-core"):
            LlamaIndexLLMCacheAdapter(MagicMock(), manager)


# --- QueryEngine adapter ---


def test_query_cache_miss(manager: CacheManager) -> None:
    engine = MagicMock()
    engine.query.return_value = _fake_query_response()
    adapter = _make_query_adapter(engine, manager)

    result = adapter.query("What is RAG?")

    engine.query.assert_called_once_with("What is RAG?")
    assert result is not None


def test_query_cache_hit(manager: CacheManager) -> None:
    engine = MagicMock()
    engine.query.return_value = _fake_query_response()
    adapter = _make_query_adapter(engine, manager)

    adapter.query("What is RAG?")
    adapter.query("What is RAG?")

    assert engine.query.call_count == 1


async def test_aquery_cache_miss(manager: CacheManager) -> None:
    engine = MagicMock()
    engine.aquery = AsyncMock(return_value=_fake_query_response())
    adapter = _make_query_adapter(engine, manager)

    result = await adapter.aquery("What is RAG?")

    assert result is not None
    engine.aquery.assert_called_once()


async def test_aquery_cache_hit(manager: CacheManager) -> None:
    engine = MagicMock()
    engine.aquery = AsyncMock(return_value=_fake_query_response())
    adapter = _make_query_adapter(engine, manager)

    await adapter.aquery("What is RAG?")
    await adapter.aquery("What is RAG?")

    assert engine.aquery.call_count == 1


def test_query_import_error(manager: CacheManager) -> None:
    with patch("omnicache_ai.adapters.llamaindex_adapter._LLAMAINDEX_AVAILABLE", False):
        from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

        with pytest.raises(ImportError, match="llama-index-core"):
            LlamaIndexQueryCacheAdapter(MagicMock(), manager)
