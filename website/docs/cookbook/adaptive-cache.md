---
title: "Adaptive Semantic Cache"
---

# Adaptive Semantic Cache + OmniCache-AI

Auto-tune the similarity threshold based on observed hit rate — no manual threshold tuning required.

## Install

```bash
pip install 'omnicache-ai[vector-faiss]'
```

## Example

```python
import numpy as np
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

# Simple deterministic embedder for demo
def embed(text: str) -> np.ndarray:
    rng = np.random.default_rng(hash(text) % (2**32))
    return rng.random(128).astype(np.float32)

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=128),
    embed_fn=embed,
    threshold=0.90,         # starting threshold
    target_hit_rate=0.35,   # self-tune toward 35% hits
    adjustment_interval=10, # re-tune every 10 lookups
    threshold_min=0.70,
    threshold_max=0.99,
    max_turn_count=5,       # skip semantic for > 5-turn chats
)

# Populate
cache.set("What is the capital of France?", "Paris")
cache.set("What is semantic caching?", "Caching by meaning.")

# Exact hit
print(cache.get("What is the capital of France?"))  # "Paris"

# Semantic hit (similar wording)
print(cache.get("Capital city of France?"))  # "Paris" (if above threshold)

# Multi-turn guard — turn_count > max_turn_count skips semantic lookup
print(cache.get("Tell me more", turn_count=6))  # None (skipped)

print(f"Current threshold: {cache.current_threshold:.3f}")
```

## With real embeddings

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=384),
    embed_fn=lambda text: model.encode(text),
    target_hit_rate=0.35,
    max_turn_count=5,
)
```

## Why adaptive?

Production semantic caches hit only **20–45%** of traffic with a fixed threshold. `AdaptiveSemanticCache` observes your actual hit rate and nudges the threshold automatically — higher if too many false negatives, lower if false positives appear.
