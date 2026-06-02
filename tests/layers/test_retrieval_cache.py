"""Tests for RetrievalCache."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder
from omnicache_ai.layers.retrieval_cache import RetrievalCache


@pytest.fixture
def cache() -> RetrievalCache:
    manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))
    return RetrievalCache(manager)


DOCS = [{"id": "1", "text": "About RAG"}, {"id": "2", "text": "About embeddings"}]


def test_get_miss(cache: RetrievalCache) -> None:
    assert cache.get("What is RAG?") is None


def test_set_and_get_roundtrip(cache: RetrievalCache) -> None:
    cache.set("What is RAG?", DOCS)
    result = cache.get("What is RAG?")
    assert result == DOCS


def test_different_queries_independent(cache: RetrievalCache) -> None:
    cache.set("Query A", DOCS)
    assert cache.get("Query B") is None


def test_different_retriever_ids_produce_different_keys(cache: RetrievalCache) -> None:
    cache.set("What is RAG?", DOCS, retriever_id="retriever-1")
    cache.set("What is RAG?", [{"id": "3"}], retriever_id="retriever-2")

    assert cache.get("What is RAG?", retriever_id="retriever-1") == DOCS
    assert cache.get("What is RAG?", retriever_id="retriever-2") == [{"id": "3"}]


def test_different_top_k_produce_different_keys(cache: RetrievalCache) -> None:
    cache.set("What is RAG?", DOCS, top_k=5)
    cache.set("What is RAG?", DOCS[:1], top_k=1)

    assert cache.get("What is RAG?", top_k=5) == DOCS
    assert cache.get("What is RAG?", top_k=1) == DOCS[:1]


def test_get_or_retrieve_cache_miss_calls_fn(cache: RetrievalCache) -> None:
    retrieve_fn = MagicMock(return_value=DOCS)

    result = cache.get_or_retrieve("What is RAG?", retrieve_fn, top_k=5)

    retrieve_fn.assert_called_once_with("What is RAG?", 5)
    assert result == DOCS


def test_get_or_retrieve_cache_hit_skips_fn(cache: RetrievalCache) -> None:
    retrieve_fn = MagicMock(return_value=DOCS)

    cache.get_or_retrieve("What is RAG?", retrieve_fn)
    result = cache.get_or_retrieve("What is RAG?", retrieve_fn)

    assert retrieve_fn.call_count == 1
    assert result == DOCS


def test_get_or_retrieve_stores_result(cache: RetrievalCache) -> None:
    retrieve_fn = MagicMock(return_value=DOCS)

    cache.get_or_retrieve("What is RAG?", retrieve_fn)
    result = cache.get("What is RAG?")

    assert result == DOCS
