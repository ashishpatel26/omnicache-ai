---
title: "API Reference"
---

# API Reference

Complete class and method reference for every public symbol in omnicache-ai v0.3.0.

---

## Core

### `CacheManager`

Central orchestrator. Wires backend, key builder, TTL policy, compressor, metrics, and optional vector backend.

```python
from omnicache_ai import CacheManager
```

**Constructor:**

```python
CacheManager(
    backend: CacheBackend,
    key_builder: CacheKeyBuilder,
    ttl_policy: TTLPolicy | None = None,
    eviction_policy: EvictionPolicy | None = None,
    vector_backend: VectorBackend | None = None,
    invalidation_engine: InvalidationEngine | None = None,
    semantic_threshold: float = 0.95,
    compressor: Compressor | None = None,
)
```

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get` | `(key, semantic=False, vector=None)` | `Any \| None` | Exact or semantic lookup |
| `set` | `(key, value, ttl=None, vector=None, tags=None, cache_type="response")` | `None` | Store value |
| `delete` | `(key)` | `None` | Remove key |
| `exists` | `(key)` | `bool` | Check key presence |
| `invalidate` | `(tag)` | `int` | Bulk remove by tag |
| `clear` | `()` | `None` | Flush all |
| `close` | `()` | `None` | Release resources |
| `for_tenant` | `(tenant_id: str)` | `CacheManager` | Scoped manager with per-tenant key namespace |
| `from_settings` | `(settings: OmnicacheSettings)` | `CacheManager` | Factory constructor |

**Properties:** `key_builder`, `ttl_policy`, `metrics`

---

### `CacheMetrics`

Thread-safe counters. Accessed via `manager.metrics`.

```python
from omnicache_ai import CacheMetrics
```

| Field | Type | Description |
|---|---|---|
| `hits` | `int` | Cache hits |
| `misses` | `int` | Cache misses |
| `evictions` | `int` | LRU evictions |
| `sets` | `int` | Cache writes |
| `provider_cache_hits` | `int` | Server-side prompt cache hits |
| `estimated_tokens_saved` | `int` | Tokens saved via provider caching |
| `estimated_cost_saved_usd` | `float` | Estimated USD saved |

| Property / Method | Returns | Description |
|---|---|---|
| `hit_rate` | `float` | `hits / (hits + misses)` |
| `miss_rate` | `float` | `1.0 - hit_rate` |
| `snapshot()` | `dict[str, Any]` | JSON-serializable dict of all fields |
| `reset()` | `None` | Zero all counters |

---

### `CacheKeyBuilder`

```python
from omnicache_ai import CacheKeyBuilder
```

`__init__(namespace="omnicache", algo="sha256")`

| Method | Signature | Returns |
|---|---|---|
| `build` | `(cache_type, content, extra=None)` | `str` |

Key format: `{namespace}:{type_prefix}:{hash[:16]}`

---

### `Serializer` / `PickleSerializer` / `JsonSerializer`

```python
from omnicache_ai import Serializer, PickleSerializer, JsonSerializer
```

Protocol — implement `dumps(value) -> bytes` and `loads(data) -> Any`.

---

### `Compressor` / `GzipCompressor` / `NoopCompressor`

```python
from omnicache_ai import Compressor, GzipCompressor, NoopCompressor
```

Protocol — implement `compress(data: bytes) -> bytes` and `decompress(data: bytes) -> bytes`.

`GzipCompressor(level: int = 6)` — level 0–9.

---

### `StampedeShield`

```python
from omnicache_ai import StampedeShield
```

`__init__(timeout: float = 30.0)`

`shield.lock(key: str)` — context manager. Acquires per-key lock; releases on exit.

---

### `RequestConfig`

```python
from omnicache_ai import RequestConfig
```

| Field | Type | Default | Description |
|---|---|---|---|
| `ttl` | `int \| None` | `None` | Per-request TTL override |
| `semantic_threshold` | `float \| None` | `None` | Per-request threshold override |
| `skip_cache` | `bool` | `False` | Bypass cache entirely |
| `tags` | `list[str]` | `[]` | Extra invalidation tags |
| `namespace_prefix` | `str \| None` | `None` | Extra key prefix |

---

### `CacheWarmer`

```python
from omnicache_ai import CacheWarmer
```

`__init__(cache: ResponseCache)`

| Method | Returns | Description |
|---|---|---|
| `warm_from_queries(queries, generate_fn, model_id, ttl, skip_existing)` | `dict[str, str]` | Warm from list |
| `warm_from_file(path, generate_fn, model_id, ttl, query_column, skip_existing)` | `dict[str, str]` | Warm from CSV |
| `awarm_from_queries(...)` | `dict[str, str]` | Async variant |

---

### `TTLPolicy`

```python
from omnicache_ai import TTLPolicy
```

`__init__(default_ttl=3600, per_type={})` · `ttl_for(cache_type) -> int | None` · `from_settings(settings)`

---

### `EvictionPolicy`

```python
from omnicache_ai import EvictionPolicy
```

| Field | Type | Default |
|---|---|---|
| `strategy` | `"lru" \| "ttl_only"` | `"lru"` |
| `max_entries` | `int \| None` | `None` |
| `max_bytes` | `int \| None` | `None` |

---

### `InvalidationEngine`

```python
from omnicache_ai import InvalidationEngine
```

`__init__(tag_store: CacheBackend)` · `register(key, tags)` · `invalidate_tag(tag, backend) -> int` · `invalidate_key(key, backend)`

---

### `OmnicacheSettings`

```python
from omnicache_ai import OmnicacheSettings
```

| Field | Type | Default |
|---|---|---|
| `backend` | `"memory" \| "disk" \| "redis"` | `"memory"` |
| `redis_url` | `str` | `"redis://localhost:6379/0"` |
| `disk_path` | `str` | `"/tmp/omnicache"` |
| `default_ttl` | `int \| None` | `3600` |
| `semantic_threshold` | `float` | `0.95` |
| `vector_backend` | `"faiss" \| "chroma" \| "none"` | `"none"` |
| `embedding_dim` | `int` | `1536` |
| `max_memory_entries` | `int` | `10000` |
| `namespace` | `str` | `"omnicache"` |
| `ttl_embedding` | `int \| None` | `86400` |
| `ttl_retrieval` | `int \| None` | `3600` |
| `ttl_context` | `int \| None` | `1800` |
| `ttl_response` | `int \| None` | `600` |

`from_env() -> OmnicacheSettings`

---

## Observability

### `PrometheusExporter`

```python
from omnicache_ai.core.exporters import PrometheusExporter
```

`__init__(metrics, port=9090, namespace="omnicache")` · `start(sync_interval=5.0)` · `stop()`

### `OpenTelemetryExporter`

```python
from omnicache_ai.core.exporters import OpenTelemetryExporter
```

`__init__(metrics, endpoint="http://localhost:4317", export_interval_ms=10_000)` · `start()`

---

## Backends

### Protocols

```python
from omnicache_ai.backends.base import CacheBackend, VectorBackend
from omnicache_ai.backends.async_base import AsyncCacheBackend
```

**CacheBackend:** `get / set / delete / exists / clear / close` (sync)

**AsyncCacheBackend:** same methods, all `async`

**VectorBackend:** `add(key, vector, metadata) / search(vector, top_k=1) -> list[tuple[str, float]] / delete / clear / close`

---

### Key-Value Backends

| Class | Import | Constructor |
|---|---|---|
| `InMemoryBackend` | `from omnicache_ai import InMemoryBackend` | `(max_size=10_000, eviction_policy=None, on_evict=None)` |
| `AsyncInMemoryBackend` | `from omnicache_ai import AsyncInMemoryBackend` | `(max_size=10_000)` |
| `TieredBackend` | `from omnicache_ai import TieredBackend` | `(l1, l2, l1_ttl=300)` |
| `DiskBackend` | `from omnicache_ai import DiskBackend` | `(directory, size_limit=2**30)` |
| `RedisBackend` | `from omnicache_ai.backends.redis_backend import RedisBackend` | `(url="redis://localhost:6379/0", key_prefix="")` |

### Vector Backends

| Class | Import | Constructor |
|---|---|---|
| `FAISSBackend` | `from omnicache_ai.backends.vector_backend import FAISSBackend` | `(dim, normalize=True)` |
| `ChromaBackend` | `from omnicache_ai.backends.vector_backend import ChromaBackend` | `(collection_name="omnicache", persist_directory=None)` |
| `QdrantBackend` | `from omnicache_ai.backends.vector_backend import QdrantBackend` | `(url=":memory:", collection="omnicache", api_key=None, dim=1536)` |
| `WeaviateBackend` | `from omnicache_ai.backends.vector_backend import WeaviateBackend` | `(url=None, api_key=None, class_name="OmnicacheEntry")` |

---

## Cache Layers

### `ResponseCache`

```python
from omnicache_ai import ResponseCache
```

`__init__(manager, serializer=None, stampede_shield=None)`

| Method | Signature | Returns |
|---|---|---|
| `get` | `(messages, model_id="default", params=None)` | `Any \| None` |
| `set` | `(messages, response, model_id, params, ttl, tags)` | `None` |
| `get_or_generate` | `(messages, generate_fn, model_id, params, ttl)` | `Any` |
| `invalidate_model` | `(model_id)` | `int` |

---

### `StreamingResponseCache`

```python
from omnicache_ai import StreamingResponseCache
```

`__init__(manager, serializer=None, chunk_joiner=None)`

| Method | Returns |
|---|---|
| `get_or_stream(messages, stream_fn, model_id, params, ttl, tags)` | `Generator` |
| `aget_or_stream(messages, stream_fn, model_id, params, ttl, tags)` | `AsyncGenerator` |

---

### `EmbeddingCache`

```python
from omnicache_ai import EmbeddingCache
```

`__init__(manager, dim=1536)`

`get(text, model_id) -> np.ndarray | None` · `set(text, vector, model_id, ttl)` · `get_or_compute(text, compute_fn, model_id, ttl) -> np.ndarray`

---

### `RetrievalCache`

```python
from omnicache_ai import RetrievalCache
```

`__init__(manager, serializer=None)`

`get(query, retriever_id, top_k) -> list | None` · `set(query, documents, retriever_id, top_k, ttl, tags)` · `get_or_retrieve(query, retrieve_fn, retriever_id, top_k, ttl) -> list`

---

### `ContextCache`

```python
from omnicache_ai import ContextCache
```

`__init__(manager, serializer=None)`

`get(session_id, turn_index=None) -> list | None` · `set(session_id, messages, turn_index, ttl, tags)` · `invalidate_session(session_id) -> int`

---

### `SemanticCache`

```python
from omnicache_ai import SemanticCache
```

`__init__(exact_backend, vector_backend, embed_fn, threshold=0.95, key_builder=None, serializer=None)`

`get(query) -> Any | None` · `set(query, value, ttl)` · `delete(query)` · `clear()`

---

### `AdaptiveSemanticCache`

```python
from omnicache_ai import AdaptiveSemanticCache
```

Extends `SemanticCache`.

`__init__(..., target_hit_rate=0.35, adjustment_interval=100, threshold_min=0.70, threshold_max=0.99, adjustment_step=0.02, max_turn_count=10)`

`get(query, turn_count=0) -> Any | None` · `current_threshold: float` (property)

---

### `PromptCacheLayer`

```python
from omnicache_ai import PromptCacheLayer
```

`__init__(metrics=None, min_chars_to_cache=1024)`

| Method | Description |
|---|---|
| `anthropic_create(client, **kwargs)` | Sync Anthropic `messages.create` + cache_control injection |
| `anthropic_acreate(client, **kwargs)` | Async variant |
| `openai_create(client, **kwargs)` | Sync OpenAI `chat.completions.create` + savings tracking |
| `openai_acreate(client, **kwargs)` | Async variant |

---

## Middleware

### `LLMMiddleware` / `AsyncLLMMiddleware`

```python
from omnicache_ai import LLMMiddleware, AsyncLLMMiddleware
```

`__init__(response_cache, key_builder, model_id="default")` — Use as `@middleware` decorator or `middleware(fn)`.

### `EmbeddingMiddleware`

```python
from omnicache_ai import EmbeddingMiddleware
```

`__init__(embedding_cache, model_id="default")` — Wraps sync/async embed functions.

### `RetrieverMiddleware`

```python
from omnicache_ai import RetrieverMiddleware
```

`__init__(retrieval_cache, retriever_id="default", default_top_k=5)` — Wraps sync/async retrievers.

---

## Adapters

| Adapter | Import | Constructor | Key Methods |
|---|---|---|---|
| `OpenAICacheAdapter` | `omnicache_ai.adapters.openai_adapter` | `(client, manager)` | `chat_create(**kw)`, `achat_create(**kw)`, `invalidate_model(model)` |
| `AnthropicCacheAdapter` | `omnicache_ai.adapters.anthropic_adapter` | `(client, manager)` | `messages_create(**kw)`, `amessages_create(**kw)`, `invalidate_model(model)` |
| `GoogleADKCacheAdapter` | `omnicache_ai.adapters.google_adk_adapter` | `(agent, manager)` | `run(task, **kw)`, `arun(task, **kw)`, `invalidate_agent()` |
| `OpenAIAgentsCacheAdapter` | `omnicache_ai.adapters.openai_agents_adapter` | `(manager)` | `run(agent, input, **kw)`, `arun(agent, input, **kw)`, `invalidate_agent(agent)` |
| `LlamaIndexLLMCacheAdapter` | `omnicache_ai.adapters.llamaindex_adapter` | `(llm, manager)` | `complete`, `acomplete`, `chat`, `achat`, `stream_complete`, `stream_chat` |
| `LlamaIndexQueryCacheAdapter` | `omnicache_ai.adapters.llamaindex_adapter` | `(query_engine, manager)` | `query(q, **kw)`, `aquery(q, **kw)` |
| `ClaudeAgentCacheAdapter` | `omnicache_ai.adapters.claude_agent_adapter` | `(manager)` | `query(prompt, options, **kw)` (async gen), `invalidate_all()` |
| `LangChainCacheAdapter` | `omnicache_ai.adapters.langchain_adapter` | `(manager)` | `lookup`, `update`, `alookup`, `aupdate`, `clear` |
| `LangGraphCacheAdapter` | `omnicache_ai.adapters.langgraph_adapter` | `(manager)` | `get_tuple`, `put`, `put_writes`, `list`, async variants |
| `AutoGenCacheAdapter` | `omnicache_ai.adapters.autogen_adapter` | `(agent, manager)` | `generate_reply`, `run`, `arun` |
| `CrewAICacheAdapter` | `omnicache_ai.adapters.crewai_adapter` | `(crew, manager)` | `kickoff`, `kickoff_async` |
| `AgnoCacheAdapter` | `omnicache_ai.adapters.agno_adapter` | `(agent, manager)` | `run`, `arun` |
| `A2ACacheAdapter` | `omnicache_ai.adapters.a2a_adapter` | `(manager, agent_id="default")` | `process`, `aprocess`, `wrap` |
