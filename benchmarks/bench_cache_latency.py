"""Latency benchmarks for omnicache-ai cache operations.

Run with:
    uv run pytest benchmarks/ --benchmark-only -v

Or compare backends:
    uv run pytest benchmarks/ --benchmark-compare
"""

from __future__ import annotations

import pickle

import pytest

from omnicache_ai.backends.disk_backend import DiskBackend
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.tiered_backend import TieredBackend
from omnicache_ai.core.cache_manager import CacheManager
from omnicache_ai.core.compressor import GzipCompressor, NoopCompressor
from omnicache_ai.core.key_builder import CacheKeyBuilder
from omnicache_ai.core.serializer import JsonSerializer, PickleSerializer
from omnicache_ai.layers.response_cache import ResponseCache
from omnicache_ai.layers.retrieval_cache import RetrievalCache

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def memory_backend():
    b = InMemoryBackend(max_size=10_000)
    yield b
    b.close()


@pytest.fixture
def disk_backend(tmp_path):
    b = DiskBackend(str(tmp_path / "bench_cache"))
    yield b
    b.close()


@pytest.fixture
def tiered_backend(tmp_path):
    b = TieredBackend(
        l1=InMemoryBackend(max_size=1_000),
        l2=DiskBackend(str(tmp_path / "l2")),
        l1_ttl=300,
    )
    yield b
    b.close()


@pytest.fixture
def manager(memory_backend):
    return CacheManager(backend=memory_backend, key_builder=CacheKeyBuilder())


# ---------------------------------------------------------------------------
# Raw backend — set / get
# ---------------------------------------------------------------------------


def test_memory_backend_set(benchmark, memory_backend):
    """Raw InMemoryBackend.set latency."""
    value = pickle.dumps({"answer": "Paris", "tokens": 42})
    benchmark(memory_backend.set, "bench:key", value)


def test_memory_backend_get_hit(benchmark, memory_backend):
    """Raw InMemoryBackend.get latency on cache hit."""
    value = pickle.dumps({"answer": "Paris"})
    memory_backend.set("bench:key", value)
    benchmark(memory_backend.get, "bench:key")


def test_memory_backend_get_miss(benchmark, memory_backend):
    """Raw InMemoryBackend.get latency on cache miss."""
    benchmark(memory_backend.get, "bench:nonexistent")


def test_disk_backend_set(benchmark, disk_backend):
    """DiskBackend.set latency."""
    value = pickle.dumps({"answer": "Paris"})
    benchmark(disk_backend.set, "bench:key", value)


def test_disk_backend_get_hit(benchmark, disk_backend):
    """DiskBackend.get latency on cache hit."""
    value = pickle.dumps({"answer": "Paris"})
    disk_backend.set("bench:key", value)
    benchmark(disk_backend.get, "bench:key")


def test_tiered_get_l1_hit(benchmark, tiered_backend):
    """TieredBackend.get latency when value is in L1 (in-memory)."""
    value = pickle.dumps({"answer": "Paris"})
    tiered_backend.set("bench:key", value)
    benchmark(tiered_backend.get, "bench:key")


# ---------------------------------------------------------------------------
# Key building
# ---------------------------------------------------------------------------


def test_key_builder(benchmark):
    """CacheKeyBuilder.build latency."""
    kb = CacheKeyBuilder(namespace="bench")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]
    benchmark(kb.build, "response", str(messages), extra={"model": "gpt-4o"})


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


SAMPLE_RESPONSE = {
    "model": "gpt-4o",
    "choices": [{"message": {"role": "assistant", "content": "Paris"}}],
    "usage": {"prompt_tokens": 20, "completion_tokens": 5},
}


def test_pickle_serialize(benchmark):
    s = PickleSerializer()
    benchmark(s.dumps, SAMPLE_RESPONSE)


def test_pickle_deserialize(benchmark):
    s = PickleSerializer()
    data = s.dumps(SAMPLE_RESPONSE)
    benchmark(s.loads, data)


def test_json_serialize(benchmark):
    s = JsonSerializer()
    benchmark(s.dumps, SAMPLE_RESPONSE)


def test_json_deserialize(benchmark):
    s = JsonSerializer()
    data = s.dumps(SAMPLE_RESPONSE)
    benchmark(s.loads, data)


# ---------------------------------------------------------------------------
# Compression
# ---------------------------------------------------------------------------

LARGE_RESPONSE = {"content": "A" * 4096, "tokens": 1000}


def test_gzip_compress(benchmark):
    c = GzipCompressor(level=6)
    data = pickle.dumps(LARGE_RESPONSE)
    benchmark(c.compress, data)


def test_gzip_decompress(benchmark):
    c = GzipCompressor(level=6)
    data = c.compress(pickle.dumps(LARGE_RESPONSE))
    benchmark(c.decompress, data)


def test_noop_compress(benchmark):
    c = NoopCompressor()
    data = pickle.dumps(LARGE_RESPONSE)
    benchmark(c.compress, data)


# ---------------------------------------------------------------------------
# High-level layers
# ---------------------------------------------------------------------------


MESSAGES = [{"role": "user", "content": "What is the capital of France?"}]


def test_response_cache_hit(benchmark, manager):
    """ResponseCache end-to-end: key build + deserialize on cache hit."""
    cache = ResponseCache(manager)
    fake_response = {"choices": [{"message": {"content": "Paris"}}]}
    cache.set("gpt-4o", MESSAGES, fake_response)

    benchmark(cache.get, "gpt-4o", MESSAGES)


def test_response_cache_miss(benchmark, manager):
    """ResponseCache end-to-end on cache miss."""
    cache = ResponseCache(manager)
    benchmark(cache.get, "gpt-4o", MESSAGES)


def test_retrieval_cache_hit(benchmark, manager):
    """RetrievalCache end-to-end on cache hit."""
    cache = RetrievalCache(manager)
    docs = [{"id": str(i), "text": f"Document {i}"} for i in range(10)]
    cache.set("What is RAG?", docs)

    benchmark(cache.get, "What is RAG?")


# ---------------------------------------------------------------------------
# Token savings calculator
# ---------------------------------------------------------------------------


def test_token_savings_estimate():
    """Not a benchmark — prints estimated savings for documentation."""
    avg_prompt_tokens = 500
    hit_rate = 0.35
    cost_per_1m = 3.0  # Claude Sonnet price per 1M input tokens
    requests_per_month = 1_000_000

    cached_requests = requests_per_month * hit_rate
    tokens_saved = cached_requests * avg_prompt_tokens
    usd_saved = (tokens_saved / 1_000_000) * cost_per_1m

    assert tokens_saved > 0
    assert usd_saved > 0

    # At 35% hit rate, 1M requests, 500 tokens avg:
    # 175M tokens saved = $525/month at Sonnet pricing
    print(
        f"\nEstimated savings at {hit_rate:.0%} hit rate, "
        f"{requests_per_month:,} req/month, "
        f"{avg_prompt_tokens} tokens/req:\n"
        f"  Tokens saved: {tokens_saved:,.0f}\n"
        f"  Cost saved:   ${usd_saved:,.2f}/month"
    )
