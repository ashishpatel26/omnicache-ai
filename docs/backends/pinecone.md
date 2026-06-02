# PineconeBackend

Pinecone serverless vector backend for semantic caching at cloud scale.

## Overview

`PineconeBackend` uses a Pinecone serverless index for approximate nearest-neighbour search. The index is created automatically if it doesn't exist.

**When to use:**

- You're already on Pinecone and want zero-ops vector scaling
- You need serverless vector search without managing Qdrant/FAISS infrastructure
- Multi-tenant deployments where a single managed Pinecone index serves many namespaces

---

## Installation

=== "pip"
    ```bash
    pip install 'omnicache-ai[vector-pinecone]'
    ```

=== "uv"
    ```bash
    uv add 'omnicache-ai[vector-pinecone]'
    ```

---

## Usage

### Basic setup

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.pinecone_backend import PineconeBackend
from omnicache_ai.layers.semantic_cache import SemanticCache

vector = PineconeBackend(
    api_key="pc-your-api-key",
    index_name="omnicache-semantic",
    dim=1536,
)
exact = InMemoryBackend()
cache = SemanticCache(exact, vector, embed_fn=my_embed, threshold=0.95)

cache.set("What is the capital of France?", "Paris")
result = cache.get("France's capital city?")
```

### Custom cloud/region

```python
vector = PineconeBackend(
    api_key="pc-your-api-key",
    index_name="omnicache-eu",
    dim=1536,
    cloud="gcp",
    region="europe-west1",
)
```

### With AdaptiveSemanticCache

```python
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

cache = AdaptiveSemanticCache(
    exact_backend=RedisBackend(url="redis://..."),
    vector_backend=PineconeBackend(api_key="...", index_name="omnicache", dim=1536),
    embed_fn=my_embed,
    target_hit_rate=0.35,
)
```

!!! note "Index auto-creation"
    If `index_name` doesn't exist in your Pinecone account, the backend creates it automatically using the specified `cloud` and `region`.

!!! tip "Cosine metric"
    PineconeBackend creates indices with `metric="cosine"`. All vectors are assumed to be pre-normalised or will be handled by Pinecone.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | *(required)* | Pinecone API key |
| `index_name` | `str` | *(required)* | Index name (created if absent) |
| `dim` | `int` | *(required)* | Embedding dimension |
| `cloud` | `str` | `"aws"` | Cloud provider for index creation |
| `region` | `str` | `"us-east-1"` | Region for index creation |
| `top_k` | `int` | `1` | Default number of candidates to fetch |

### Methods

| Method | Signature | Returns | Description |
|---|---|---|---|
| `add` | `(key: str, vector: np.ndarray, metadata: dict)` | `None` | Upsert a vector with key as metadata |
| `search` | `(vector: np.ndarray, top_k: int = 1)` | `list[tuple[str, float]]` | Return (key, score) pairs |
| `delete` | `(key: str)` | `None` | Remove a vector by key |
| `clear` | `()` | `None` | Delete all vectors (`delete_all=True`) |
| `close` | `()` | `None` | No-op (Pinecone client is stateless) |

---

## Source

:material-file-code: `omnicache_ai/backends/pinecone_backend.py`
