---
title: "OpenAIAgentsCacheAdapter"
---

# OpenAIAgentsCacheAdapter

Cache wrapper for the OpenAI Agents SDK. Intercepts `Runner.run()` and `Runner.run_async()` and returns cached results for identical agent + input combinations.

## Installation

```bash
pip install openai-agents
```

---

## Usage

```python
from agents import Agent, Runner
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant",
    model="gpt-4o",
)

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = OpenAIAgentsCacheAdapter(manager)

# Sync — wraps Runner.run_sync()
result = adapter.run(agent, "What is the capital of France?")

# Async — wraps Runner.run()
result = await adapter.arun(agent, "What is the capital of France?")
print(result.final_output)
```

### With Disk Backend (persistent across restarts)

```python
from omnicache_ai import DiskBackend

manager = CacheManager(
    backend=DiskBackend(directory="/var/cache/agents"),
    key_builder=CacheKeyBuilder(namespace="prod"),
)
adapter = OpenAIAgentsCacheAdapter(manager)
```

### Invalidate by agent

```python
adapter.invalidate_agent(agent)  # clears all cached results for this agent
```

---

## How It Works

Cache key = `hash(agent.name + agent.model + input_text + kwargs)`. The full `RunResult` object is serialised with pickle and replayed on cache hit.

Prompt caching is automatic in the OpenAI Agents SDK for repeated system prompts — `OpenAIAgentsCacheAdapter` adds an **application-level** cache on top, eliminating entire agent runs for known inputs.

---

## API Reference

| Method | Description |
|---|---|
| `run(agent, input_text, **kwargs)` | Cached sync `Runner.run_sync()` |
| `arun(agent, input_text, **kwargs)` | Cached async `Runner.run()` |
| `invalidate_agent(agent)` | Invalidate all cached results for an agent |
