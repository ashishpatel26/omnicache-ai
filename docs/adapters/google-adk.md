# GoogleADKCacheAdapter

Cache Google Agent Development Kit agent responses so identical tasks return instantly.

## Overview

`GoogleADKCacheAdapter` wraps a Google ADK `Agent` and intercepts `agent.run()` and `agent.run_async()`. The cache key includes the agent name and the full task input.

**When to use:**

- ADK agents invoked with identical or templated tasks
- Long-running ADK pipelines that re-run the same tasks across iterations
- Cost reduction on Gemini-backed ADK agents

---

## Installation

```bash
pip install 'omnicache-ai[google-adk]'
```

---

## Usage

### Basic caching

```python
from google.adk.agents import Agent
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

agent = Agent(name="summariser", model="gemini-2.0-flash", instruction="...")
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cached = GoogleADKCacheAdapter(agent, manager)

result = cached.run("Summarise the quarterly report.")
```

### Async usage

```python
result = await cached.arun("Summarise the quarterly report.")
```

### Agent invalidation

```python
from omnicache_ai.core.invalidation import InvalidationEngine

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)
cached = GoogleADKCacheAdapter(agent, manager)
cached.invalidate_agent()  # flush all entries for this agent
```

!!! note "Transparent proxy"
    Any attribute not overridden (e.g. `agent.name`, `agent.tools`) is forwarded to the underlying ADK agent via `__getattr__`.

!!! warning "None results not cached"
    If `agent.run()` returns `None`, the result is not stored. This prevents caching empty/error responses.

---

## API Reference

### GoogleADKCacheAdapter

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `agent` | `google.adk.agents.Agent` | *(required)* | ADK agent instance |
| `manager` | `CacheManager` | *(required)* | Cache manager |

**Methods:**

| Method | Signature | Description |
|---|---|---|
| `run` | `(task: Any, **kwargs) -> Any` | Cached `agent.run` |
| `arun` | `(task: Any, **kwargs) -> Any` | Async — uses `agent.run_async` if available |
| `invalidate_agent` | `() -> int` | Flush all cached entries for this agent |

---

## Source

:material-file-code: `omnicache_ai/adapters/google_adk_adapter.py`
