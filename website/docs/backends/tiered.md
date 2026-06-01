---
title: "TieredBackend"
---

# TieredBackend

Two-level cache: fast L1 (memory) with persistent L2 fallback (Redis, disk). On a miss in L1 but hit in L2, the value is promoted to L1 so subsequent reads stay fast.

## Overview

```
Read:   L1 → (hit) return | (miss) → L2 → (hit) promote to L1, return | (miss) → None
Write:  L1 + L2 simultaneously
Delete: L1 + L2 simultaneously
```

Typical setup: `L1 = InMemoryBackend`, `L2 = RedisBackend` or `DiskBackend`.

---

## Usage

### Memory + Redis

```python
from omnicache_ai import InMemoryBackend, CacheManager, CacheKeyBuilder, TieredBackend
from omnicache_ai.backends.redis_backend import RedisBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=1_000),
    l2=RedisBackend(url="redis://localhost:6379/0"),
    l1_ttl=300,  # 5-min local copy — shorter than L2 TTL
)

manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())
```

### Memory + Disk

```python
from omnicache_ai import DiskBackend, TieredBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=500),
    l2=DiskBackend(directory="/var/cache/omnicache"),
    l1_ttl=60,
)
```

---

## Why Use TieredBackend?

| Scenario | Without Tiered | With Tiered |
|---|---|---|
| First read after process restart | Redis: ~2ms | Redis: ~2ms (L2 hit, promotes to L1) |
| Repeated read in same process | Redis: ~2ms every time | Memory: ~10µs (L1 hit) |
| Multi-node consistency | ✅ (Redis) | ✅ (L2 = Redis is authoritative) |
| Single-node speed | ❌ | ✅ (L1 is in-process) |

---

## L1 TTL Strategy

Set `l1_ttl` **shorter** than your L2 TTL so hot entries stay warm in memory without becoming stale:

```
L2 TTL = 3600s (1 hour in Redis)
l1_ttl = 300s  (5 minutes in memory)
→ Memory stays fresh; Redis is the source of truth on L1 expiry
```

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `l1` | `CacheBackend` | *(required)* | Fast primary backend (typically InMemoryBackend) |
| `l2` | `CacheBackend` | *(required)* | Persistent fallback (Redis, disk) |
| `l1_ttl` | `int \| None` | `300` | TTL in seconds for L2→L1 promoted values |
