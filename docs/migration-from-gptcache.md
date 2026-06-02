# Migrating from GPTCache

GPTCache (last updated 2024) is effectively unmaintained. omnicache-ai is the modern replacement — more backends, more adapters, actively maintained.

This guide covers the most common GPTCache patterns and their omnicache-ai equivalents.

---

## Installation

```bash
# Remove GPTCache
pip uninstall gptcache

# Install omnicache-ai
pip install omnicache-ai
```

---

## Basic LLM caching

**GPTCache:**
```python
from gptcache import cache
from gptcache.adapter import openai

cache.init()
openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}],
)
```

**omnicache-ai:**
```python
import openai
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

client = openai.OpenAI()
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
adapter = OpenAICacheAdapter(client, manager)

adapter.chat_create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

---

## Semantic / embedding-based caching

**GPTCache:**
```python
from gptcache import cache
from gptcache.embedding import Onnx
from gptcache.manager import CacheBase, VectorBase, get_data_manager
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation

onnx = Onnx()
cache.init(
    embedding_func=onnx.to_embeddings,
    data_manager=get_data_manager(CacheBase("sqlite"), VectorBase("faiss", dimension=onnx.dimension)),
    similarity_evaluation=SearchDistanceEvaluation(),
)
```

**omnicache-ai:**
```python
from omnicache_ai import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend
from omnicache_ai.layers.semantic_cache import SemanticCache

def my_embed(text: str) -> np.ndarray:
    # your embedding function (OpenAI, sentence-transformers, etc.)
    ...

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=my_embed,
    threshold=0.95,
)

# Store
cache.set("What is the capital of France?", "Paris")

# Retrieve (exact or semantic match)
result = cache.get("What's France's capital?")  # returns "Paris"
```

For self-tuning threshold (omnicache-ai exclusive):
```python
from omnicache_ai.layers.adaptive_semantic_cache import AdaptiveSemanticCache

cache = AdaptiveSemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=my_embed,
    target_hit_rate=0.35,      # auto-tune to 35% hit rate
    adjustment_interval=100,   # recalibrate every 100 lookups
)
```

---

## LangChain integration

**GPTCache:**
```python
from gptcache.adapter.langchain_models import LangChainLLMs
from langchain.llms import OpenAI

cached_llm = LangChainLLMs(llm=OpenAI())
```

**omnicache-ai:**
```python
from langchain_openai import ChatOpenAI
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter
import langchain

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
langchain.llm_cache = LangChainCacheAdapter(manager)

llm = ChatOpenAI(model="gpt-4o")
# All calls through llm now cached automatically
```

---

## Persistent cache (disk)

**GPTCache:**
```python
from gptcache.manager import CacheBase, VectorBase, get_data_manager

data_manager = get_data_manager(
    CacheBase("sqlite", sql_url="sqlite:///cache.db"),
    VectorBase("faiss", dimension=1536),
)
```

**omnicache-ai:**
```python
from omnicache_ai import CacheManager, CacheKeyBuilder
from omnicache_ai.backends.disk_backend import DiskBackend

manager = CacheManager(
    backend=DiskBackend("/path/to/cache"),
    key_builder=CacheKeyBuilder(),
)
```

---

## Redis (shared / multi-process)

GPTCache had limited Redis support. omnicache-ai provides full Redis backend:

```python
from omnicache_ai import CacheManager, CacheKeyBuilder
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(),
)
```

---

## Feature comparison

| Feature | GPTCache | omnicache-ai |
|---|---|---|
| OpenAI adapter | ✅ | ✅ |
| Anthropic adapter | ❌ | ✅ |
| LangChain adapter | ✅ | ✅ |
| LangGraph adapter | ❌ | ✅ |
| AutoGen adapter | ❌ | ✅ |
| CrewAI adapter | ❌ | ✅ |
| FAISS backend | ✅ | ✅ |
| Qdrant backend | ❌ | ✅ |
| Weaviate backend | ❌ | ✅ |
| Redis backend | partial | ✅ |
| Streaming cache | ❌ | ✅ |
| Adaptive threshold | ❌ | ✅ |
| Stampede protection | ❌ | ✅ |
| Async support | ❌ | ✅ |
| Prometheus metrics | ❌ | ✅ |
| OpenTelemetry | ❌ | ✅ |
| Active maintenance | ❌ dead | ✅ |

---

## Getting help

- [GitHub Issues](https://github.com/ashishpatel26/omnicache-ai/issues)
- [Documentation](https://ashishpatel26.github.io/omnicache-ai/)
- [Quick Start](../getting-started/quickstart.md)
