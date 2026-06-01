"""Cache metrics and observability with omnicache-ai.

Demonstrates:
- CacheMetrics snapshot (hits, misses, hit_rate, cost saved)
- Multi-tenant namespacing with CacheManager.for_tenant()
- CacheWarmer bulk pre-population
- RequestConfig per-request overrides

Run:
    uv run python -m cookbook.metrics.agent
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend, ResponseCache
from omnicache_ai.core.request_config import RequestConfig
from omnicache_ai.core.warmer import CacheWarmer


def fake_llm(messages: list) -> dict:
    time.sleep(0.01)
    return {"answer": f"Response to: {messages[-1]['content']}"}


HOT_QUERIES = [
    "What is RAG?",
    "Explain semantic caching",
    "What is a vector database?",
    "How does LRU eviction work?",
]


def main() -> None:
    manager = CacheManager(
        backend=InMemoryBackend(max_size=1000),
        key_builder=CacheKeyBuilder(namespace="cookbook-metrics"),
    )

    # ── 1. Cache Warming ──────────────────────────────────────────────
    print("=== 1. Cache Warming ===")
    cache = ResponseCache(manager)
    warmer = CacheWarmer(cache)

    t0 = time.perf_counter()
    results = warmer.warm_from_queries(HOT_QUERIES, fake_llm, model_id="sim", ttl=3600)
    t1 = time.perf_counter()
    for q, status in results.items():
        print(f"  [{status}] {q}")
    print(f"Warmed in {t1 - t0:.3f}s")

    # ── 2. Live queries (should all hit) ─────────────────────────────
    print("\n=== 2. Querying warmed cache ===")
    for q in HOT_QUERIES:
        r = cache.get([{"role": "user", "content": q}], model_id="sim")
        print(f"  {'HIT' if r else 'MISS'} — {q}")

    # ── 3. Metrics snapshot ──────────────────────────────────────────
    print("\n=== 3. Metrics ===")
    snap = manager.metrics.snapshot()
    for k, v in snap.items():
        print(f"  {k}: {v}")

    # ── 4. Multi-tenant namespacing ──────────────────────────────────
    print("\n=== 4. Multi-tenant namespacing ===")
    tenant_a = manager.for_tenant("acme-corp")
    tenant_b = manager.for_tenant("beta-inc")

    cache_a = ResponseCache(tenant_a)
    cache_b = ResponseCache(tenant_b)

    msg = [{"role": "user", "content": "What is our SLA?"}]
    cache_a.set(msg, {"answer": "99.9% uptime for acme-corp"}, model_id="sim")
    cache_b.set(msg, {"answer": "99.5% uptime for beta-inc"}, model_id="sim")

    r_a = cache_a.get(msg, model_id="sim")
    r_b = cache_b.get(msg, model_id="sim")
    print(f"  Tenant A: {r_a}")
    print(f"  Tenant B: {r_b}")
    assert r_a != r_b, "Tenants are isolated — different values for same key"
    print("  Tenant isolation: ✓")

    # ── 5. Per-request skip_cache ────────────────────────────────────
    print("\n=== 5. Per-request RequestConfig (skip_cache) ===")
    cfg = RequestConfig(skip_cache=True, ttl=10)
    msg2 = [{"role": "user", "content": "Force fresh answer"}]

    # skip_cache=True means we bypass and always call the LLM
    if not cfg.skip_cache:
        result = cache.get(msg2, model_id="sim")
    else:
        result = None

    if result is None:
        result = fake_llm(msg2)
        print(f"  Fresh call (skip_cache=True): {result}")
    else:
        print(f"  Cached: {result}")


if __name__ == "__main__":
    main()
