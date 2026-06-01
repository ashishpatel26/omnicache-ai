---
title: "OpenAICacheAdapter"
---

# OpenAICacheAdapter

Wraps `openai.OpenAI` and `openai.AsyncOpenAI` `chat.completions.create` calls with response caching. Returns cached results for identical `(model, messages, params)` combinations without hitting the API.

## Installation

```bash
pip install 'omnicache-ai[openai]'
```

---

## Usage

### Sync

```python
import openai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

client = openai.OpenAI()
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = OpenAICacheAdapter(client, manager)

# First call — hits the API
response = adapter.chat_create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is semantic caching?"}],
)

# Second call with same args — returns from cache instantly
response = adapter.chat_create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is semantic caching?"}],
)
```

### Async

```python
client = openai.AsyncOpenAI()
adapter = OpenAICacheAdapter(client, manager)

response = await adapter.achat_create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is semantic caching?"}],
)
```

### With Redis backend

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="prod"),
)
adapter = OpenAICacheAdapter(client, manager)
```

### Invalidate by model

```python
adapter.invalidate_model("gpt-4o")  # remove all cached gpt-4o responses
```

---

## How It Works

Cache key = `hash(model + messages + non-stream params)`. The full `ChatCompletion` response object is serialised and replayed on hit. The `stream` parameter is excluded from the key so streaming vs non-streaming calls share the same cache entry.

---

## API Reference

| Method | Description |
|---|---|
| `chat_create(**kwargs)` | Cached `client.chat.completions.create()` (sync) |
| `achat_create(**kwargs)` | Cached `client.chat.completions.create()` (async) |
| `invalidate_model(model)` | Invalidate all cached responses for a model |
