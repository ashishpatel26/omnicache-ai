---
title: "PineconeBackend"
---

# PineconeBackend

Pinecone serverless vector backend for semantic caching at cloud scale. Creates the Pinecone index automatically if it doesn't exist.

## Installation

```bash
pip install 'omnicache-ai[vector-pinecone]'
```

---

## Usage

### Basic setup with SemanticCache

```python
from omnicache_ai.backends.pinecone_backend import PineconeBackend
from omnicache_ai import SemanticCache, InMemoryBackend

vector_backend = PineconeBackend(
    api_key="pc-your-api-key",
    index_name="omnicache-semantic",
    dim=1536,
)

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=vector_backend,
    embed_fn=lambda text: embed_model.encode(text),
    threshold=0.92,
)

cache.set("What is the capital of France?", "Paris")
result = cache.get("France's capital city?")  # "Paris"
```

### Custom cloud and region

```python
vector_backend = PineconeBackend(
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
from omnicache_ai.backends.redis_backend import RedisBackend

cache = AdaptiveSemanticCache(
    exact_backend=RedisBackend(url="redis://localhost:6379/0"),
    vector_backend=PineconeBackend(
        api_key="pc-...",
        index_name="omnicache",
        dim=1536,
    ),
    embed_fn=embed_fn,
    target_hit_rate=0.35,
)
```

:::note[Auto index creation]
If `index_name` doesn't exist in your Pinecone account, the backend creates it automatically using the specified `cloud` and `region` with cosine metric.
:::

:::tip[Serverless vs dedicated]
Pinecone serverless scales to zero — no idle cost. Use serverless for dev/staging. For production SLAs requiring consistent p99 latency, consider Qdrant or a dedicated Pinecone pod.
:::

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | Pinecone API key |
| `index_name` | `str` | required | Index name (created if absent) |
| `dim` | `int` | required | Embedding dimension |
| `cloud` | `str` | `"aws"` | Cloud provider for index creation |
| `region` | `str` | `"us-east-1"` | Region for index creation |
| `top_k` | `int` | `1` | Default number of candidates to fetch |

### Methods

| Method | Description |
|---|---|
| `add(key, vector, metadata)` | Upsert a vector with key stored as metadata |
| `search(vector, top_k)` | Return `(key, score)` pairs for nearest neighbours |
| `delete(key)` | Remove a vector by key |
| `clear()` | Delete all vectors (`delete_all=True`) |
| `close()` | No-op (Pinecone client is stateless) |
