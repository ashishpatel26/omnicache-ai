---
title: "Anthropic SDK"
---

# Anthropic SDK + OmniCache-AI

Cache `client.messages.create` calls — identical requests return instantly without hitting the API.

## Install

```bash
pip install 'omnicache-ai[anthropic]'
```

## Example

```python
import anthropic, time
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

client = anthropic.Anthropic()
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = AnthropicCacheAdapter(client, manager)

messages = [{"role": "user", "content": "Explain semantic caching in 3 sentences"}]

t0 = time.perf_counter()
r1 = adapter.messages_create(
    model="claude-haiku-4-5",
    max_tokens=256,
    messages=messages,
)
t1 = time.perf_counter()
print(r1.content[0].text)
print(f"First:  {t1-t0:.3f}s")  # ~0.6s live API call

t2 = time.perf_counter()
r2 = adapter.messages_create(model="claude-haiku-4-5", max_tokens=256, messages=messages)
t3 = time.perf_counter()
print(f"Second: {t3-t2:.4f}s (cache hit)")

snap = manager.metrics.snapshot()
print(f"Hit rate: {snap['hit_rate']:.0%}")
```

## Async

```python
client = anthropic.AsyncAnthropic()
adapter = AnthropicCacheAdapter(client, manager)

response = await adapter.amessages_create(
    model="claude-haiku-4-5",
    max_tokens=256,
    messages=[{"role": "user", "content": "What is RAG?"}],
)
```

## With system prompt

```python
response = adapter.messages_create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system="You are a concise technical writer.",
    messages=[{"role": "user", "content": "Design a thread-safe cache"}],
)
```

## Combine with PromptCacheLayer for two-level savings

```python
from omnicache_ai import ResponseCache
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

LONG_SYSTEM = "You are an expert Python architect... " * 20  # > 1024 chars

response_cache = ResponseCache(manager)
prompt_layer = PromptCacheLayer(metrics=manager.metrics, min_chars_to_cache=512)

messages = [{"role": "user", "content": "Design a thread-safe cache"}]

# Check response cache first (zero cost on hit)
cached = response_cache.get(messages, model_id="claude-sonnet-4-6")
if not cached:
    # Live call — PromptCacheLayer injects cache_control on the system prompt
    response = prompt_layer.anthropic_create(
        client._client,  # raw anthropic.Anthropic instance
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=LONG_SYSTEM,
        messages=messages,
    )
    response_cache.set(messages, response, model_id="claude-sonnet-4-6", ttl=3600)

snap = manager.metrics.snapshot()
print(f"Provider cache hits: {snap['provider_cache_hits']}")
print(f"Cost saved: ${snap['estimated_cost_saved_usd']:.4f}")
```

## Invalidate by model

```python
adapter.invalidate_model("claude-haiku-4-5")
```
