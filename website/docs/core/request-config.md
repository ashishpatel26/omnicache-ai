---
title: "RequestConfig"
---

# RequestConfig

Per-request override dataclass for TTL, semantic threshold, cache bypass, and tags. Use when different requests in the same application need different cache behaviour.

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `ttl` | `int \| None` | `None` | Override TTL in seconds for this request. `None` = use `TTLPolicy` default |
| `semantic_threshold` | `float \| None` | `None` | Override cosine similarity threshold. `None` = use global threshold |
| `skip_cache` | `bool` | `False` | Bypass cache entirely — no read, no write |
| `tags` | `list[str]` | `[]` | Additional invalidation tags for this cache entry |
| `namespace_prefix` | `str \| None` | `None` | Extra key prefix for per-request tenant isolation |

---

## Usage

```python
from omnicache_ai.core.request_config import RequestConfig
```

### Short TTL for volatile data

```python
cfg = RequestConfig(ttl=30)  # cache for only 30 seconds

# Apply manually in your cache logic:
if not cfg.skip_cache:
    cached = cache.get(messages, model_id="gpt-4o")
if cached is None:
    result = llm_fn(messages)
    cache.set(messages, result, model_id="gpt-4o", ttl=cfg.ttl)
```

### Skip cache for debugging or forced refresh

```python
cfg = RequestConfig(skip_cache=True)

if cfg.skip_cache:
    result = llm_fn(messages)  # always live
else:
    result = cache.get_or_generate(messages, llm_fn)
```

### Lower semantic threshold for broader matching

```python
cfg = RequestConfig(semantic_threshold=0.80)

# Use with AdaptiveSemanticCache or SemanticCache manually:
if not cfg.skip_cache:
    result = sem_cache.get(query)  # uses cache's default threshold
    # For per-request threshold, pass to vector backend directly
```

### Add extra invalidation tags

```python
cfg = RequestConfig(tags=["session:abc123", "user:42"])
cache.set(messages, result, model_id="gpt-4o", tags=cfg.tags)

# Later invalidate by session:
manager.invalidate("session:abc123")
```

---

## Design Note

`RequestConfig` is a plain dataclass — it carries intent, not logic. Apply it in your own cache orchestration layer or pass it through middleware. Future versions of `CacheManager.get()` and `ResponseCache.get_or_generate()` will accept `RequestConfig` directly.
