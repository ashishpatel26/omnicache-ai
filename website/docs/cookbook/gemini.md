---
title: "Google Gemini"
---

# Google Gemini + OmniCache-AI

Cache `model.generate_content` calls — identical prompts return instantly without hitting the API.

## Install

```bash
pip install 'omnicache-ai[gemini]'
```

## Example

```python
import time
import google.generativeai as genai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel("gemini-2.0-flash")

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
adapter = GeminiCacheAdapter(model, manager)

prompt = "What is semantic caching and why does it matter?"

t0 = time.perf_counter()
r1 = adapter.generate_content(prompt)
t1 = time.perf_counter()
print(r1.text)
print(f"First call:  {t1 - t0:.3f}s")  # live API call

t0 = time.perf_counter()
r2 = adapter.generate_content(prompt)
t1 = time.perf_counter()
print(f"Second call: {t1 - t0:.6f}s")  # <1ms cache hit
```

## Async Example

```python
import asyncio
import google.generativeai as genai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel("gemini-2.0-flash")

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
adapter = GeminiCacheAdapter(model, manager)

async def main():
    prompt = "Explain transformers in one sentence."
    r1 = await adapter.agenerate_content(prompt)
    r2 = await adapter.agenerate_content(prompt)
    assert r1.text == r2.text  # same cached result

asyncio.run(main())
```

## Multi-Turn Conversation

```python
contents = [
    {"role": "user", "parts": ["My name is Alice."]},
    {"role": "model", "parts": ["Hello Alice! How can I help?"]},
    {"role": "user", "parts": ["What is my name?"]},
]
response = adapter.generate_content(contents)
print(response.text)  # "Your name is Alice." — served from cache on second call
```
