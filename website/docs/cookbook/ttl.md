---
title: "TTL Policies"
---

# TTL Policies

Control how long cached entries live with global defaults, per-layer overrides,
environment-variable configuration, or infinite retention.

```bash
pip install omnicache-ai
```

---

## 11.1 Global TTL

Apply a single time-to-live to every cached entry.

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder, TTLPolicy

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    ttl_policy=TTLPolicy(default_ttl=600),  # 10 minutes for everything
)
```

---

## 11.2 Per-layer TTL

Assign different TTLs to each cache layer so that stable data (embeddings) lives
longer while volatile data (LLM responses) expires quickly.

```python
from omnicache_ai import TTLPolicy, CacheManager, InMemoryBackend, CacheKeyBuilder

policy = TTLPolicy(
    default_ttl=3600,
    per_type={
        "embed":     86_400,   # 24 h — embeddings rarely change
        "retrieval": 3_600,    # 1 h  — document corpus updates hourly
        "context":   1_800,    # 30 min — session context
        "response":  300,      # 5 min — LLM responses can go stale
    },
)
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    ttl_policy=policy,
)
```

:::tip
Start with conservative (shorter) TTLs and increase them once you've verified that
cache staleness is not an issue for your use case.
:::


---

## 11.3 Per-layer TTL from environment

Set TTLs through environment variables for deployment-time configuration without
code changes.

```bash
export OMNICACHE_TTL_EMBEDDING=86400
export OMNICACHE_TTL_RETRIEVAL=3600
export OMNICACHE_TTL_CONTEXT=1800
export OMNICACHE_TTL_RESPONSE=300
```

```python
from omnicache_ai import CacheManager, OmnicacheSettings

manager = CacheManager.from_settings(OmnicacheSettings.from_env())
```

---

## 11.4 No TTL (cache forever)

Disable expiration entirely. Entries remain until explicitly invalidated or the
backend is cleared.

```python
from omnicache_ai import TTLPolicy, CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    ttl_policy=TTLPolicy(default_ttl=None),  # None = no expiry
)
```

:::note
Without a TTL, the cache will grow indefinitely. Combine with `InMemoryBackend(max_size=...)`
or periodic tag-based invalidation to keep memory usage in check.
:::
