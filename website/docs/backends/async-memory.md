---
title: "AsyncInMemoryBackend"
---

# AsyncInMemoryBackend

Async-native in-memory backend using `asyncio.Lock`. Use this in async frameworks (FastAPI, async LangGraph, async LLM middleware) to avoid blocking the event loop.

## When to Use

| Framework | Backend to use |
|---|---|
| FastAPI / Starlette | `AsyncInMemoryBackend` |
| Async LangGraph | `AsyncInMemoryBackend` |
| Standard Python scripts | `InMemoryBackend` (sync, faster) |
| Shared across processes | `RedisBackend` (async via `redis.asyncio`) |

---

## Usage

```python
from omnicache_ai import AsyncInMemoryBackend

backend = AsyncInMemoryBackend(max_size=10_000)

await backend.set("key", b"value", ttl=60)
value = await backend.get("key")   # b"value"
await backend.delete("key")
exists = await backend.exists("key")  # False
await backend.clear()
await backend.close()
```

### In an async context

```python
import asyncio
from omnicache_ai import AsyncInMemoryBackend

async def main():
    backend = AsyncInMemoryBackend()
    await backend.set("result", b"cached-response", ttl=300)
    data = await backend.get("result")
    print(data)

asyncio.run(main())
```

---

## Internals

`AsyncInMemoryBackend` wraps `InMemoryBackend` (LRU + per-entry TTL) behind an `asyncio.Lock`. All reads and writes acquire the lock before delegating to the synchronous implementation. This ensures correctness in concurrent async code without spawning threads.

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_size` | `int` | `10_000` | Max entries before LRU eviction |

Implements `AsyncCacheBackend` protocol — all methods are `async`.
