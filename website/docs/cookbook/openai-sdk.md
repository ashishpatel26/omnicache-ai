---
title: "OpenAI SDK"
---

# OpenAI SDK + OmniCache-AI

Cache `client.chat.completions.create` calls — identical requests return instantly without hitting the API.

## Install

```bash
pip install 'omnicache-ai[openai]'
```

## Example

```python
import openai, time
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

client = openai.OpenAI()
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = OpenAICacheAdapter(client, manager)

messages = [{"role": "user", "content": "What are the top 3 benefits of caching LLM responses?"}]

t0 = time.perf_counter()
r1 = adapter.chat_create(model="gpt-4o-mini", messages=messages)
t1 = time.perf_counter()
print(r1.choices[0].message.content)
print(f"First:  {t1-t0:.3f}s")  # ~0.8s live API call

t2 = time.perf_counter()
r2 = adapter.chat_create(model="gpt-4o-mini", messages=messages)
t3 = time.perf_counter()
print(f"Second: {t3-t2:.4f}s (cache hit)")  # ~0.0001s

snap = manager.metrics.snapshot()
print(f"Hit rate: {snap['hit_rate']:.0%}")
```

## Async

```python
client = openai.AsyncOpenAI()
adapter = OpenAICacheAdapter(client, manager)

response = await adapter.achat_create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain vector embeddings"}],
)
```

## With Redis (shared across workers)

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="prod"),
)
adapter = OpenAICacheAdapter(client, manager)
```

## Invalidate by model

```python
# Clear all cached gpt-4o-mini responses
adapter.invalidate_model("gpt-4o-mini")
```

## With GzipCompressor (reduce Redis memory)

```python
from omnicache_ai import GzipCompressor

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="prod"),
    compressor=GzipCompressor(level=6),
)
adapter = OpenAICacheAdapter(client, manager)
```
