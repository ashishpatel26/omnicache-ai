---
title: "Provider Prompt Caching"
---

# Provider Prompt Caching + OmniCache-AI

Track Anthropic and OpenAI server-side prompt cache savings alongside your application-level cache hits.

## Install

```bash
pip install anthropic
```

## Example — Anthropic with cache_control injection

```python
import anthropic
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

client = anthropic.Anthropic()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
layer = PromptCacheLayer(metrics=manager.metrics, min_chars_to_cache=512)

# Long system prompt — auto-cached by Anthropic after first call
SYSTEM = "You are an expert Python architect... " * 20

response = layer.anthropic_create(
    client,
    model="claude-haiku-4-5",
    max_tokens=256,
    system=SYSTEM,
    messages=[{"role": "user", "content": "Design a thread-safe LRU cache"}],
)

snap = manager.metrics.snapshot()
print(f"Provider cache hits:  {snap['provider_cache_hits']}")
print(f"Tokens saved:         {snap['estimated_tokens_saved']:,}")
print(f"Cost saved:           ${snap['estimated_cost_saved_usd']:.4f}")
```

## Two-level savings: response cache + prompt cache

```python
from omnicache_ai import ResponseCache

response_cache = ResponseCache(manager)
prompt_layer = PromptCacheLayer(metrics=manager.metrics)

messages = [{"role": "user", "content": "Design a thread-safe LRU cache"}]

# Check response cache first (eliminates entire API call on hit)
cached = response_cache.get(messages, model_id="claude-haiku-4-5")
if cached:
    return cached  # zero cost

# Miss — call API with prompt caching (saves tokens on live call)
response = prompt_layer.anthropic_create(client, model="claude-haiku-4-5",
                                          system=SYSTEM, messages=messages, max_tokens=256)
response_cache.set(messages, response, model_id="claude-haiku-4-5", ttl=3600)
```

## Run the cookbook example

```bash
export ANTHROPIC_API_KEY=your_key
uv run python -m cookbook.prompt_cache.agent
```
