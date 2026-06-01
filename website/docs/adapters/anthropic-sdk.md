---
title: "AnthropicCacheAdapter"
---

# AnthropicCacheAdapter

Wraps `anthropic.Anthropic` and `anthropic.AsyncAnthropic` `messages.create` calls with response caching. Returns cached results for identical `(model, messages, system, params)` combinations.

## Installation

```bash
pip install 'omnicache-ai[anthropic]'
```

---

## Usage

### Sync

```python
import anthropic
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

client = anthropic.Anthropic()
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = AnthropicCacheAdapter(client, manager)

response = adapter.messages_create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain vector embeddings"}],
)

# Second call — cache hit, no API cost
response = adapter.messages_create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain vector embeddings"}],
)
```

### Async

```python
client = anthropic.AsyncAnthropic()
adapter = AnthropicCacheAdapter(client, manager)

response = await adapter.amessages_create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain vector embeddings"}],
)
```

### With system prompt

```python
response = adapter.messages_create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a concise technical writer.",
    messages=[{"role": "user", "content": "What is RAG?"}],
)
```

:::tip[Combine with PromptCacheLayer]
For long system prompts, use `PromptCacheLayer` alongside `AnthropicCacheAdapter`:
- `AnthropicCacheAdapter` caches the full response (eliminates entire API calls)
- `PromptCacheLayer` injects `cache_control` on system prompts (saves tokens within live calls)
:::

### Invalidate by model

```python
adapter.invalidate_model("claude-sonnet-4-6")
```

---

## API Reference

| Method | Description |
|---|---|
| `messages_create(**kwargs)` | Cached `client.messages.create()` (sync) |
| `amessages_create(**kwargs)` | Cached `client.messages.create()` (async) |
| `invalidate_model(model)` | Invalidate all cached responses for a model |
