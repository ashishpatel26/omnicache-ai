"""Google ADK agent with omnicache-ai response caching.

Demonstrates: GoogleADKCacheAdapter wrapping an ADK Agent.
Second run returns instantly from cache with no model call.

Run:
    uv run python -m cookbook.google_adk.agent

Requires:
    pip install 'omnicache-ai[google-adk]'
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend
from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

TASK = "Summarise the key benefits of semantic caching for LLM applications in 3 bullet points."


def main() -> None:
    try:
        from google.adk.agents import Agent
    except ImportError:
        print("google-adk not installed. Run: pip install google-adk")
        return

    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="cookbook-google-adk"),
    )

    agent = Agent(
        name="research_agent",
        model="gemini-2.0-flash",
        instruction="You are a concise technical writer. Answer in bullet points.",
    )
    cached = GoogleADKCacheAdapter(agent, manager)

    print("=== First Run (live agent call) ===")
    t0 = time.perf_counter()
    result1 = cached.run(TASK)
    t1 = time.perf_counter()
    print(result1)
    print(f"Time: {t1 - t0:.3f}s")

    print("\n=== Second Run (cache hit) ===")
    t2 = time.perf_counter()
    result2 = cached.run(TASK)
    t3 = time.perf_counter()
    print(result2)
    print(f"Time: {t3 - t2:.3f}s")
    print(f"\nSpeedup: {(t1 - t0) / max(t3 - t2, 0.001):.1f}x faster")

    snap = manager.metrics.snapshot()
    print(
        f"\nCache stats — hits: {snap['hits']}, misses: {snap['misses']}, hit_rate: {snap['hit_rate']:.0%}"
    )


if __name__ == "__main__":
    main()
