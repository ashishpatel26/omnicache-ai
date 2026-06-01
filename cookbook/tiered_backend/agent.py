"""Tiered backend (L1 memory + L2 disk) with omnicache-ai.

Demonstrates:
- TieredBackend: in-memory L1 for speed, disk L2 for persistence
- L2 → L1 promotion on cache hit (subsequent reads stay in memory)
- CacheMetrics tracking across both tiers

Run:
    uv run python -m cookbook.tiered_backend.agent
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnicache_ai import (
    CacheKeyBuilder,
    CacheManager,
    DiskBackend,
    InMemoryBackend,
    ResponseCache,
    TieredBackend,
)


def simulate_llm(messages: list) -> dict:
    """Fake LLM — returns deterministic response."""
    time.sleep(0.05)  # simulate 50ms API call
    return {"content": f"Answer to: {messages[-1]['content']}", "model": "simulated"}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # L1: fast in-memory (evicted on process restart)
        # L2: disk (survives restarts, shared across processes)
        backend = TieredBackend(
            l1=InMemoryBackend(max_size=100),
            l2=DiskBackend(directory=tmpdir),
            l1_ttl=300,  # 5-min local copy
        )

        manager = CacheManager(
            backend=backend,
            key_builder=CacheKeyBuilder(namespace="cookbook-tiered"),
        )
        cache = ResponseCache(manager)

        messages = [{"role": "user", "content": "What is semantic caching?"}]

        print("=== First call (miss → LLM → stored in L1 + L2) ===")
        t0 = time.perf_counter()
        r1 = cache.get_or_generate(messages, simulate_llm, model_id="sim")
        t1 = time.perf_counter()
        print(f"Response: {r1}")
        print(f"Time: {t1 - t0:.3f}s")

        print("\n=== Second call (L1 hit — in-memory) ===")
        t2 = time.perf_counter()
        r2 = cache.get_or_generate(messages, simulate_llm, model_id="sim")
        t3 = time.perf_counter()
        print(f"Response: {r2}")
        print(f"Time: {t3 - t2:.3f}s")
        print(f"Speedup: {(t1 - t0) / max(t3 - t2, 0.0001):.0f}x faster")

        # Simulate process restart by clearing L1 only
        backend._l1.clear()

        print("\n=== Third call (L1 cold, L2 hit → promotes to L1) ===")
        t4 = time.perf_counter()
        r3 = cache.get_or_generate(messages, simulate_llm, model_id="sim")
        t5 = time.perf_counter()
        print(f"Response: {r3}")
        print(f"Time: {t5 - t4:.3f}s")

        print("\n=== Fourth call (L1 warm again after promotion) ===")
        t6 = time.perf_counter()
        r4 = cache.get_or_generate(messages, simulate_llm, model_id="sim")
        t7 = time.perf_counter()
        print(f"Response: {r4}")
        print(f"Time: {t7 - t6:.3f}s")

        snap = manager.metrics.snapshot()
        print(f"\nMetrics — hits: {snap['hits']}, misses: {snap['misses']}, sets: {snap['sets']}")


if __name__ == "__main__":
    main()
