"""Provider-level prompt caching with omnicache-ai PromptCacheLayer.

Demonstrates:
- Auto-injection of Anthropic cache_control on long system prompts
- Tracking of provider_cache_hits and estimated_cost_saved_usd in CacheMetrics
- Combining PromptCacheLayer with ResponseCache for two-level savings

Run:
    uv run python -m cookbook.prompt_cache.agent

Requires:
    pip install anthropic
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend, ResponseCache
from omnicache_ai.layers.prompt_cache import PromptCacheLayer

# Long system prompt — will be auto-cached by Anthropic after first call
SYSTEM_PROMPT = (
    """
You are an expert Python architect with 15 years of experience building
distributed systems, async applications, and high-performance APIs.

Guidelines:
- Always provide type annotations
- Prefer composition over inheritance
- Write thread-safe code by default
- Use dataclasses for value objects
- Prefer immutable data structures
- Always handle edge cases explicitly
- Write self-documenting code with clear variable names
- Include error handling for all external calls
"""
    * 8
)  # repeat to ensure > 1024 chars for caching threshold

QUESTIONS = [
    "How should I design a thread-safe LRU cache in Python?",
    "What's the best pattern for async retry with exponential backoff?",
]


def main() -> None:
    try:
        import anthropic
    except ImportError:
        print("anthropic not installed. Run: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable")
        return

    client = anthropic.Anthropic(api_key=api_key)
    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="cookbook-prompt-cache"),
    )
    response_cache = ResponseCache(manager)
    layer = PromptCacheLayer(metrics=manager.metrics, min_chars_to_cache=512)

    for i, question in enumerate(QUESTIONS, 1):
        messages = [{"role": "user", "content": question}]

        # Check response cache first
        cached = response_cache.get(messages, model_id="claude-haiku-4-5")
        if cached:
            print(f"\n=== Q{i} (response cache hit) ===")
            print(cached.content[0].text[:200])
            continue

        print(f"\n=== Q{i} (live API call with prompt caching) ===")
        t0 = time.perf_counter()
        response = layer.anthropic_create(
            client,
            model="claude-haiku-4-5",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        t1 = time.perf_counter()
        print(response.content[0].text[:200])
        print(f"Time: {t1 - t0:.3f}s")

        response_cache.set(messages, response, model_id="claude-haiku-4-5", ttl=3600)

    snap = manager.metrics.snapshot()
    print("\n=== Metrics ===")
    print(f"Response cache hits:    {snap['hits']}")
    print(f"Provider cache hits:    {snap['provider_cache_hits']}")
    print(f"Tokens saved:           {snap['estimated_tokens_saved']:,}")
    print(f"Estimated cost saved:   ${snap['estimated_cost_saved_usd']:.4f}")


if __name__ == "__main__":
    main()
