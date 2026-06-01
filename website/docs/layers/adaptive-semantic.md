---
title: "AdaptiveSemanticCache"
---

# AdaptiveSemanticCache

Extends `SemanticCache` with automatic threshold tuning and multi-turn safety guard.

## Why Adaptive?

A fixed similarity threshold of 0.95 sounds safe but production data shows semantic caches hit only 20–45% of traffic. A threshold that is too high misses real hits; too low causes false positives (wrong answers returned).

`AdaptiveSemanticCache` solves this by:

1. **Auto-tuning the threshold** every N lookups to hit a target hit rate (default: 35%)
2. **Multi-turn guard** — skipping semantic lookup for long conversations where overlapping embeddings cause false positives

---

## Usage

```python
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=lambda text: embed_model.encode(text),
    threshold=0.90,            # starting threshold
    target_hit_rate=0.35,      # aim for 35% hits
    adjustment_interval=50,    # re-tune every 50 lookups
    threshold_min=0.75,        # never go below 0.75
    threshold_max=0.99,        # never exceed 0.99
    adjustment_step=0.02,      # nudge by 0.02 per recalibration
    max_turn_count=5,          # skip semantic for > 5-turn conversations
)

# Single-turn query — semantic lookup active
result = cache.get("What is the capital of France?")

# Multi-turn — pass turn_count to suppress semantic lookup when needed
result = cache.get("Tell me more about that", turn_count=6)  # skips vector search

# Store
cache.set("What is the capital of France?", "Paris")
```

### Check current threshold

```python
print(cache.current_threshold)  # adapts automatically over time
```

---

## Configuration Guide

| Parameter | Effect | When to adjust |
|---|---|---|
| `target_hit_rate` | Desired fraction of lookups that are hits | Lower (0.20) for precision; raise (0.45) for recall |
| `adjustment_interval` | How often threshold is recalibrated | Lower = faster adaptation; higher = more stable |
| `threshold_min` | Safety floor — never go below this | Raise if you see wrong answers |
| `threshold_max` | Safety ceiling | Rarely needs changing |
| `max_turn_count` | Multi-turn guard | Match your typical conversation length |

---

## API Reference

Inherits all methods from `SemanticCache`. The `get()` method adds a `turn_count` parameter:

| Method | Extra Parameter | Description |
|---|---|---|
| `get(query, turn_count=0)` | `turn_count: int` | Semantic lookup skipped if `turn_count > max_turn_count` |
| `current_threshold` | — | Current auto-tuned similarity threshold |
