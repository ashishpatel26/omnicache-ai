---
title: "CacheMetrics"
---

# CacheMetrics

Thread-safe counters for cache operations. Every `CacheManager` exposes a `metrics` property — no configuration required.

## Fields

| Field | Type | Description |
|---|---|---|
| `hits` | `int` | Exact or semantic cache hits served without a model call |
| `misses` | `int` | Cache misses requiring a downstream API call |
| `evictions` | `int` | LRU evictions from `InMemoryBackend` |
| `sets` | `int` | Total cache writes |
| `hit_rate` | `float` | `hits / (hits + misses)` — 0.0 to 1.0 |
| `miss_rate` | `float` | `1.0 - hit_rate` |
| `provider_cache_hits` | `int` | Server-side prompt cache hits (Anthropic/OpenAI) tracked by `PromptCacheLayer` |
| `estimated_tokens_saved` | `int` | Tokens saved via provider prompt caching |
| `estimated_cost_saved_usd` | `float` | Estimated USD saved via provider caching |

---

## Usage

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
)

# Use the cache...
manager.set("key", b"value")
manager.get("key")   # hit
manager.get("other") # miss

snap = manager.metrics.snapshot()
print(snap)
# {
#   'hits': 1, 'misses': 1, 'evictions': 0, 'sets': 1,
#   'hit_rate': 0.5, 'miss_rate': 0.5,
#   'provider_cache_hits': 0,
#   'estimated_tokens_saved': 0,
#   'estimated_cost_saved_usd': 0.0
# }
```

### Live access

```python
print(manager.metrics.hits)
print(manager.metrics.hit_rate)
```

### Reset counters

```python
manager.metrics.reset()
```

---

## Thread Safety

All counter increments use a `threading.Lock`. Safe for use with `LLMMiddleware`, `AsyncLLMMiddleware`, and concurrent requests.

---

## Exporting Metrics

See [Observability](observability.md) for Prometheus and OpenTelemetry export.

---

## Provider Cache Savings

When using `PromptCacheLayer`, provider-level savings are tracked automatically:

```python
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

layer = PromptCacheLayer(metrics=manager.metrics)
response = layer.anthropic_create(client, model="claude-sonnet-4-6",
                                   system=LONG_SYSTEM, messages=messages, max_tokens=1024)

snap = manager.metrics.snapshot()
print(f"Provider cache hits: {snap['provider_cache_hits']}")
print(f"Tokens saved:        {snap['estimated_tokens_saved']:,}")
print(f"Cost saved:          ${snap['estimated_cost_saved_usd']:.4f}")
```
