---
title: "StreamingResponseCache"
---

# StreamingResponseCache

Cache layer for streaming LLM responses. Buffers chunks from a live stream, stores the complete result, and replays chunks from cache on subsequent identical requests — giving callers a consistent streaming interface regardless of cache state.

## Overview

Standard `ResponseCache` can only cache complete (non-streaming) responses. When your LLM call uses `stream=True`, each chunk arrives as a generator — there's nothing to cache until the stream ends.

`StreamingResponseCache` solves this:

- **Cache miss**: forwards chunks to the caller in real time while buffering them. After the stream ends, the full result is stored.
- **Cache hit**: replays stored chunks as a generator — callers get the same streaming interface.

---

## Usage

### Sync

```python
import openai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.layers.streaming_cache import StreamingResponseCache

client = openai.OpenAI()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
stream_cache = StreamingResponseCache(manager)

def stream_fn(messages):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True,
    )

messages = [{"role": "user", "content": "Explain caching in 3 sentences"}]

# First call — live stream, buffered and cached
for chunk in stream_cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)

print()

# Second call — replayed from cache at full speed
for chunk in stream_cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Async

```python
async def async_stream_fn(messages):
    async for chunk in await client.chat.completions.create(..., stream=True):
        yield chunk

async for chunk in stream_cache.aget_or_stream(messages, async_stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Custom chunk joiner

By default, chunks are stored as a list. Provide `chunk_joiner` to merge them into a single value before storage:

```python
stream_cache = StreamingResponseCache(
    manager,
    chunk_joiner=lambda chunks: "".join(
        c.choices[0].delta.content or "" for c in chunks
    ),
)
```

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `manager` | `CacheManager` | *(required)* | Cache manager instance |
| `serializer` | `Serializer \| None` | `PickleSerializer` | Serializer for stored chunks |
| `chunk_joiner` | `Callable \| None` | `None` | Merge chunks before storage; `None` = store as list |

| Method | Description |
|---|---|
| `get_or_stream(messages, stream_fn, model_id, params, ttl, tags)` | Sync generator |
| `aget_or_stream(messages, stream_fn, model_id, params, ttl, tags)` | Async generator |
