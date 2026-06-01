---
title: "OpenAI Agents SDK"
---

# OpenAI Agents SDK + OmniCache-AI

Cache OpenAI Agents SDK `Runner.run()` results for repeated agent inputs.

## Install

```bash
pip install openai-agents
```

## Example

```python
import asyncio, time
from agents import Agent
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)

agent = Agent(
    name="assistant",
    instructions="You are a concise technical assistant.",
    model="gpt-4o-mini",
)
adapter = OpenAIAgentsCacheAdapter(manager)

QUESTION = "What are the top 3 benefits of semantic caching?"

async def main():
    t0 = time.perf_counter()
    r1 = await adapter.arun(agent, QUESTION)
    t1 = time.perf_counter()
    print(r1.final_output)
    print(f"First:  {t1-t0:.3f}s")

    t2 = time.perf_counter()
    r2 = await adapter.arun(agent, QUESTION)
    t3 = time.perf_counter()
    print(f"Second: {t3-t2:.3f}s (cache hit)")

asyncio.run(main())
```

## Run the cookbook example

```bash
uv run python -m cookbook.openai_agents.agent
```
