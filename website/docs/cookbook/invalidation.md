---
title: "Tag-Based Invalidation"
---

# Tag-Based Invalidation

Invalidate related cache entries in one call -- by model, session, agent, or any custom tag.

```bash
pip install omnicache-ai
```

---

## 10.1 Invalidate all entries for a model

Remove all cached responses associated with a specific model version.

```python
from omnicache_ai import (
    CacheManager, InMemoryBackend, CacheKeyBuilder,
    InvalidationEngine, ResponseCache,
)

tag_store = InMemoryBackend()
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="inv"),
    invalidation_engine=InvalidationEngine(tag_store),
)
rc = ResponseCache(manager)

msgs = [{"role": "user", "content": "Hello"}]
rc.set(msgs, "Hi!",   model_id="gpt-4o",    tags=["model:gpt-4o"])
rc.set(msgs, "Hey!",  model_id="gpt-4o",    tags=["model:gpt-4o"])
rc.set(msgs, "Hola!", model_id="gpt-4o-mini", tags=["model:gpt-4o-mini"])

# Invalidate only gpt-4o entries
count = rc.invalidate_model("gpt-4o")
print(f"Removed {count} gpt-4o entries")

# gpt-4o-mini entry is untouched
print(rc.get(msgs, "gpt-4o-mini"))  # "Hola!"
```

---

## 10.2 Invalidate a user session

Clear all cached conversation turns for a specific user session.

```python
from omnicache_ai import (
    CacheManager, InMemoryBackend, CacheKeyBuilder,
    InvalidationEngine, ContextCache,
)

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)
ctx = ContextCache(manager)

ctx.set("user-123", 0, [{"role": "user", "content": "Hello"}])
ctx.set("user-123", 1, [{"role": "assistant", "content": "Hi there!"}])

ctx.invalidate_session("user-123")  # removes all turns for user-123
print(ctx.get("user-123", 0))  # None
```

---

## 10.3 Custom tags across frameworks

Use deployment-version or environment tags to surgically invalidate cache entries
after a new deploy without clearing unrelated data.

```python
from omnicache_ai import (
    CacheManager, InMemoryBackend, CacheKeyBuilder, InvalidationEngine,
)

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="multi"),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)

# Tag entries with a deployment version
manager.set("k1", "v1", tags=["deploy:v1.0", "env:prod"])
manager.set("k2", "v2", tags=["deploy:v1.0", "env:prod"])
manager.set("k3", "v3", tags=["deploy:v2.0", "env:prod"])

# After deploying v2.0 — clear all v1.0 cache
count = manager.invalidate("deploy:v1.0")
print(f"Cleared {count} entries from v1.0 deploy")

# v2.0 entry is untouched
print(manager.get("k3"))  # "v3"
```

:::tip
Combine multiple tags on each entry (e.g., `model:gpt-4o`, `deploy:v2.0`, `env:prod`)
for fine-grained invalidation. Invalidating any one tag removes just the matching entries.
:::
