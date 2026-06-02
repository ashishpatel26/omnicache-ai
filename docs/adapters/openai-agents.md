# OpenAIAgentsCacheAdapter

Cache OpenAI Agents SDK `Runner.run` results so identical agent inputs return instantly.

## Overview

`OpenAIAgentsCacheAdapter` wraps the OpenAI Agents SDK `Runner` and intercepts `Runner.run_sync` (sync) and `Runner.run` (async). The cache key is built from the agent name, model, and input text — so different agents and different inputs remain independent.

**When to use:**

- OpenAI Agents pipelines that process the same inputs across multiple runs
- Cost reduction on long-running `gpt-4o`-backed agent workflows
- Evaluation harnesses where agents are tested on fixed datasets

---

## Installation

```bash
pip install openai-agents
pip install omnicache-ai
```

---

## Usage

### Basic caching

```python
from agents import Agent, Runner
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

agent = Agent(name="assistant", instructions="You are a helpful assistant.")
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
adapter = OpenAIAgentsCacheAdapter(manager)

result = adapter.run(agent, "What is the capital of France?")
```

### Async usage

```python
result = await adapter.arun(agent, "What is the capital of France?")
```

### Agent invalidation

```python
from omnicache_ai.core.invalidation import InvalidationEngine

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)
adapter = OpenAIAgentsCacheAdapter(manager)
adapter.invalidate_agent(agent)  # flush all entries for this agent
```

!!! note "None results not cached"
    If `Runner.run_sync` returns `None`, the result is not stored.

---

## API Reference

### OpenAIAgentsCacheAdapter

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `manager` | `CacheManager` | *(required)* | Cache manager |

**Methods:**

| Method | Signature | Description |
|---|---|---|
| `run` | `(agent: Agent, input_text: str, **kwargs) -> RunResult` | Cached `Runner.run_sync` |
| `arun` | `(agent: Agent, input_text: str, **kwargs) -> RunResult` | Async `Runner.run` |
| `invalidate_agent` | `(agent: Agent) -> int` | Flush all cached entries for an agent |

---

## Source

:material-file-code: `omnicache_ai/adapters/openai_agents_adapter.py`
