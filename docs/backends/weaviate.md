# WeaviateBackend

Weaviate-based vector similarity backend — the only vector DB with native hybrid search (vector + BM25 keyword).

## Overview

`WeaviateBackend` uses Weaviate's `near_vector` search for cosine similarity matching. Supports both embedded (local) and cloud Weaviate instances.

**When to use:**

- You need hybrid semantic + keyword search over cached entries
- You're already running Weaviate for other workloads
- You want a managed cloud vector store with filtering capabilities

---

## Installation

=== "pip"
    ```bash
    pip install 'omnicache-ai[vector-weaviate]'
    ```

=== "uv"
    ```bash
    uv add 'omnicache-ai[vector-weaviate]'
    ```

---

## Usage

### Embedded (local, no server)

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import WeaviateBackend
from omnicache_ai.layers.semantic_cache import SemanticCache

vector = WeaviateBackend()  # embedded local instance
exact = InMemoryBackend()
cache = SemanticCache(exact, vector, embed_fn=my_embed, threshold=0.95)

cache.set("What is the capital of France?", "Paris")
result = cache.get("France's capital city?")  # "Paris"
```

### Weaviate Cloud

```python
vector = WeaviateBackend(
    url="https://your-cluster.weaviate.io",
    api_key="your-weaviate-api-key",
    class_name="OmnicacheEntry",
)
```

### Self-hosted Weaviate

```bash
docker run -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:latest
```

```python
vector = WeaviateBackend(url="http://localhost:8080")
```

### With AdaptiveSemanticCache

```python
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=WeaviateBackend(),
    embed_fn=my_embed,
    target_hit_rate=0.35,
)
```

!!! note "Certainty score"
    Weaviate returns `certainty` (0–1) as the similarity score. This is equivalent to cosine similarity for normalised vectors.

!!! warning "Connection lifecycle"
    Call `backend.close()` when done — it closes the Weaviate client connection.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str \| None` | `None` | Weaviate URL; `None` = embedded local |
| `api_key` | `str \| None` | `None` | Weaviate Cloud API key |
| `class_name` | `str` | `"OmnicacheEntry"` | Weaviate class name for cache entries |

### Methods

| Method | Signature | Returns | Description |
|---|---|---|---|
| `add` | `(key: str, vector: np.ndarray, metadata: dict)` | `None` | Index a vector |
| `search` | `(vector: np.ndarray, top_k: int = 1)` | `list[tuple[str, float]]` | Return (key, certainty) pairs |
| `delete` | `(key: str)` | `None` | Remove a vector by key |
| `clear` | `()` | `None` | Delete and recreate the Weaviate class |
| `close` | `()` | `None` | Close the Weaviate client connection |

---

## Source

:material-file-code: `omnicache_ai/backends/vector_backend.py` — `WeaviateBackend` class
