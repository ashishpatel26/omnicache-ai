---
title: "LlamaIndex Adapters"
---

# LlamaIndex Adapters

Two adapters for LlamaIndex: one for LLM calls and one for QueryEngine (RAG) queries.

## Installation

```bash
pip install 'omnicache-ai[llamaindex]'
```

---

## LlamaIndexLLMCacheAdapter

Drop-in replacement for any LlamaIndex LLM. Caches `complete()`, `chat()`, and their async variants.

```python
from llama_index.llms.openai import OpenAI
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

llm = OpenAI(model="gpt-4o")
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
cached_llm = LlamaIndexLLMCacheAdapter(llm, manager)

# Use anywhere a LlamaIndex LLM is accepted
response = cached_llm.complete("What is retrieval-augmented generation?")
response = cached_llm.complete("What is retrieval-augmented generation?")  # cache hit

# Async
response = await cached_llm.acomplete("Explain vector embeddings")

# Chat
from llama_index.core.llms import ChatMessage
messages = [ChatMessage(role="user", content="What is RAG?")]
response = cached_llm.chat(messages)
```

### With Settings

```python
from llama_index.core import Settings

Settings.llm = cached_llm  # all LlamaIndex components use the cached LLM
```

---

## LlamaIndexQueryCacheAdapter

Caches `QueryEngine.query()` results — ideal for RAG pipelines where the same questions recur.

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

documents = SimpleDirectoryReader("data/").load_data()
index = VectorStoreIndex.from_documents(documents)
engine = index.as_query_engine()

cached_engine = LlamaIndexQueryCacheAdapter(engine, manager)

response = cached_engine.query("What are the key findings?")
response = cached_engine.query("What are the key findings?")  # cache hit — no retrieval, no LLM call

# Async
response = await cached_engine.aquery("Summarise section 3")
```

---

## API Reference

### LlamaIndexLLMCacheAdapter

| Method | Description |
|---|---|
| `complete(prompt, **kwargs)` | Cached completion |
| `acomplete(prompt, **kwargs)` | Async cached completion |
| `chat(messages, **kwargs)` | Cached chat |
| `achat(messages, **kwargs)` | Async cached chat |
| `stream_complete(...)` | Passthrough (not cached) |
| `stream_chat(...)` | Passthrough (not cached) |

### LlamaIndexQueryCacheAdapter

| Method | Description |
|---|---|
| `query(query_str, **kwargs)` | Cached query |
| `aquery(query_str, **kwargs)` | Async cached query |
