---
title: "WeaviateBackend"
---

# WeaviateBackend

Weaviate-based vector similarity backend. The only vector database with native hybrid search (semantic + BM25 keyword) without a separate layer. Supports embedded (local) and Weaviate Cloud instances.

## Installation

```bash
pip install 'omnicache-ai[vector-weaviate]'
```

---

## Usage

### Embedded (local, no server)

```python
from omnicache_ai.backends.vector_backend import WeaviateBackend
from omnicache_ai import SemanticCache, InMemoryBackend

vector_backend = WeaviateBackend()  # embedded local instance

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=vector_backend,
    embed_fn=lambda text: embed_model.encode(text),
)
```

### Weaviate Cloud

```python
vector_backend = WeaviateBackend(
    url="https://your-cluster.weaviate.network",
    api_key="your-weaviate-api-key",
    class_name="OmnicacheEntry",
)
```

---

## Why Weaviate?

Weaviate is the only vector database with **native hybrid search** — it combines BM25 keyword ranking with vector similarity in a single query without a separate BM25 layer. This makes it ideal for RAG caches where queries mix keyword specificity (e.g. product codes) with semantic meaning.

| Feature | Weaviate | Qdrant | FAISS |
|---|---|---|---|
| Native hybrid search | ✅ | ❌ | ❌ |
| Persistent | ✅ | ✅ | ❌ |
| Cloud-managed | ✅ | ✅ | ❌ |
| Embedded (no server) | ✅ | ❌ | ✅ |

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str \| None` | `None` | Weaviate instance URL. `None` = embedded |
| `api_key` | `str \| None` | `None` | Weaviate Cloud API key |
| `class_name` | `str` | `"OmnicacheEntry"` | Weaviate class name for cache entries |
