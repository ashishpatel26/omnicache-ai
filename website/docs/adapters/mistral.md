---
title: "MistralCacheAdapter"
---

# MistralCacheAdapter

Wraps `mistralai.Mistral` `chat.complete` calls with response caching. Returns cached results for identical `(model, messages, params)` combinations.

## Installation

```bash
pip install 'omnicache-ai[mistral]'
```

---

## Usage

### Sync

```python
from mistralai import Mistral
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

client = Mistral(api_key="your-api-key")
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = MistralCacheAdapter(client, manager)

response = adapter.chat_complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)

# Second call — cache hit, no API cost
response = adapter.chat_complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
```

### Async

```python
response = await adapter.achat_complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Summarise this report."}],
)
```

### With persistent cache

```python
from omnicache_ai.backends.disk_backend import DiskBackend

manager = CacheManager(
    backend=DiskBackend("/var/cache/mistral"),
    key_builder=CacheKeyBuilder(namespace="mistral"),
)
adapter = MistralCacheAdapter(client, manager)
```

### Invalidate by model

```python
from omnicache_ai.core.invalidation import InvalidationEngine

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)
adapter = MistralCacheAdapter(client, manager)
adapter.invalidate_model("mistral-large-latest")
```

:::note[Stream excluded from key]
The `stream` parameter is excluded from cache key computation. Streaming and non-streaming requests for the same prompt share the same cache entry.
:::

---

## API Reference

| Method | Description |
|---|---|
| `chat_complete(**kwargs)` | Cached `client.chat.complete()` (sync) |
| `achat_complete(**kwargs)` | Cached `client.chat.complete_async()` (async) |
| `invalidate_model(model)` | Invalidate all cached responses for a model |
