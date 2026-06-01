---
title: "Semantic Cache"
---

# Semantic Cache

Return cached answers for semantically similar queries -- not just exact string matches.
Uses a vector index (FAISS or ChromaDB) to find near-duplicate questions.

```bash
pip install 'omnicache-ai[vector-faiss]'
```

---

## 8.1 Standalone semantic cache

Build a semantic cache with your own embedding function and a cosine-similarity threshold.

```python
import numpy as np
from omnicache_ai import SemanticCache
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend

# Provide your own embed function (wraps any embedder)
from langchain_openai import OpenAIEmbeddings
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

def embed(text: str) -> np.ndarray:
    return np.array(embedder.embed_query(text), dtype=np.float32)

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=embed,
    threshold=0.93,   # cosine similarity cutoff
)

# Populate
cache.set("What is the capital of France?", "Paris")
cache.set("Who wrote Hamlet?", "William Shakespeare")

# Exact match
print(cache.get("What is the capital of France?"))   # "Paris"

# Semantically similar — still hits
print(cache.get("What's France's capital city?"))     # "Paris"
print(cache.get("Which city is the capital of France?"))  # "Paris"

# Unrelated — cache miss
print(cache.get("What is the speed of light?"))       # None
```

:::tip
Tune the `threshold` parameter to balance between cache hit rate and answer relevance.
A value of 0.93 works well for paraphrase detection; lower it to 0.88-0.90 for broader matching.
:::


---

## 8.2 Semantic cache inside a LangChain chain

Use the semantic cache as a front-end for a LangChain LLM call so that
rephrased questions hit the cache instead of the model.

```python
import numpy as np
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from omnicache_ai import SemanticCache
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend

embedder = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini")

sem_cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=lambda t: np.array(embedder.embed_query(t), dtype=np.float32),
    threshold=0.95,
)

def cached_ask(question: str) -> str:
    cached = sem_cache.get(question)
    if cached is not None:
        print("[CACHE HIT]")
        return cached
    answer = llm.invoke(question).content
    sem_cache.set(question, answer)
    return answer

print(cached_ask("What is RAG?"))
print(cached_ask("Can you explain RAG?"))          # hit
print(cached_ask("Describe retrieval augmented generation."))  # hit
```

---

## 8.3 Semantic cache with ChromaDB backend

Swap FAISS for ChromaDB for a persistent, production-ready vector store.

```python
# pip install 'omnicache-ai[vector-chroma]'
import numpy as np
from omnicache_ai import SemanticCache
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import ChromaBackend

cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=ChromaBackend(collection_name="qa_cache", dim=1536),
    embed_fn=lambda t: np.random.rand(1536).astype(np.float32),  # replace with real embedder
    threshold=0.92,
)
cache.set("Explain transformers", "Transformers are a type of neural network...")
print(cache.get("What are transformers?"))
```

:::note
Replace the random embedding function with a real embedder (e.g., OpenAI, Sentence Transformers)
for meaningful semantic matching.
:::
