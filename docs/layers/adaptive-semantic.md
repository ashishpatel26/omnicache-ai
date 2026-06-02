# AdaptiveSemanticCache

Self-tuning semantic cache that automatically adjusts the similarity threshold to hit a target hit rate.

---

## Overview

`AdaptiveSemanticCache` extends [`SemanticCache`](semantic.md) with two production features:

1. **Adaptive threshold** — recalibrates the cosine similarity cutoff every N lookups to approach a target hit rate (default 35%). If hit rate is too low, the threshold drops (more permissive); if too high, it rises (more restrictive).

2. **Multi-turn guard** — skips semantic search for conversations longer than `max_turn_count` messages, where semantic overlap between turns causes false positives.

**When to use:** Production semantic caching where a fixed threshold either over-matches (bad answers) or under-matches (no cache benefit).

!!! tip "Production default"
    `target_hit_rate=0.35` matches real-world LLM cache hit rates (20–45%). Start there and observe `current_threshold` stabilising.

---

## Usage

### Basic setup

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

def embed(text: str) -> np.ndarray:
    # your embedding function
    ...

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=embed,
    threshold=0.90,          # starting threshold
    target_hit_rate=0.35,    # auto-tune toward 35%
    adjustment_interval=100, # recalibrate every 100 lookups
)
```

### Store and retrieve

```python
cache.set("What is the capital of France?", "Paris")

# Exact match
result = cache.get("What is the capital of France?")  # "Paris"

# Semantic match (similar phrasing)
result = cache.get("France's capital city?")  # "Paris" if cosine similarity ≥ threshold
```

### Multi-turn guard

```python
# For long conversations, skip semantic search to avoid false positives
result = cache.get("Summarise our discussion", turn_count=12)
# turn_count > max_turn_count (default 10) → skips vector search, exact match only
```

### Inspect current threshold

```python
print(cache.current_threshold)  # e.g. 0.87 after auto-tuning
```

### Qdrant backend (production scale)

```python
from omnicache_ai.backends.vector_backend import QdrantBackend

cache = AdaptiveSemanticCache(
    exact_backend=RedisBackend(url="redis://..."),
    vector_backend=QdrantBackend(url="http://qdrant:6333", dim=1536),
    embed_fn=embed,
    target_hit_rate=0.35,
)
```

---

## How It Works

1. Call `get(query, turn_count)` — if `turn_count > max_turn_count`, skip to exact-match only
2. Otherwise delegate to `SemanticCache.get(query)` (exact then vector search)
3. Track window hits and total lookups
4. Every `adjustment_interval` lookups — compute actual hit rate:
   - Actual < target → lower threshold by `adjustment_step` (floor: `threshold_min`)
   - Actual > target + 0.05 → raise threshold by `adjustment_step` (ceiling: `threshold_max`)
5. Reset window counters

```
get(query, turn_count=N)
      |
  turn_count > max_turns?
  /                    \
yes                     no
 |                       |
exact match only    SemanticCache.get(query)
                          |
                   track hit/miss
                          |
                   window_total >= interval?
                          |
                   adjust threshold
```

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exact_backend` | `CacheBackend` | *(required)* | KV backend for exact matches |
| `vector_backend` | `VectorBackend` | *(required)* | Vector backend for similarity search |
| `embed_fn` | `Callable[[str], np.ndarray]` | *(required)* | Embedding function |
| `threshold` | `float` | `0.90` | Initial similarity threshold |
| `key_builder` | `CacheKeyBuilder \| None` | auto | Key builder |
| `serializer` | `Serializer \| None` | `PickleSerializer` | Value serializer |
| `target_hit_rate` | `float` | `0.35` | Desired hit rate (0.0–1.0) |
| `adjustment_interval` | `int` | `100` | Recalibrate every N lookups |
| `threshold_min` | `float` | `0.70` | Minimum allowed threshold |
| `threshold_max` | `float` | `0.99` | Maximum allowed threshold |
| `adjustment_step` | `float` | `0.02` | Nudge amount per recalibration |
| `max_turn_count` | `int` | `10` | Skip semantic for conversations longer than N turns |

### Methods

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `get` | `(query: str, turn_count: int = 0)` | `Any \| None` | Retrieve with adaptive threshold |
| `set` | `(query: str, value: Any, ttl, tags)` | `None` | Store (inherited from SemanticCache) |
| `delete` | `(query: str)` | `None` | Remove entry |
| `clear` | `()` | `None` | Flush all entries |
| `current_threshold` | property | `float` | Current similarity threshold |

---

## Source

:material-file-code: `omnicache_ai/layers/adaptive_semantic_cache.py`
