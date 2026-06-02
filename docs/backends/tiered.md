# TieredBackend

Two-level (L1 + L2) cache: memory speed for hot entries, persistent storage for cold ones.

## Overview

`TieredBackend` chains two backends: a fast L1 (typically in-memory) and a slower L2 (Redis or disk). On a cache miss in L1 but hit in L2, the value is promoted to L1 for future fast access.

**When to use:**

- You need memory-speed cache hits but also persistence across process restarts
- You're running multiple processes that share a Redis L2 but want per-process memory caching
- You want automatic hot/cold tiering without application logic changes

---

## Installation

No extra dependencies — `TieredBackend` uses only the backends you configure.

```bash
pip install omnicache-ai            # L1=memory + L2=disk (no extras)
pip install 'omnicache-ai[redis]'   # L1=memory + L2=Redis
```

---

## Usage

### Memory + Redis (recommended for multi-process)

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.backends.redis_backend import RedisBackend
from omnicache_ai.backends.tiered_backend import TieredBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=1_000),
    l2=RedisBackend(url="redis://localhost:6379/0"),
    l1_ttl=300,  # 5-minute local copy
)
manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())
```

### Memory + Disk (single-process persistence)

```python
from omnicache_ai.backends.disk_backend import DiskBackend
from omnicache_ai.backends.tiered_backend import TieredBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=500),
    l2=DiskBackend("/var/cache/omnicache"),
    l1_ttl=600,
)
```

### Using with CacheManager

```python
manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())

manager.set("my_key", {"result": "Paris"})
value = manager.get("my_key")   # L1 hit — microsecond latency
```

!!! tip "L1 TTL"
    Set `l1_ttl` shorter than your L2 TTL. This ensures the in-memory copy expires before the persistent copy — you'll re-read from L2 and re-promote rather than serving stale data forever.

!!! note "L1 + L2 write policy"
    Every `set` writes to **both** L1 and L2. Reads only fetch from L2 on L1 miss, then promote to L1.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `l1` | `CacheBackend` | *(required)* | Fast primary backend (typically in-memory) |
| `l2` | `CacheBackend` | *(required)* | Slower persistent backend |
| `l1_ttl` | `int \| None` | `300` | TTL for L1 promotion copies (seconds) |

### Methods

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get` | `(key: str)` | `Any \| None` | L1 first; on miss fetches L2 and promotes |
| `set` | `(key: str, value: Any, ttl: int \| None)` | `None` | Writes to both L1 and L2 |
| `delete` | `(key: str)` | `None` | Removes from both L1 and L2 |
| `exists` | `(key: str)` | `bool` | True if key exists in L1 or L2 |
| `clear` | `()` | `None` | Flushes both backends |
| `close` | `()` | `None` | Closes both backends |

---

## Source

:material-file-code: `omnicache_ai/backends/tiered_backend.py`
