"""OpenAI Agents SDK with omnicache-ai response caching.

Demonstrates: OpenAIAgentsCacheAdapter wrapping Runner calls.
Second run returns instantly from cache.

Run:
    uv run python -m cookbook.openai_agents.agent

Requires:
    pip install openai-agents
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend
from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

QUESTION = "What are the top 3 benefits of using a semantic cache in an LLM application?"


async def main() -> None:
    try:
        from agents import Agent
    except ImportError:
        print("openai-agents not installed. Run: pip install openai-agents")
        return

    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="cookbook-openai-agents"),
    )

    agent = Agent(
        name="assistant",
        instructions="You are a concise technical assistant. Answer in 3 bullet points.",
        model="gpt-4o-mini",
    )
    adapter = OpenAIAgentsCacheAdapter(manager)

    print("=== First Run (live agent call) ===")
    t0 = time.perf_counter()
    result1 = await adapter.arun(agent, QUESTION)
    t1 = time.perf_counter()
    print(result1.final_output)
    print(f"Time: {t1 - t0:.3f}s")

    print("\n=== Second Run (cache hit) ===")
    t2 = time.perf_counter()
    result2 = await adapter.arun(agent, QUESTION)
    t3 = time.perf_counter()
    print(result2.final_output)
    print(f"Time: {t3 - t2:.3f}s")
    print(f"\nSpeedup: {(t1 - t0) / max(t3 - t2, 0.001):.1f}x faster")

    snap = manager.metrics.snapshot()
    print(
        f"\nCache — hits: {snap['hits']}, misses: {snap['misses']}, hit_rate: {snap['hit_rate']:.0%}"
    )


if __name__ == "__main__":
    asyncio.run(main())
