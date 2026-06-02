"""Tests for StreamingResponseCache."""

from __future__ import annotations

import pytest

from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.key_builder import CacheKeyBuilder
from omnicache_ai.layers.streaming_cache import StreamingResponseCache


@pytest.fixture
def cache() -> StreamingResponseCache:
    manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))
    return StreamingResponseCache(manager)


MESSAGES = [{"role": "user", "content": "Hello"}]
CHUNKS = ["Hello", " ", "world", "!"]


def _stream_fn(messages):
    yield from CHUNKS


async def _async_stream_fn(messages):
    for chunk in CHUNKS:
        yield chunk


def test_get_or_stream_cache_miss_yields_all_chunks(cache: StreamingResponseCache) -> None:
    result = list(cache.get_or_stream(MESSAGES, _stream_fn, model_id="gpt-4o"))
    assert result == CHUNKS


def test_get_or_stream_cache_hit_replays_chunks(cache: StreamingResponseCache) -> None:
    call_count = 0

    def counting_stream(messages):
        nonlocal call_count
        call_count += 1
        yield from CHUNKS

    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o"))
    result = list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o"))

    assert call_count == 1
    assert result == CHUNKS


def test_different_messages_produce_different_keys(cache: StreamingResponseCache) -> None:
    call_count = 0

    def counting_stream(messages):
        nonlocal call_count
        call_count += 1
        yield from CHUNKS

    other_messages = [{"role": "user", "content": "Bye"}]
    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o"))
    list(cache.get_or_stream(other_messages, counting_stream, model_id="gpt-4o"))

    assert call_count == 2


def test_different_model_ids_produce_different_keys(cache: StreamingResponseCache) -> None:
    call_count = 0

    def counting_stream(messages):
        nonlocal call_count
        call_count += 1
        yield from CHUNKS

    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o"))
    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-3.5-turbo"))

    assert call_count == 2


def test_chunk_joiner_applied_on_store(cache: StreamingResponseCache) -> None:
    manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="t"))
    joined_cache = StreamingResponseCache(manager, chunk_joiner="".join)

    list(joined_cache.get_or_stream(MESSAGES, _stream_fn, model_id="gpt-4o"))
    result = list(joined_cache.get_or_stream(MESSAGES, _stream_fn, model_id="gpt-4o"))

    # chunk_joiner joins into a single string — replayed as [string]
    assert result == ["Hello world!"]


async def test_aget_or_stream_cache_miss(cache: StreamingResponseCache) -> None:
    result = []
    async for chunk in cache.aget_or_stream(MESSAGES, _async_stream_fn, model_id="gpt-4o"):
        result.append(chunk)
    assert result == CHUNKS


async def test_aget_or_stream_cache_hit(cache: StreamingResponseCache) -> None:
    call_count = 0

    async def counting_async_stream(messages):
        nonlocal call_count
        call_count += 1
        for chunk in CHUNKS:
            yield chunk

    result1 = []
    async for chunk in cache.aget_or_stream(MESSAGES, counting_async_stream, model_id="gpt-4o"):
        result1.append(chunk)

    result2 = []
    async for chunk in cache.aget_or_stream(MESSAGES, counting_async_stream, model_id="gpt-4o"):
        result2.append(chunk)

    assert call_count == 1
    assert result1 == result2 == CHUNKS


def test_params_discriminate_cache_key(cache: StreamingResponseCache) -> None:
    call_count = 0

    def counting_stream(messages):
        nonlocal call_count
        call_count += 1
        yield from CHUNKS

    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o", params={"temp": 0.5}))
    list(cache.get_or_stream(MESSAGES, counting_stream, model_id="gpt-4o", params={"temp": 1.0}))

    assert call_count == 2
