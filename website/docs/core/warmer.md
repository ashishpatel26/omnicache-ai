---
title: "CacheWarmer"
---

# CacheWarmer

Bulk-populate the response cache from known query lists or CSV files before traffic arrives. Eliminates cold-start misses for high-frequency queries.

## Usage

### From a query list

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder, ResponseCache
from omnicache_ai.core.warmer import CacheWarmer
import openai

client = openai.OpenAI()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cache = ResponseCache(manager)
warmer = CacheWarmer(cache)

def generate(messages):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

results = warmer.warm_from_queries(
    queries=[
        "What is RAG?",
        "Explain semantic caching",
        "What is a vector database?",
    ],
    generate_fn=generate,
    model_id="gpt-4o-mini",
    ttl=3600,
)

for query, status in results.items():
    print(f"[{status}] {query}")
# [warmed] What is RAG?
# [warmed] Explain semantic caching
# [warmed] What is a vector database?
```

### From a CSV file

CSV must have a column named `query` (configurable via `query_column`):

```csv
query
What is RAG?
Explain semantic caching
What is a vector database?
```

```python
results = warmer.warm_from_file(
    path="hot_queries.csv",
    generate_fn=generate,
    model_id="gpt-4o-mini",
    ttl=3600,
    query_column="query",   # default
    skip_existing=True,     # skip queries already in cache
)
```

### Async warming

```python
results = await warmer.awarm_from_queries(
    queries=HOT_QUERIES,
    generate_fn=async_generate,
    model_id="gpt-4o-mini",
)
```

---

## skip_existing

`skip_existing=True` (default) avoids re-calling the LLM for queries already in cache. This makes `CacheWarmer` safe to run on startup repeatedly:

```python
# Run on every deployment — only warms uncached queries
warmer.warm_from_file("hot_queries.csv", generate_fn, model_id="gpt-4o-mini")
```

---

## API Reference

| Method | Description |
|---|---|
| `warm_from_queries(queries, generate_fn, model_id, ttl, skip_existing)` | Warm from a list of query strings |
| `warm_from_file(path, generate_fn, model_id, ttl, query_column, skip_existing)` | Warm from CSV |
| `awarm_from_queries(queries, generate_fn, model_id, ttl, skip_existing)` | Async version |

Returns `dict[str, str]` mapping `query → "hit"` (skipped) or `"warmed"` (newly cached).
