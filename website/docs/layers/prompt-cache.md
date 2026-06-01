---
title: "PromptCacheLayer"
---

# PromptCacheLayer

Surfaces provider-level prompt caching (Anthropic `cache_control`, OpenAI automatic prefix caching) and tracks cost savings in `CacheMetrics`.

## Overview

LLM providers offer server-side caching of repeated prompt prefixes:

- **Anthropic**: explicit `cache_control` markers — 90% discount on cached input tokens
- **OpenAI**: automatic for prompts ≥ 1024 tokens — 50% discount on cached tokens

`PromptCacheLayer` handles both:
- **Anthropic**: automatically injects `cache_control: {"type": "ephemeral"}` on system prompts longer than `min_chars_to_cache` (default: 1024 chars)
- **OpenAI**: no injection needed; just tracks the savings from the `usage.prompt_tokens_details.cached_tokens` field in the response

Savings are recorded to `CacheMetrics` as `provider_cache_hits`, `estimated_tokens_saved`, and `estimated_cost_saved_usd`.

---

## Usage

### Anthropic

```python
import anthropic
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

client = anthropic.Anthropic()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
layer = PromptCacheLayer(metrics=manager.metrics, min_chars_to_cache=512)

SYSTEM = """
You are an expert Python engineer with deep knowledge of async programming,
type systems, and distributed systems. You provide concise, correct code
with minimal explanation unless asked.
""" * 10  # long system prompt — will be cached

response = layer.anthropic_create(
    client,
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=SYSTEM,
    messages=[{"role": "user", "content": "Fix the deadlock in worker.py"}],
)

# Check savings
snap = manager.metrics.snapshot()
print(f"Provider cache hits: {snap['provider_cache_hits']}")
print(f"Tokens saved: {snap['estimated_tokens_saved']}")
print(f"Cost saved: ${snap['estimated_cost_saved_usd']:.4f}")
```

### Anthropic Async

```python
response = await layer.anthropic_acreate(
    client,
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=SYSTEM,
    messages=[{"role": "user", "content": "Explain the retry logic"}],
)
```

### OpenAI (savings tracking only — injection is automatic)

```python
import openai

client = openai.OpenAI()
layer = PromptCacheLayer(metrics=manager.metrics)

response = layer.openai_create(
    client,
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "What does the cache module do?"},
    ],
)
```

---

## Combining with ResponseCache

Use both layers together: `PromptCacheLayer` saves tokens within live API calls; `ResponseCache` eliminates entire API calls for known inputs.

```python
from omnicache_ai import ResponseCache

response_cache = ResponseCache(manager)
prompt_layer = PromptCacheLayer(metrics=manager.metrics)

# 1. Check response cache first
cached = response_cache.get(messages, model_id="claude-sonnet-4-6")
if cached:
    return cached

# 2. Miss — call API with prompt caching enabled
response = prompt_layer.anthropic_create(client, model="claude-sonnet-4-6",
                                          system=SYSTEM, messages=messages, max_tokens=1024)

# 3. Store in response cache for next time
response_cache.set(messages, response, model_id="claude-sonnet-4-6")
```

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `metrics` | `CacheMetrics \| None` | `None` | Metrics instance to record savings |
| `min_chars_to_cache` | `int` | `1024` | System prompt character threshold for `cache_control` injection |

| Method | Description |
|---|---|
| `anthropic_create(client, **kwargs)` | Sync Anthropic `messages.create` with injection |
| `anthropic_acreate(client, **kwargs)` | Async Anthropic `messages.create` with injection |
| `openai_create(client, **kwargs)` | Sync OpenAI `chat.completions.create` with savings tracking |
| `openai_acreate(client, **kwargs)` | Async OpenAI `chat.completions.create` with savings tracking |
