---
title: "Streaming Cache"
---

# Streaming Response Cache + OmniCache-AI

Cache streaming LLM responses — buffer chunks on first call, replay from cache instantly on subsequent identical requests.

## Install

```bash
pip install omnicache-ai openai
```

## Example

```python
import openai, time
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.layers.streaming_cache import StreamingResponseCache

client = openai.OpenAI()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
stream_cache = StreamingResponseCache(manager)

messages = [{"role": "user", "content": "Explain caching in 3 sentences"}]

def stream_fn(messages):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    )

print("=== First call (live stream, buffered) ===")
t0 = time.perf_counter()
for chunk in stream_cache.get_or_stream(messages, stream_fn, model_id="gpt-4o-mini"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
print(f"\nTime: {time.perf_counter()-t0:.3f}s")

print("\n=== Second call (cache hit, replayed) ===")
t0 = time.perf_counter()
for chunk in stream_cache.get_or_stream(messages, stream_fn, model_id="gpt-4o-mini"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
print(f"\nTime: {time.perf_counter()-t0:.3f}s")
```

## Async streaming

```python
import asyncio

client = openai.AsyncOpenAI()

async def async_stream_fn(messages):
    async for chunk in await client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, stream=True
    ):
        yield chunk

async def main():
    async for chunk in stream_cache.aget_or_stream(
        messages, async_stream_fn, model_id="gpt-4o-mini"
    ):
        print(chunk.choices[0].delta.content or "", end="", flush=True)

asyncio.run(main())
```

## Custom chunk joiner

Store a single string instead of a list of chunks:

```python
stream_cache = StreamingResponseCache(
    manager,
    chunk_joiner=lambda chunks: "".join(
        c.choices[0].delta.content or "" for c in chunks
    ),
)
```
