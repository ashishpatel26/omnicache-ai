---
title: "StampedeShield"
---

# StampedeShield

Per-key `threading.Lock` that prevents cache stampede — the scenario where multiple concurrent threads simultaneously miss the same cache key and all call the LLM, paying N × cost for one result.

## The Problem

```
Thread A: get("key") → None (miss)         ─┐
Thread B: get("key") → None (miss)           ├─ all call LLM simultaneously → 3x cost
Thread C: get("key") → None (miss)         ─┘
```

## The Solution

```
Thread A: acquires lock for "key" → calls LLM → stores result → releases lock
Thread B: waits for lock → gets result from cache → returns immediately
Thread C: waits for lock → gets result from cache → returns immediately
```

---

## Built-In Protection

`StampedeShield` is **wired into `ResponseCache.get_or_generate()` automatically** — you don't need to use it directly.

```python
from omnicache_ai import ResponseCache, CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cache = ResponseCache(manager)  # StampedeShield active by default

# Safe under concurrent access — only one thread calls generate_fn per key
result = cache.get_or_generate(
    messages=[{"role": "user", "content": "What is RAG?"}],
    generate_fn=my_llm_fn,
    model_id="gpt-4o",
)
```

---

## Direct Usage

For custom cache logic outside `ResponseCache`:

```python
from omnicache_ai import StampedeShield

shield = StampedeShield(timeout=30.0)

with shield.lock("omnicache:resp:abc123"):
    cached = manager.get(key)
    if cached is None:
        result = expensive_llm_call()
        manager.set(key, result)
    else:
        result = cached
```

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timeout` | `float` | `30.0` | Seconds to wait for lock before raising `TimeoutError` |

`shield.lock(key)` is a `contextmanager` that yields `True` (first acquirer) and releases on exit.
