---
title: "Storage Backends"
---

# Storage Backends

OmniCache-AI provides nine interchangeable backends — four key-value stores, one tiered backend, one async backend, and three vector similarity stores. Every backend conforms to a `Protocol`, so you can swap implementations without changing application code.

---

## Key-Value Backends (CacheBackend)

| Backend | Class | Extras | Best For |
|---|---|---|---|
| [In-Memory (LRU)](memory.md) | `InMemoryBackend` | — (core) | Dev, testing, single-process |
| [Async In-Memory](async-memory.md) | `AsyncInMemoryBackend` | — (core) | FastAPI, async LangGraph |
| [Tiered (L1+L2)](tiered.md) | `TieredBackend` | — (core) | Memory speed + Redis persistence |
| [Disk](disk.md) | `DiskBackend` | — (core) | Single-node persistence |
| [Redis](redis.md) | `RedisBackend` | `[redis]` | Shared across processes / services |

## Vector Backends (VectorBackend)

| Backend | Class | Extras | Best For |
|---|---|---|---|
| [FAISS](faiss.md) | `FAISSBackend` | `[vector-faiss]` | Fast in-process similarity |
| [ChromaDB](chroma.md) | `ChromaBackend` | `[vector-chroma]` | Persistent vector store + metadata |
| [Qdrant](qdrant.md) | `QdrantBackend` | `[vector-qdrant]` | Production scale (22ms p95) |
| [Weaviate](weaviate.md) | `WeaviateBackend` | `[vector-weaviate]` | Hybrid search (vector + BM25) |

---

## Decision Flowchart

```mermaid
flowchart TD
    Start(["Which backend?"]) --> Q1{"Multiple processes\nor services?"}

    Q1 -->|Yes| Q1b{"Also need\nfast local reads?"}
    Q1b -->|Yes| TIERED["TieredBackend\nL1=InMemory + L2=Redis"]
    Q1b -->|No| REDIS["RedisBackend"]

    Q1 -->|No| Q2{"Need vector\nsimilarity?"}

    Q2 -->|Yes| Q3{"Need hybrid\nsearch (vector+BM25)?"}
    Q3 -->|Yes| WEAV["WeaviateBackend"]
    Q3 -->|No| Q3b{"Production scale\n10M+ vectors?"}
    Q3b -->|Yes| QDRANT["QdrantBackend"]
    Q3b -->|No| Q3c{"Persist to disk?"}
    Q3c -->|Yes| CHROMA["ChromaBackend"]
    Q3c -->|No| FAISS["FAISSBackend"]

    Q2 -->|No| Q4{"Async framework?"}
    Q4 -->|Yes| AMEM["AsyncInMemoryBackend"]
    Q4 -->|No| Q5{"Survive restarts?"}
    Q5 -->|Yes| DISK["DiskBackend"]
    Q5 -->|No| MEM["InMemoryBackend"]

    style REDIS fill:#dc2626,color:#fff
    style TIERED fill:#b45309,color:#fff
    style FAISS fill:#2563eb,color:#fff
    style CHROMA fill:#7c3aed,color:#fff
    style QDRANT fill:#0e7490,color:#fff
    style WEAV fill:#0f766e,color:#fff
    style DISK fill:#d97706,color:#fff
    style MEM fill:#059669,color:#fff
    style AMEM fill:#047857,color:#fff
```

---

## Protocols

Both protocols are `@runtime_checkable` — verify with `isinstance()`.

### CacheBackend

```python
from omnicache_ai.backends.base import CacheBackend
# get / set / delete / exists / clear / close
```

### AsyncCacheBackend

```python
from omnicache_ai.backends.async_base import AsyncCacheBackend
# async get / set / delete / exists / clear / close
```

### VectorBackend

```python
from omnicache_ai.backends.base import VectorBackend
# add / search / delete / clear / close
```

---

## Custom Backend

Implement the `CacheBackend` protocol — no inheritance required:

```python
class MyBackend:
    def get(self, key: str): ...
    def set(self, key: str, value, ttl=None): ...
    def delete(self, key: str): ...
    def exists(self, key: str) -> bool: ...
    def clear(self): ...
    def close(self): ...
```
