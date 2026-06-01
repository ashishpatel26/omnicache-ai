---
title: "Tiered Backend"
---

# Tiered Backend + OmniCache-AI

Combine in-memory speed with Redis persistence using `TieredBackend`.

## Example

```python
import time, tempfile
from omnicache_ai import (
    CacheManager, CacheKeyBuilder, InMemoryBackend,
    DiskBackend, ResponseCache, TieredBackend,
)

with tempfile.TemporaryDirectory() as tmpdir:
    backend = TieredBackend(
        l1=InMemoryBackend(max_size=100),
        l2=DiskBackend(directory=tmpdir),
        l1_ttl=300,
    )
    manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())
    cache = ResponseCache(manager)
    messages = [{"role": "user", "content": "What is semantic caching?"}]

    def llm(messages):
        time.sleep(0.05)  # simulate 50ms API call
        return {"answer": "Semantic caching matches by meaning, not exact text."}

    # Miss → stored in L1 + L2
    r1 = cache.get_or_generate(messages, llm, model_id="sim")
    print("L1+L2 write:", r1)

    # L1 hit (in-memory, microseconds)
    r2 = cache.get_or_generate(messages, llm, model_id="sim")

    # Simulate process restart — clear L1 only
    backend._l1.clear()

    # L2 hit → promoted back to L1
    r3 = cache.get_or_generate(messages, llm, model_id="sim")
    print("L2→L1 promotion:", r3)
```

## With Redis L2

```python
from omnicache_ai.backends.redis_backend import RedisBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=1_000),
    l2=RedisBackend(url="redis://localhost:6379/0"),
    l1_ttl=300,
)
```

## Run the cookbook example

```bash
uv run python -m cookbook.tiered_backend.agent
```
