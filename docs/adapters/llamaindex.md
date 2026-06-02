# LlamaIndex Adapters

Cache LlamaIndex LLM calls and query engine responses so identical queries never re-run.

## Overview

omnicache-ai provides two LlamaIndex adapters:

- **`LlamaIndexLLMCacheAdapter`** — drop-in replacement for any LlamaIndex `LLM`. Caches `complete`, `chat`, `acomplete`, `achat`. Streaming methods bypass the cache.
- **`LlamaIndexQueryCacheAdapter`** — wraps a `QueryEngine`. Caches `query` and `aquery` by query string.

**When to use:**

- RAG pipelines that issue the same queries repeatedly across different sessions
- LlamaIndex evaluation harnesses where the same LLM prompt is tested multiple times
- Reducing API costs in iterative document analysis workflows

---

## Installation

```bash
pip install 'omnicache-ai[llamaindex]'
```

---

## Usage

### LLM adapter

```python
from llama_index.llms.openai import OpenAI
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

llm = OpenAI(model="gpt-4o")
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cached_llm = LlamaIndexLLMCacheAdapter(llm, manager)

# Use cached_llm anywhere a LlamaIndex LLM is accepted
response = cached_llm.complete("What is the capital of France?")
```

### Async LLM usage

```python
response = await cached_llm.acomplete("What is the capital of France?")
chat_response = await cached_llm.achat(messages)
```

### Query engine adapter

```python
from llama_index.core import VectorStoreIndex
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

index = VectorStoreIndex.from_documents(docs)
engine = index.as_query_engine()
cached_engine = LlamaIndexQueryCacheAdapter(engine, manager)

response = cached_engine.query("What does the contract say about termination?")
```

### Async query engine

```python
response = await cached_engine.aquery("What does the contract say about termination?")
```

!!! note "Streaming bypasses cache"
    `stream_complete` and `stream_chat` always call through to the underlying LLM — streaming responses are not cached by `LlamaIndexLLMCacheAdapter`. Use [`StreamingResponseCache`](../layers/streaming-response.md) if you need streaming caching.

---

## API Reference

### LlamaIndexLLMCacheAdapter

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `llm` | `llama_index.core.llms.LLM` | *(required)* | Any LlamaIndex LLM instance |
| `manager` | `CacheManager` | *(required)* | Cache manager |

**Methods:**

| Method | Signature | Description |
|---|---|---|
| `complete` | `(prompt: str, **kwargs) -> CompletionResponse` | Cached completion |
| `acomplete` | `(prompt: str, **kwargs) -> CompletionResponse` | Async cached completion |
| `chat` | `(messages: list, **kwargs) -> ChatResponse` | Cached chat |
| `achat` | `(messages: list, **kwargs) -> ChatResponse` | Async cached chat |
| `stream_complete` | `(prompt: str, **kwargs) -> Generator` | Passthrough — not cached |
| `stream_chat` | `(messages: list, **kwargs) -> Generator` | Passthrough — not cached |

### LlamaIndexQueryCacheAdapter

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query_engine` | `BaseQueryEngine` | *(required)* | LlamaIndex query engine |
| `manager` | `CacheManager` | *(required)* | Cache manager |

**Methods:**

| Method | Signature | Description |
|---|---|---|
| `query` | `(query: str, **kwargs) -> Response` | Cached query |
| `aquery` | `(query: str, **kwargs) -> Response` | Async cached query |

---

## Source

:material-file-code: `omnicache_ai/adapters/llamaindex_adapter.py`
