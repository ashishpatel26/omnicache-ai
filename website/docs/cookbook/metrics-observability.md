---
title: "Metrics & Observability"
---

# Metrics & Observability + OmniCache-AI

Track hit rates, cost savings, warm the cache, and use multi-tenant namespacing.

## CacheMetrics snapshot

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())

# ... use the cache ...

snap = manager.metrics.snapshot()
print(snap)
# {
#   'hits': 142, 'misses': 31, 'evictions': 0, 'sets': 31,
#   'hit_rate': 0.821, 'miss_rate': 0.179,
#   'provider_cache_hits': 12,
#   'estimated_tokens_saved': 8400,
#   'estimated_cost_saved_usd': 0.025
# }
```

## Cache Warming

```python
from omnicache_ai import ResponseCache
from omnicache_ai.core.warmer import CacheWarmer

cache = ResponseCache(manager)
warmer = CacheWarmer(cache)

results = warmer.warm_from_queries(
    queries=["What is RAG?", "Explain caching", "What is a vector DB?"],
    generate_fn=my_llm_fn,
    model_id="gpt-4o-mini",
    ttl=3600,
)
for q, status in results.items():
    print(f"[{status}] {q}")
```

## Multi-tenant namespacing

```python
tenant_a = manager.for_tenant("acme-corp")
tenant_b = manager.for_tenant("beta-inc")

from omnicache_ai import ResponseCache
cache_a = ResponseCache(tenant_a)
cache_b = ResponseCache(tenant_b)

msg = [{"role": "user", "content": "What is our SLA?"}]
cache_a.set(msg, {"answer": "99.9% uptime"}, model_id="gpt-4o")
cache_b.set(msg, {"answer": "99.5% uptime"}, model_id="gpt-4o")

# Each tenant gets their own value — fully isolated
print(cache_a.get(msg, model_id="gpt-4o"))  # 99.9%
print(cache_b.get(msg, model_id="gpt-4o"))  # 99.5%
```

## Prometheus export

```bash
pip install 'omnicache-ai[observability]'
```

```python
from omnicache_ai.core.exporters import PrometheusExporter

exporter = PrometheusExporter(manager.metrics, port=9090)
exporter.start()
# Scrape: http://localhost:9090/metrics
```

## CLI stats

```bash
python -m omnicache_ai stats
```

## Run the cookbook example

```bash
uv run python -m cookbook.metrics.agent
```
