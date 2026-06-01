---
title: "InMemoryBackend"
---

# InMemoryBackend

A thread-safe, in-process key-value cache that uses an `OrderedDict` for LRU eviction and `time.monotonic()` for per-entry TTL tracking. Zero external dependencies.

## Overview

`InMemoryBackend` is the simplest and fastest backend. It stores everything in the process's own memory, protected by a reentrant lock (`threading.RLock`) so multiple threads can read and write concurrently without corruption.

**When to use it:**

- Development and testing
- Single-process applications where speed matters most
- Short-lived caches that do not need to survive restarts
- Workloads that fit comfortably in RAM

**Tradeoffs:**

- Data is lost when the process exits.
- Not shared across processes or machines.
- Memory usage grows with cache size (bounded by `max_size`).

## Installation

No extra dependencies required. `InMemoryBackend` is included in the core package.

```bash
pip install omnicache-ai
```

## Usage

### Basic key-value caching

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend

cache = InMemoryBackend(max_size=5_000)

# Store a value with a 60-second TTL
cache.set("user:42:profile", {"name": "Alice", "role": "admin"}, ttl=60)

# Retrieve it
profile = cache.get("user:42:profile")  # {"name": "Alice", "role": "admin"}

# Check existence
cache.exists("user:42:profile")  # True

# Delete a single key
cache.delete("user:42:profile")

# Clear everything
cache.clear()
```

### Using with CacheManager

```python
from omnicache_ai import CacheManager, CacheKeyBuilder
from omnicache_ai.backends.memory_backend import InMemoryBackend

manager = CacheManager(
    backend=InMemoryBackend(max_size=10_000),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)

manager.set("prompt:hash123", b"cached response", ttl=300)
result = manager.get("prompt:hash123")
```

### LRU eviction in action

```python
cache = InMemoryBackend(max_size=3)

cache.set("a", 1)
cache.set("b", 2)
cache.set("c", 3)

# Access "a" to make it most-recently-used
cache.get("a")

# Adding a fourth entry evicts the LRU item ("b")
cache.set("d", 4)

cache.exists("a")  # True  (was accessed recently)
cache.exists("b")  # False (evicted as LRU)
cache.exists("c")  # True
cache.exists("d")  # True
```

### TTL expiration

```python
import time
from omnicache_ai.backends.memory_backend import InMemoryBackend

cache = InMemoryBackend()

cache.set("temp", "short-lived", ttl=2)
cache.get("temp")   # "short-lived"

time.sleep(3)
cache.get("temp")   # None (expired)
```

:::note[Monotonic clock]
TTL is tracked with `time.monotonic()`, which is immune to system clock
adjustments. Expiration is evaluated lazily on `get()` -- there is no
background reaper thread.
:::


:::warning[Not multi-process safe]
Each process gets its own independent cache. If you need shared state
across processes, use [DiskBackend](disk.md) or [RedisBackend](redis.md).
:::


## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_size` | `int` | `10_000` | Maximum number of entries before LRU eviction kicks in. |

### Methods

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get` | `get(key: str)` | `Any \| None` | Return the cached value, or `None` if the key is missing or expired. Moves the key to the most-recently-used position. |
| `set` | `set(key: str, value: Any, ttl: int \| None = None)` | `None` | Store a value. `ttl` is in seconds; `None` means no expiry. Evicts the LRU entry if `max_size` is exceeded. |
| `delete` | `delete(key: str)` | `None` | Remove a key. No-op if the key does not exist. |
| `exists` | `exists(key: str)` | `bool` | Return `True` if the key is present and not expired. Internally calls `get()`. |
| `clear` | `clear()` | `None` | Remove all entries from the cache. |
| `close` | `close()` | `None` | Release resources. Calls `clear()` internally. |
| `__len__` | `len(cache)` | `int` | Return the number of entries currently stored (including expired but not-yet-reaped entries). |

:::tip[Thread safety]
Every public method acquires a `threading.RLock` before touching the
internal `OrderedDict`. You can safely share a single `InMemoryBackend`
instance across threads.
:::
