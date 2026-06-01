---
title: "LlamaIndex"
---

# LlamaIndex + OmniCache-AI

Two adapters — one for LLM calls, one for QueryEngine (RAG) queries.

## Install

```bash
pip install 'omnicache-ai[llamaindex]'
```

---

## LLM Cache

Drop `LlamaIndexLLMCacheAdapter` in anywhere a LlamaIndex LLM is accepted:

```python
import time
from llama_index.llms.openai import OpenAI
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

llm = OpenAI(model="gpt-4o-mini")
manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)
cached_llm = LlamaIndexLLMCacheAdapter(llm, manager)

prompt = "What is retrieval-augmented generation?"

t0 = time.perf_counter()
r1 = cached_llm.complete(prompt)
t1 = time.perf_counter()
print(r1.text)
print(f"First:  {t1-t0:.3f}s")

t2 = time.perf_counter()
r2 = cached_llm.complete(prompt)
t3 = time.perf_counter()
print(f"Second: {t3-t2:.3f}s (cache hit)")
```

### Use as global LlamaIndex LLM

```python
from llama_index.core import Settings

Settings.llm = cached_llm  # all LlamaIndex components use cached LLM
```

---

## QueryEngine Cache (RAG)

Cache entire `QueryEngine.query()` results — no retrieval, no LLM call on repeated queries:

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

documents = SimpleDirectoryReader("data/").load_data()
index = VectorStoreIndex.from_documents(documents)
engine = index.as_query_engine()

cached_engine = LlamaIndexQueryCacheAdapter(engine, manager)

query = "What are the key findings in the report?"

r1 = cached_engine.query(query)   # retrieves + calls LLM
r2 = cached_engine.query(query)   # instant from cache

# Async
r3 = await cached_engine.aquery(query)
```

---

## Async LLM

```python
r = await cached_llm.acomplete("Explain vector embeddings")
r = await cached_llm.achat(messages)
```

## Run the cookbook

```bash
uv run python -m cookbook.llamaindex.agent
```
