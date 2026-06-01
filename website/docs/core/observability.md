---
title: "Observability"
---

# Observability

OmniCache-AI provides built-in metrics via `CacheMetrics` and two exporters for production monitoring: Prometheus and OpenTelemetry.

## CacheMetrics

Every `CacheManager` instance has a `metrics` property exposing live counters:

```python
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())

# Use the cache...
manager.get("key")
manager.set("key", b"value")

snap = manager.metrics.snapshot()
print(snap)
# {
#   'hits': 0, 'misses': 1, 'evictions': 0, 'sets': 1,
#   'hit_rate': 0.0, 'miss_rate': 1.0,
#   'provider_cache_hits': 0,
#   'estimated_tokens_saved': 0,
#   'estimated_cost_saved_usd': 0.0
# }
```

### Fields

| Field | Description |
|---|---|
| `hits` | Exact or semantic cache hits |
| `misses` | Cache misses requiring a downstream call |
| `evictions` | LRU evictions from `InMemoryBackend` |
| `sets` | Total cache writes |
| `hit_rate` | `hits / (hits + misses)` |
| `provider_cache_hits` | Server-side prompt cache hits (Anthropic/OpenAI) |
| `estimated_tokens_saved` | Tokens saved via provider prompt caching |
| `estimated_cost_saved_usd` | Estimated USD saved via provider caching |

---

## Prometheus Exporter

```bash
pip install 'omnicache-ai[observability]'
```

```python
from omnicache_ai.core.exporters import PrometheusExporter

exporter = PrometheusExporter(manager.metrics, port=9090, namespace="myapp")
exporter.start()  # non-blocking — scrapes at http://localhost:9090/metrics
```

### Exposed metrics

| Metric | Type | Description |
|---|---|---|
| `myapp_cache_hits_total` | Counter | Total cache hits |
| `myapp_cache_misses_total` | Counter | Total cache misses |
| `myapp_cache_evictions_total` | Counter | Total LRU evictions |
| `myapp_cache_sets_total` | Counter | Total cache writes |
| `myapp_cache_hit_rate` | Gauge | Current hit rate |
| `myapp_provider_cache_hits_total` | Counter | Provider prompt cache hits |
| `myapp_tokens_saved_total` | Counter | Tokens saved via provider caching |
| `myapp_cost_saved_usd` | Gauge | Estimated USD saved |

### Prometheus config example

```yaml
scrape_configs:
  - job_name: omnicache
    static_configs:
      - targets: ["localhost:9090"]
```

---

## OpenTelemetry Exporter

```python
from omnicache_ai.core.exporters import OpenTelemetryExporter

exporter = OpenTelemetryExporter(
    metrics=manager.metrics,
    endpoint="http://otel-collector:4317",
    export_interval_ms=10_000,
)
exporter.start()
```

Pushes `omnicache.hit_rate`, `omnicache.hits`, `omnicache.misses`, and `omnicache.cost_saved_usd` as observable gauges to any OTEL-compatible backend (Grafana, Datadog, Honeycomb, etc.).

---

## CLI

Quick snapshot without code:

```bash
python -m omnicache_ai stats
```

```json
{
  "hits": 142,
  "misses": 31,
  "evictions": 0,
  "sets": 31,
  "hit_rate": 0.821,
  "miss_rate": 0.179,
  "provider_cache_hits": 12,
  "estimated_tokens_saved": 8400,
  "estimated_cost_saved_usd": 0.025
}
```
