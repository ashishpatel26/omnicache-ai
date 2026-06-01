# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Development setup:**
```bash
uv sync --dev
```

**Testing:**
```bash
uv run pytest                                                        # all tests
uv run pytest tests/layers/test_response_cache.py -v                # single test file
uv run pytest tests/ -k "test_cache_hit" -v                         # single test by name
uv run pytest --cov=omnicache_ai --cov-report=term-missing          # with coverage
```

**Linting & type checking:**
```bash
uv run ruff check omnicache_ai/
uv run ruff format omnicache_ai/
uv run mypy omnicache_ai/ --ignore-missing-imports
```

**Build:**
```bash
uv build
```

**Docs (local preview):**
```bash
uv run mkdocs serve
```

## Architecture

OmniCache-AI is a multi-layer caching system for AI agent pipelines. It intercepts calls to LLMs, embedding models, vector retrievers, and agent frameworks to return cached results instead of making redundant API calls.

### Data Flow

```
Framework Adapter → Middleware → Cache Layers → Backend (KV or Vector)
                                      ↓ (miss)
                              Actual API Call → Store in Cache → Return
```

### Core Layer (`omnicache_ai/core/`)

`CacheManager` is the central orchestrator — it wires together a KV backend, optional vector backend, `CacheKeyBuilder`, `TTLPolicy`, `EvictionPolicy`, and `InvalidationEngine`. All cache layer classes receive a `CacheManager` instance.

**Key building:** `CacheKeyBuilder` generates `{namespace}:{type_prefix}:{sha256_hash[:16]}` keys from deterministic serialization of inputs.

**Invalidation:** `InvalidationEngine` maintains a secondary tag→key mapping store, enabling bulk eviction of all entries tagged with a given tag (e.g., invalidate all entries for a session or model).

### Backends (`omnicache_ai/backends/`)

Two backend types defined by protocols in `base.py`:
- **`CacheBackend`** (KV): `get/set/delete/exists/clear/close()` — implemented by `InMemoryBackend` (LRU OrderedDict + RLock), `DiskBackend` (diskcache), `RedisBackend`
- **`VectorBackend`**: similarity search — implemented by `FAISSBackend` (IndexFlatIP on L2-normalized vectors) and `ChromaBackend`

Redis, FAISS, and Chroma are optional extras installed via `pip install omnicache-ai[redis]`, `[vector-faiss]`, or `[vector-chroma]`.

### Cache Layers (`omnicache_ai/layers/`)

Each layer class wraps a `CacheManager` and handles one type of cached artifact:

| Layer | Key Inputs | Serialization |
|-------|-----------|---------------|
| `ResponseCache` | model + messages + params | pickle |
| `EmbeddingCache` | model + text | `np.tobytes()` |
| `RetrievalCache` | query + retriever + top_k | pickle |
| `ContextCache` | session_id + turn_index | pickle |
| `SemanticCache` | query embedding (cosine ≥ 0.95 threshold) | pickle |

`SemanticCache` uses the vector backend to find semantically similar prior queries and returns their cached answers without exact key matching.

### Middleware (`omnicache_ai/middleware/`)

Decorator-pattern wrappers (`LLMMiddleware`, `AsyncLLMMiddleware`, `EmbeddingMiddleware`, `RetrieverMiddleware`) that intercept any callable without changing its signature. Used when not integrating with a full framework adapter.

### Adapters (`omnicache_ai/adapters/`)

Framework-specific integrations that hook into native extension points:
- **LangChain**: overrides `BaseCache.lookup/update` (+ async variants)
- **LangGraph**: overrides `BaseCheckpointSaver.get_tuple/put/list`
- **AutoGen**: wraps `AssistantAgent.run/arun()`
- **CrewAI**: wraps `Crew.kickoff/kickoff_async()`
- **Agno**: wraps `Agent.run/arun()`
- **A2A**: wraps `process/aprocess()` or uses `@wrap` decorator

### Configuration (`omnicache_ai/config/settings.py`)

`OmnicacheSettings` is a dataclass with 12-factor env var support. Key variables:
- `OMNICACHE_BACKEND` — `memory` (default), `disk`, or `redis`
- `OMNICACHE_REDIS_URL`, `OMNICACHE_DISK_PATH`
- `OMNICACHE_SEMANTIC_THRESHOLD` — cosine similarity cutoff (default: 0.95)
- `OMNICACHE_TTL_{EMBEDDING,RETRIEVAL,CONTEXT,RESPONSE}` — per-layer TTL overrides
- `OMNICACHE_NAMESPACE` — key prefix (default: `omnicache`)

### Public API

17 classes exported from `omnicache_ai/__init__.py`. Optional backends/adapters are imported dynamically based on installed extras — import errors for missing extras should be caught gracefully.

### Testing Conventions

- `tests/conftest.py` provides shared fixtures: `backend` (parametrized memory+disk), `key_builder`, `cache_manager`, `mock_embed` (deterministic normalized embedding via hashed seed)
- `asyncio_mode = "auto"` in pyproject.toml — async tests need no special decorator
- CI runs a matrix of Ubuntu/Windows/macOS × Python 3.12/3.13
- mypy runs in strict mode; ruff line-length is 100, target Python 3.12
