# QdrantBackend

Qdrant-based vector similarity backend — the fastest vector DB in 2026 (22ms p95 at 10M vectors).

## Overview

`QdrantBackend` uses Qdrant's cosine similarity index for approximate nearest-neighbour search. Supports both in-memory mode (no server required) and remote Qdrant Cloud or self-hosted instances.

**When to use:**

- Production semantic caching at scale (>100k vectors)
- You need sub-25ms vector search at 10M+ vectors
- You're already running Qdrant for other workloads

---

## Installation

=== "pip"
    ```bash
    pip install 'omnicache-ai[vector-qdrant]'
    ```

=== "uv"
    ```bash
    uv add 'omnicache-ai[vector-qdrant]'
    ```

---

## Usage

### In-memory mode (no server)

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import QdrantBackend
from omnicache_ai.layers.semantic_cache import SemanticCache

vector = QdrantBackend(url=":memory:", collection="semantic", dim=1536)
exact = InMemoryBackend()
cache = SemanticCache(exact, vector, embed_fn=my_embed, threshold=0.95)

cache.set("What is the capital of France?", "Paris")
result = cache.get("What is France's capital?")  # "Paris"
```

### Remote Qdrant Cloud

```python
vector = QdrantBackend(
    url="https://your-cluster.qdrant.io",
    api_key="your-qdrant-api-key",
    collection="omnicache-semantic",
    dim=1536,
)
```

### Self-hosted Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

```python
vector = QdrantBackend(url="http://localhost:6333", collection="omnicache", dim=1536)
```

### With AdaptiveSemanticCache

```python
from omnicache_ai.backends.redis_backend import RedisBackend
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

cache = AdaptiveSemanticCache(
    exact_backend=RedisBackend(url="redis://localhost:6379/0"),
    vector_backend=QdrantBackend(url=":memory:", dim=1536),
    embed_fn=my_embed,
    target_hit_rate=0.35,
)
```

!!! tip "Cosine metric"
    QdrantBackend creates collections with `Distance.COSINE`. No need to pre-normalize vectors — Qdrant handles it internally.

!!! note "Deletion support"
    Unlike FAISS, QdrantBackend supports true deletion (`delete(key)`) without rebuilding the index.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | `":memory:"` | Qdrant URL or `:memory:` for in-process |
| `collection` | `str` | `"omnicache"` | Qdrant collection name |
| `api_key` | `str \| None` | `None` | Qdrant Cloud API key |
| `dim` | `int` | `1536` | Embedding dimension |

### Methods

| Method | Signature | Returns | Description |
|---|---|---|---|
| `add` | `(key: str, vector: np.ndarray, metadata: dict)` | `None` | Index a vector |
| `search` | `(vector: np.ndarray, top_k: int = 1)` | `list[tuple[str, float]]` | Return (key, score) pairs |
| `delete` | `(key: str)` | `None` | Remove a vector |
| `clear` | `()` | `None` | Recreate the collection (drop all vectors) |
| `close` | `()` | `None` | Clear and release |

---

## Source

:material-file-code: `omnicache_ai/backends/vector_backend.py` — `QdrantBackend` class
