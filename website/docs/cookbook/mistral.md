---
title: "Mistral AI"
---

# Mistral AI + OmniCache-AI

Cache `client.chat.complete` calls — identical requests return instantly without hitting the API.

## Install

```bash
pip install 'omnicache-ai[mistral]'
```

## Example

```python
import time
from mistralai import Mistral
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

client = Mistral(api_key="your-api-key")
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = MistralCacheAdapter(client, manager)

messages = [{"role": "user", "content": "What is semantic caching?"}]

t0 = time.perf_counter()
r1 = adapter.chat_complete(model="mistral-small-latest", messages=messages)
t1 = time.perf_counter()
print(r1.choices[0].message.content)
print(f"First call:  {t1 - t0:.3f}s")  # live API call

t0 = time.perf_counter()
r2 = adapter.chat_complete(model="mistral-small-latest", messages=messages)
t1 = time.perf_counter()
print(f"Second call: {t1 - t0:.6f}s")  # <1ms cache hit
```

## Async Example

```python
import asyncio
from mistralai import Mistral
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

client = Mistral(api_key="your-api-key")
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
adapter = MistralCacheAdapter(client, manager)

async def main():
    messages = [{"role": "user", "content": "What is 2+2?"}]
    r1 = await adapter.achat_complete(model="mistral-large-latest", messages=messages)
    r2 = await adapter.achat_complete(model="mistral-large-latest", messages=messages)
    assert r1.choices[0].message.content == r2.choices[0].message.content

asyncio.run(main())
```

## With Redis (shared across workers)

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="mistral"),
)
adapter = MistralCacheAdapter(client, manager)
```
