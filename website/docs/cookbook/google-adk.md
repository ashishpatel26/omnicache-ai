---
title: "Google ADK"
---

# Google ADK + OmniCache-AI

Cache Google ADK agent runs — eliminating redundant agent orchestration and model calls for repeated tasks.

## Install

```bash
pip install 'omnicache-ai[google-adk]'
```

## Example

```python
import time
from google.adk.agents import Agent
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)

agent = Agent(
    name="research_agent",
    model="gemini-2.0-flash",
    instruction="You are a concise technical writer.",
)
cached = GoogleADKCacheAdapter(agent, manager)

TASK = "List 3 benefits of semantic caching for LLM applications"

t0 = time.perf_counter()
result1 = cached.run(TASK)
t1 = time.perf_counter()
print(f"First run:  {t1-t0:.3f}s")  # ~1.2s (live agent)

t2 = time.perf_counter()
result2 = cached.run(TASK)
t3 = time.perf_counter()
print(f"Second run: {t3-t2:.3f}s")  # ~0.0001s (cache hit)
print(f"Speedup:    {(t1-t0)/(t3-t2):.0f}x faster")
```

## Async

```python
result = await cached.arun(TASK)
```

## With Redis (share cache across workers)

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(namespace="prod"),
)
cached = GoogleADKCacheAdapter(agent, manager)
```

## Run the cookbook example

```bash
uv run python -m cookbook.google_adk.agent
```
