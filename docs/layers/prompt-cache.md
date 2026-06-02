# PromptCacheLayer

Inject provider-level cache markers and track token savings from Anthropic and OpenAI prompt caching.

---

## Overview

`PromptCacheLayer` does two things:

1. **Injection** — for Anthropic, wraps long system prompts with `cache_control: {"type": "ephemeral"}` so the provider caches the prefix server-side (90% cost discount on cached tokens).

2. **Tracking** — reads the `cache_read_input_tokens` / `cached_tokens` field from API responses and updates `CacheMetrics` with estimated tokens saved and USD saved.

This layer works *alongside* `ResponseCache` or `AnthropicCacheAdapter` — they cache full responses; `PromptCacheLayer` reduces token cost when a response *is not* cached but the system prompt is long and repeated.

**When to use:**

- Long, repeated system prompts (instructions, document context) with Anthropic or OpenAI
- You want to track provider-level cache savings in Prometheus/OTEL metrics
- Combined with response caching for maximum cost reduction

!!! note "Anthropic vs OpenAI behaviour"
    Anthropic: cache_control injection is explicit — only prompts ≥ `min_chars_to_cache` characters get marked.
    OpenAI: caching is automatic for prompts ≥ 1024 tokens — this layer only *tracks* savings, does not inject markers.

---

## Usage

### Anthropic with injection + tracking

```python
import anthropic
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder, CacheMetrics
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

client = anthropic.Anthropic()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
layer = PromptCacheLayer(metrics=manager.metrics, min_chars_to_cache=1024)

response = layer.anthropic_create(
    client,
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are an expert Python engineer with 20 years experience. " + long_context,
    messages=[{"role": "user", "content": "Fix the auth bug."}],
)

print(f"Provider cache hits: {manager.metrics.provider_cache_hits}")
print(f"Tokens saved: {manager.metrics.estimated_tokens_saved}")
print(f"USD saved: ${manager.metrics.estimated_cost_saved_usd:.4f}")
```

### Async Anthropic

```python
response = await layer.anthropic_acreate(
    client,
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=long_system_prompt,
    messages=[{"role": "user", "content": "Explain the code."}],
)
```

### OpenAI savings tracking

```python
import openai

openai_client = openai.OpenAI()
layer = PromptCacheLayer(metrics=manager.metrics)

response = layer.openai_create(
    openai_client,
    model="gpt-4o",
    messages=[
        {"role": "system", "content": very_long_system_prompt},
        {"role": "user", "content": "Answer this question."},
    ],
)
```

### Combined with ResponseCache

```python
from omnicache_ai.layers.response_cache import ResponseCache

response_cache = ResponseCache(manager)
prompt_layer = PromptCacheLayer(metrics=manager.metrics)

messages = [{"role": "user", "content": "What is RAG?"}]

# Check response cache first
cached = response_cache.get("claude-sonnet-4-6", messages)
if cached is None:
    # Cache miss — use prompt layer (gets provider-level discount + tracks savings)
    raw = prompt_layer.anthropic_create(client, model="claude-sonnet-4-6", max_tokens=512, messages=messages)
    response_cache.set("claude-sonnet-4-6", messages, raw)
    cached = raw
```

---

## How It Works

1. `anthropic_create` calls `_inject_anthropic_cache(system)`:
   - If `system` is a string and `len(system) >= min_chars_to_cache` → wraps in `[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]`
2. Calls `client.messages.create(**kwargs)` with the modified system
3. Reads `response.usage.cache_read_input_tokens` from the response
4. If > 0: increments `metrics.provider_cache_hits`, adds to `estimated_tokens_saved`, computes `estimated_cost_saved_usd` using per-model pricing

```
anthropic_create(client, system="long prompt...", ...)
        |
  len(system) >= min_chars?
  /                        \
yes                         no
 |                           |
wrap with cache_control    pass through unchanged
        |
  client.messages.create(...)
        |
  response.usage.cache_read_input_tokens > 0?
  /                                          \
yes                                           no
 |
metrics.provider_cache_hits += 1
metrics.estimated_tokens_saved += cache_read
metrics.estimated_cost_saved_usd += ...
```

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `metrics` | `CacheMetrics \| None` | `None` | Metrics instance for savings tracking |
| `min_chars_to_cache` | `int` | `1024` | Min system prompt length to inject cache_control |

### Methods

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `anthropic_create` | `(client, **kwargs)` | `Message` | Sync Anthropic with injection + tracking |
| `anthropic_acreate` | `(client, **kwargs)` | `Message` | Async variant |
| `openai_create` | `(client, **kwargs)` | `ChatCompletion` | Sync OpenAI with savings tracking |
| `openai_acreate` | `(client, **kwargs)` | `ChatCompletion` | Async variant |

---

## Source

:material-file-code: `omnicache_ai/layers/prompt_cache.py`
