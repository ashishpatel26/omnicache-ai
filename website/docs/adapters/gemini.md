---
title: "GeminiCacheAdapter"
---

# GeminiCacheAdapter

Wraps `google.generativeai.GenerativeModel` `generate_content` calls with response caching. Returns cached results for identical `(model, contents, params)` combinations.

## Installation

```bash
pip install 'omnicache-ai[gemini]'
```

---

## Usage

### Sync

```python
import google.generativeai as genai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel("gemini-2.0-flash")

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = GeminiCacheAdapter(model, manager)

response = adapter.generate_content("What is the capital of France?")

# Second call — cache hit, no API cost
response = adapter.generate_content("What is the capital of France?")
```

### Async

```python
response = await adapter.agenerate_content("Summarise the quarterly report.")
```

### Multi-turn content

```python
contents = [
    {"role": "user", "parts": ["Hello"]},
    {"role": "model", "parts": ["Hi! How can I help?"]},
    {"role": "user", "parts": ["What is 2+2?"]},
]
response = adapter.generate_content(contents)
```

### With Redis shared cache

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="gemini"),
)
adapter = GeminiCacheAdapter(model, manager)
```

### Invalidate model entries

```python
from omnicache_ai.core.invalidation import InvalidationEngine

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)
adapter = GeminiCacheAdapter(model, manager)
adapter.invalidate_model()
```

:::note[Transparent proxy]
Any attribute not overridden (e.g. `model.model_name`, `model.tools`) is forwarded to the underlying `GenerativeModel` via `__getattr__`.
:::

---

## API Reference

| Method | Description |
|---|---|
| `generate_content(contents, **kwargs)` | Cached `model.generate_content()` (sync) |
| `agenerate_content(contents, **kwargs)` | Cached `model.generate_content_async()` (async) |
| `invalidate_model()` | Invalidate all cached responses for this model |
