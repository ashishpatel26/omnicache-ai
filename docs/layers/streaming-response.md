# StreamingResponseCache

Cache streaming LLM responses and replay them as a generator — callers get a consistent interface regardless of cache state.

---

## Overview

`StreamingResponseCache` solves a hard problem: streaming responses are ephemeral (each chunk is yielded once and gone). This layer:

- **Cache miss** — transparently buffers chunks as they stream, yields each chunk live, then stores the full buffer
- **Cache hit** — replays the buffered chunks as a generator so the caller's `for chunk in ...` loop works identically

Key discriminators: `messages`, `model_id`, `params`.

**When to use:** Any LLM call that uses `stream=True` but where the same prompt is likely to be repeated.

!!! warning "Memory trade-off"
    Buffering a full stream requires holding all chunks in memory until the stream completes. For very long responses, consider setting a TTL to bound cache size growth.

---

## Usage

### Basic sync streaming

```python
import openai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.layers.streaming_cache import StreamingResponseCache

client = openai.OpenAI()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cache = StreamingResponseCache(manager)

messages = [{"role": "user", "content": "Tell me a story."}]

def stream_fn(msgs):
    return client.chat.completions.create(
        model="gpt-4o", messages=msgs, stream=True
    )

# First call — buffers live stream
for chunk in cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)

# Second call — replayed from cache
for chunk in cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Async streaming

```python
from omnicache_ai.layers.streaming_cache import StreamingResponseCache

async def async_stream_fn(msgs):
    async for chunk in await client.chat.completions.create(
        model="gpt-4o", messages=msgs, stream=True
    ):
        yield chunk

async for chunk in cache.aget_or_stream(messages, async_stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="")
```

### Custom chunk joiner

```python
# Store chunks joined into a single string instead of a list
cache = StreamingResponseCache(manager, chunk_joiner="".join)

# On cache hit, returns ["full concatenated response"] — a list with one item
```

### With TTL

```python
for chunk in cache.get_or_stream(
    messages, stream_fn, model_id="gpt-4o", ttl=3600
):
    ...
```

---

## How It Works

1. Build cache key from `messages`, `model_id`, and `params`
2. Check backend for stored chunks
3. **Hit** — deserialize stored list, yield each chunk
4. **Miss** — call `stream_fn(messages)`, yield each chunk live, buffer all, then store

```
messages + model_id + params
          |
          v
      _build_key()
          |
     cache.get(key)
     /           \
  hit             miss
   |               |
yield from      stream_fn(messages)
stored_chunks    → yield chunk live
                 → buffer chunks
                 → cache.set(key, chunks)
```

!!! tip "Consistent interface"
    Callers always iterate over a generator — they cannot tell whether chunks came from cache or a live stream.

---

## API Reference

### Constructor

| Parameter | Type | Default | Description |
|---|---|---|---|
| `manager` | `CacheManager` | *(required)* | Cache manager |
| `serializer` | `Serializer \| None` | `PickleSerializer` | Serializer for stored chunks |
| `chunk_joiner` | `Callable[[list], Any] \| None` | `None` | Optional callable to merge chunks before storing |

### Methods

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `get_or_stream` | `messages, stream_fn, model_id, params, ttl, tags` | `Generator` | Sync streaming with cache |
| `aget_or_stream` | `messages, stream_fn, model_id, params, ttl, tags` | `AsyncGenerator` | Async streaming with cache |

---

## Source

:material-file-code: `omnicache_ai/layers/streaming_cache.py`
