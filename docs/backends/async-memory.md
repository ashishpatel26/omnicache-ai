# AsyncInMemoryBackend

Async-native in-memory LRU cache using `asyncio.Lock` — no thread blocking in async frameworks.

## Overview

`AsyncInMemoryBackend` wraps [`InMemoryBackend`](memory.md) with an `asyncio.Lock`, making all operations safe for use in async frameworks like FastAPI, async LangGraph, and any `asyncio`-based pipeline. All operations are coroutines — `await backend.get(key)`.

**When to use:**

- Your application runs in an async event loop (FastAPI, aiohttp, async LangGraph)
- You want in-memory caching without blocking the event loop
- You need the same LRU behaviour as `InMemoryBackend` but with `async/await` syntax

---

## Installation

No extra dependencies — included in the core package.

```bash
pip install omnicache-ai
```

---

## Usage

### Direct usage

```python
from omnicache_ai.backends.async_memory_backend import AsyncInMemoryBackend

backend = AsyncInMemoryBackend(max_size=10_000)

await backend.set("key", b"value", ttl=300)
value = await backend.get("key")         # b"value"
exists = await backend.exists("key")     # True
await backend.delete("key")
await backend.clear()
await backend.close()
```

### With FastAPI

```python
from fastapi import FastAPI
from omnicache_ai import CacheManager, CacheKeyBuilder
from omnicache_ai.backends.async_memory_backend import AsyncInMemoryBackend
from omnicache_ai.layers.response_cache import ResponseCache

app = FastAPI()
backend = AsyncInMemoryBackend(max_size=5_000)
manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())
cache = ResponseCache(manager)

@app.get("/answer")
async def answer(question: str):
    cached = cache.get("gpt-4o", [{"role": "user", "content": question}])
    if cached:
        return cached
    result = await call_openai(question)
    cache.set("gpt-4o", [{"role": "user", "content": question}], result)
    return result
```

!!! note "LRU eviction"
    When `max_size` is reached, the least recently used entry is evicted automatically — same behaviour as `InMemoryBackend`.

!!! warning "Not shared across processes"
    Like `InMemoryBackend`, this backend is in-process only. Use `RedisBackend` for shared async caching across multiple workers.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_size` | `int` | `10_000` | Maximum entries before LRU eviction |

### Methods

All methods are coroutines (use `await`):

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get` | `(key: str)` | `Any \| None` | Retrieve value |
| `set` | `(key: str, value: Any, ttl: int \| None)` | `None` | Store value |
| `delete` | `(key: str)` | `None` | Remove value |
| `exists` | `(key: str)` | `bool` | Check if key exists |
| `clear` | `()` | `None` | Flush all entries |
| `close` | `()` | `None` | Release resources |

---

## Source

:material-file-code: `omnicache_ai/backends/async_memory_backend.py`
