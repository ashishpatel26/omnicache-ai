# Changelog

All notable changes to **omnicache-ai** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-01

### Added
- **CacheMetrics**: hit/miss/eviction/set counters with `hit_rate` property; exposed via `manager.metrics`
- **Serializer protocol**: `PickleSerializer` (default) + `JsonSerializer`; all cache layers accept `serializer=` param
- **StampedeShield**: per-key `threading.Lock` wired into `ResponseCache.get_or_generate()` — prevents cache stampede under concurrency
- **TieredBackend**: L1 (memory) + L2 (Redis/disk) with automatic L2→L1 promotion on read
- **AsyncCacheBackend** protocol + **AsyncInMemoryBackend**: native async backends for FastAPI / async LangGraph
- **OpenAICacheAdapter**: wraps `client.chat.completions.create` (sync + async)
- **AnthropicCacheAdapter**: wraps `client.messages.create` (sync + async)
- **Compressor protocol**: `GzipCompressor` + `NoopCompressor` (default); wired into `CacheManager` — reduces storage for large LLM responses
- **StreamingResponseCache**: buffers streaming LLM output, replays chunks from cache as generator (sync + async)
- **CLI**: `python -m omnicache_ai stats|flush|inspect <key>` (was a stub)
- **pre-commit**: ruff + ruff-format + mypy + standard file checks; hooks installed at `.pre-commit-config.yaml`
- **Dockerfile**: slim Python 3.12 image with uv for containerized usage
- CI: pre-commit runs on ubuntu/3.12 leg in `ci.yml`

### Fixed
- **FAISSBackend.delete()**: switched `IndexFlatIP` → `IndexIDMap2` — deleted vectors now actually removed from the index (previously caused stale semantic matches)
- **EvictionPolicy**: was exported but never used; now wired into `CacheManager.from_settings()` and `InMemoryBackend`
- **LangChainCacheAdapter.clear()**: was a silent no-op; now calls `manager.clear()`

## [0.1.0] - 2026-03-21

### Added
- **Core**: `CacheManager`, `CacheKeyBuilder`, `TTLPolicy`, `EvictionPolicy`, `InvalidationEngine`
- **Backends**: `InMemoryBackend` (LRU), `DiskBackend` (diskcache), `RedisBackend`, `FAISSBackend`, `ChromaBackend`
- **Cache layers**: `EmbeddingCache`, `RetrievalCache`, `ContextCache`, `ResponseCache`, `SemanticCache`
- **Middleware**: `LLMMiddleware`, `AsyncLLMMiddleware`, `EmbeddingMiddleware`, `RetrieverMiddleware`
- **Adapters**: LangChain, LangGraph (0.x + 1.x), AutoGen (0.2.x + 0.4+), CrewAI, Agno, A2A
- **Config**: `OmnicacheSettings` with environment variable support
- **CLI**: `omnicache` entry point
- Tag-based invalidation engine
- Semantic similarity cache (exact + vector cosine lookup)
- Full test suite with pytest
- CI/CD via GitHub Actions
- README, COOKBOOK, and publishing recipes for PyPI / conda-forge
