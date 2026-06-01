---
title: "QdrantBackend"
---

# QdrantBackend

Qdrant-based vector similarity backend. Fastest vector DB in 2026 (22ms p95 at 10M vectors). Supports both in-memory mode (no server required) and remote Qdrant Cloud / self-hosted.

## Installation

```bash
pip install 'omnicache-ai[vector-qdrant]'
```

---

## Usage

### In-Memory (no server needed)

```python
from omnicache_ai.backends.vector_backend import QdrantBackend
from omnicache_ai import SemanticCache, InMemoryBackend, CacheKeyBuilder

vector_backend = QdrantBackend(dim=1536)  # default: :memory:

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=vector_backend,
    embed_fn=lambda text: embed_model.encode(text),
    threshold=0.92,
)
```

### Remote (Qdrant Cloud)

```python
vector_backend = QdrantBackend(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key",
    collection="omnicache",
    dim=1536,
)
```

### Self-Hosted

```bash
docker run -p 6333:6333 qdrant/qdrant
```

```python
vector_backend = QdrantBackend(
    url="http://localhost:6333",
    collection="omnicache",
    dim=1536,
)
```

---

## Why Qdrant?

| Metric | Qdrant | FAISS (in-proc) | Chroma |
|---|---|---|---|
| p95 latency @ 10M vectors | **22ms** | ~5ms (no server) | ~80ms |
| True deletion support | ✅ | ❌ (workaround) | ✅ |
| Persistent by default | ✅ | ❌ | ✅ |
| Distributed / multi-node | ✅ | ❌ | ❌ |
| Hybrid search (vector + BM25) | ❌ | ❌ | ❌ |

Use Qdrant when you need production-grade persistence, true deletion, and sub-30ms latency at scale.

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | `":memory:"` | Qdrant URL or `:memory:` for in-process |
| `collection` | `str` | `"omnicache"` | Qdrant collection name |
| `api_key` | `str \| None` | `None` | Qdrant Cloud API key |
| `dim` | `int` | `1536` | Embedding dimension |
