---
title: "ClaudeAgentCacheAdapter"
---

# ClaudeAgentCacheAdapter

Cache wrapper for the Claude Agent SDK (`claude_code_sdk`). Caches `query()` async generator results — eliminating redundant agent runs for identical prompts.

## Installation

```bash
pip install claude-code-sdk
```

---

## Usage

```python
import claude_code_sdk
from claude_code_sdk import ClaudeCodeOptions

from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = ClaudeAgentCacheAdapter(manager)

options = ClaudeCodeOptions(max_turns=5)

# First run — live agent call, result buffered and cached
messages = []
async for msg in adapter.query("Fix the import error in utils.py", options=options):
    messages.append(msg)
    print(msg)

# Second run — identical prompt, replayed from cache instantly
async for msg in adapter.query("Fix the import error in utils.py", options=options):
    print(msg)  # same messages, no agent call
```

### Invalidate all cached runs

```python
adapter.invalidate_all()
```

---

## How It Works

`ClaudeAgentCacheAdapter.query()` is an async generator that:

1. Checks the cache for the prompt + options key.
2. **Cache hit**: replays stored messages one by one — caller gets the same async generator interface.
3. **Cache miss**: streams the live agent, collects all messages, stores them, and yields each chunk in real time.

This means callers always get a streaming interface regardless of cache state.

---

## API Reference

| Method | Description |
|---|---|
| `query(prompt, options, **kwargs)` | Cached async generator wrapping `claude_code_sdk.query()` |
| `invalidate_all()` | Invalidate all cached Claude agent responses |
