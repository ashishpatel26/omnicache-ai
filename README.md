<div align="center">
  <img src="assets/omnicache_logo.png" alt="OmniCache-AI Logo" width="280"/>

<h1>omnicache-ai</h1>

<p><strong>Unified multi-layer caching for AI Agent pipelines.</strong><br/>
  Drop it in front of any LLM call, embedding, retrieval query, or agent workflow<br/>
  to eliminate redundant API calls and cut latency and cost.</p>

[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyPI](https://img.shields.io/badge/PyPI-omnicache--ai-orange?logo=pypi&logoColor=white)](https://pypi.org/project/omnicache-ai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-1C3C3C?logo=langchain)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.4%2B-0078D4?logo=microsoft)](https://microsoft.github.io/autogen/)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.x-FF4B4B)](https://www.crewai.com/)
[![Agno](https://img.shields.io/badge/Agno-2.x-6366F1)](https://www.agno.com/)

</div>

---

## Table of Contents

- [Why omnicache-ai?](#why-omnicache-ai)
- [Key Features](#key-features)
- [AI Agent Pipeline Architecture](#ai-agent-pipeline-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Cache Layers](#cache-layers)
- [Middleware](#middleware-decorator-pattern)
- [Framework Adapters](#framework-adapters)
- [Backends](#backends)
- [Tag-Based Invalidation](#tag-based-invalidation)
- [Custom Backend](#custom-backend)
- [Project Structure](#project-structure)
- [Development](#development)

---

## Why omnicache-ai?

Every AI agent pipeline makes the same expensive calls repeatedly:

| Without caching                                 | With omnicache-ai                                 |
| ----------------------------------------------- | ------------------------------------------------- |
| Every LLM call billed at full token cost        | Identical prompts returned instantly, zero tokens |
| Embeddings re-computed on every request         | Vectors stored and reused across sessions         |
| Vector search re-run for same queries           | Retrieval results cached by query + top-k         |
| Agent state lost between runs                   | Session context persisted across turns            |
| Semantically identical questions treated as new | Cosine similarity match returns cached answer     |

---

## Key Features

### Cache Layers

| Layer             | Class                    | What it caches                                                       | Serialization  |
| ----------------- | ------------------------ | -------------------------------------------------------------------- | -------------- |
| LLM Response      | `ResponseCache`          | Model output keyed by model + messages + params                      | pluggable      |
| Embeddings        | `EmbeddingCache`         | `np.ndarray` vectors keyed by model + text                           | `np.tobytes()` |
| Retrieval         | `RetrievalCache`         | Document lists keyed by query + retriever + top-k                    | pluggable      |
| Context/Session   | `ContextCache`           | Conversation turns keyed by session ID + turn index                  | pluggable      |
| Semantic          | `SemanticCache`          | Answers reused for semantically similar queries (cosine ≥ threshold) | pluggable      |
| Adaptive Semantic | `AdaptiveSemanticCache`  | SemanticCache + auto-tuning threshold + multi-turn guard             | pluggable      |
| Streaming         | `StreamingResponseCache` | Buffers streamed LLM chunks; replays from cache as generator         | pluggable      |
| Prompt Cache      | `PromptCacheLayer`       | Injects Anthropic `cache_control`; tracks provider cache savings     | —              |

### Storage Backends

| Backend              | Class                 | Extras              | Best For                             |
| -------------------- | --------------------- | ------------------- | ------------------------------------ |
| In-Memory (LRU)      | `InMemoryBackend`     | — (core)            | Dev, testing, single-process         |
| Async In-Memory      | `AsyncInMemoryBackend`| — (core)            | FastAPI, async frameworks            |
| Disk                 | `DiskBackend`         | — (core)            | Persistent, single-machine           |
| Redis                | `RedisBackend`        | `[redis]`           | Shared across processes / services   |
| Tiered (L1 + L2)     | `TieredBackend`       | — (core)            | Memory speed + Redis persistence     |
| FAISS                | `FAISSBackend`        | `[vector-faiss]`    | High-speed in-process vector search  |
| ChromaDB             | `ChromaBackend`       | `[vector-chroma]`   | Persistent vector store + metadata   |
| Qdrant               | `QdrantBackend`       | `[vector-qdrant]`   | Fastest production vector DB (22ms)  |
| Weaviate             | `WeaviateBackend`     | `[vector-weaviate]` | Native hybrid search (vector + BM25) |

### Framework Adapters

| Framework             | Class                        | Hook Point                                           | Async                             |
| --------------------- | ---------------------------- | ---------------------------------------------------- | --------------------------------- |
| OpenAI SDK            | `OpenAICacheAdapter`         | `client.chat.completions.create`                     | ✅`achat_create`                  |
| Anthropic SDK         | `AnthropicCacheAdapter`      | `client.messages.create`                             | ✅`amessages_create`              |
| Google ADK            | `GoogleADKCacheAdapter`      | `Agent.run()` / `run_async()`                        | ✅`arun`                          |
| OpenAI Agents SDK     | `OpenAIAgentsCacheAdapter`   | `Runner.run()` / `run_sync()`                        | ✅`arun`                          |
| LlamaIndex LLM        | `LlamaIndexLLMCacheAdapter`  | `complete()` / `chat()` / async variants             | ✅`acomplete` / `achat`           |
| LlamaIndex QueryEngine| `LlamaIndexQueryCacheAdapter`| `query()` / `aquery()`                               | ✅`aquery`                        |
| Claude Agent SDK      | `ClaudeAgentCacheAdapter`    | `claude_code_sdk.query()` async generator            | ✅ (async generator)              |
| LangChain ≥ 0.2       | `LangChainCacheAdapter`      | `BaseCache` — `lookup` / `update`                    | ✅`alookup` / `aupdate`           |
| LangGraph ≥ 0.1 / 1.x | `LangGraphCacheAdapter`      | `BaseCheckpointSaver` — `get_tuple` / `put` / `list` | ✅`aget_tuple` / `aput` / `alist` |
| AutoGen ≥ 0.4         | `AutoGenCacheAdapter`        | `AssistantAgent.run()` / `arun()`                    | ✅`arun`                          |
| AutoGen 0.2.x         | `AutoGenCacheAdapter`        | `ConversableAgent.generate_reply()`                  | —                                 |
| CrewAI ≥ 0.28         | `CrewAICacheAdapter`         | `Crew.kickoff()`                                     | ✅`kickoff_async`                 |
| Agno ≥ 0.1            | `AgnoCacheAdapter`           | `Agent.run()` / `arun()`                             | ✅`arun`                          |
| A2A ≥ 0.2             | `A2ACacheAdapter`            | `process()` / `wrap()` decorator                     | ✅`aprocess`                      |

### Middleware

| Class                 | Wraps                         | Async |
| --------------------- | ----------------------------- | ----- |
| `LLMMiddleware`       | Any sync LLM callable         | —     |
| `AsyncLLMMiddleware`  | Any async LLM callable        | ✅    |
| `EmbeddingMiddleware` | Any sync/async embed function | ✅    |
| `RetrieverMiddleware` | Any sync/async retriever      | ✅    |

### Core Engine

| Component        | Class                | Description                                                                    |
| ---------------- | -------------------- | ------------------------------------------------------------------------------ |
| Orchestrator     | `CacheManager`       | Central hub — wires backend, key builder, TTL policy, invalidation             |
| Key Builder      | `CacheKeyBuilder`    | `namespace:type:sha256[:16]` canonical keys                                    |
| Metrics          | `CacheMetrics`       | Hit/miss/eviction counters + provider cache hits + cost saved                  |
| Serializer       | `Serializer`         | Pluggable encode/decode — `PickleSerializer` (default), `JsonSerializer`       |
| Compressor       | `Compressor`         | Optional compression — `GzipCompressor`, `NoopCompressor` (default)           |
| Stampede Shield  | `StampedeShield`     | Per-key `threading.Lock` prevents concurrent duplicate LLM calls               |
| Request Config   | `RequestConfig`      | Per-request TTL / threshold / `skip_cache` overrides                           |
| Cache Warmer     | `CacheWarmer`        | Bulk pre-populate from query lists or CSV files                                |
| TTL Policy       | `TTLPolicy`          | Global + per-layer TTL overrides                                               |
| Eviction         | `EvictionPolicy`     | LRU / TTL-only strategies, wired into `InMemoryBackend`                        |
| Invalidation     | `InvalidationEngine` | Tag-based bulk eviction                                                        |
| Multi-Tenant     | `CacheManager.for_tenant(id)` | Scoped manager with per-tenant key namespacing, shared backend       |
| Settings         | `OmnicacheSettings`  | Dataclass + `from_env()` for 12-factor config                                  |
| Prometheus       | `PrometheusExporter` | `/metrics` HTTP endpoint — requires `[observability]`                          |
| OpenTelemetry    | `OpenTelemetryExporter` | Push metrics to OTEL collector — requires `[observability]`                 |

---

## AI Agent Pipeline Architecture

### Where Cache Layers Sit in a Full AI Pipeline

```mermaid
flowchart TD
    User(["👤 User / Application"])

    User -->|query| Adapters

    subgraph Adapters["🔌 Framework Adapters (13)"]
        direction LR
        OAI["OpenAI SDK"]
        ANT["Anthropic SDK"]
        GADK["Google ADK"]
        OAIA["OpenAI Agents SDK"]
        LLI["LlamaIndex"]
        CLA["Claude Agent SDK"]
        LC["LangChain"]
        LG["LangGraph"]
        AG["AutoGen"]
        CR["CrewAI"]
        AN["Agno"]
        A2["A2A"]
    end

    Adapters -->|intercepted call| MW

    subgraph MW["⚙️ Middleware"]
        direction LR
        LLM_MW["LLMMiddleware"]
        EMB_MW["EmbeddingMiddleware"]
        RET_MW["RetrieverMiddleware"]
    end

    MW -->|cache lookup| Layers

    subgraph Layers["🗂️ Cache Layers (omnicache-ai)"]
        direction TB
        ASC["AdaptiveSemanticCache\n(auto-tuning threshold)"]
        SC["SemanticCache\n(cosine similarity)"]
        RC["ResponseCache\n(LLM output, stampede-safe)"]
        SRC["StreamingResponseCache\n(buffered stream replay)"]
        EC["EmbeddingCache\n(np.ndarray)"]
        REC["RetrievalCache\n(documents)"]
        CC["ContextCache\n(session turns)"]
        PC["PromptCacheLayer\n(provider cache_control)"]
    end

    Layers -->|hit → return| User
    Layers -->|miss → forward| Core

    subgraph Core["🧠 Core Engine"]
        direction LR
        CM["CacheManager\n+ for_tenant()"]
        KB["CacheKeyBuilder\nnamespace:type:sha256"]
        MT["CacheMetrics\nhit_rate · cost_saved"]
        IE["InvalidationEngine\ntag-based eviction"]
        TP["TTLPolicy\nper-layer TTLs"]
        SS["StampedeShield\nper-key lock"]
        OBS["Observability\nPrometheus · OTEL"]
    end

    Core <-->|read / write| Backends

    subgraph Backends["💾 Storage Backends (9)"]
        direction LR
        MEM["InMemoryBackend\n(LRU)"]
        AMEM["AsyncInMemoryBackend\n(asyncio)"]
        TIER["TieredBackend\n(L1 + L2)"]
        DISK["DiskBackend\n(diskcache)"]
        REDIS["RedisBackend\n[redis]"]
        FAISS["FAISSBackend\n[vector-faiss]"]
        CHROMA["ChromaBackend\n[vector-chroma]"]
        QDRANT["QdrantBackend\n[vector-qdrant]"]
        WEAV["WeaviateBackend\n[vector-weaviate]"]
    end

    Core -->|miss| LLM_CALL

    subgraph LLM_CALL["🤖 Actual AI Work (on cache miss only)"]
        direction LR
        LLM["LLM API\ngpt-4o / claude / gemini"]
        EMB["Embedder\ntext-embedding-3"]
        VDB["Vector DB\npinecone / weaviate"]
        TOOLS["Tools / APIs"]
    end

    LLM_CALL -->|result| Core
    Core -->|store + return| User

    style Layers fill:#1e3a5f,color:#fff,stroke:#3b82f6
    style Backends fill:#1a3326,color:#fff,stroke:#22c55e
    style Adapters fill:#3b1f5e,color:#fff,stroke:#a855f7
    style MW fill:#3b2a0f,color:#fff,stroke:#f59e0b
    style Core fill:#1e2a3b,color:#fff,stroke:#64748b
    style LLM_CALL fill:#3b1a1a,color:#fff,stroke:#ef4444
```

---

### Cache Layer Responsibilities in the Pipeline

```mermaid
flowchart LR
    Q(["Query"])

    Q --> S0
    subgraph S0["① Adaptive Semantic Layer"]
        ASC["AdaptiveSemanticCache\nauto-tuning threshold\n+ multi-turn guard"]
    end

    S0 -->|miss| S1
    subgraph S1["② Semantic Layer"]
        SC["SemanticCache\ncosine similarity ≥ threshold\n→ skip everything below"]
    end

    S1 -->|miss| S2
    subgraph S2["③ Response Layer"]
        RC["ResponseCache\nexact model+msgs+params\nhash match · stampede-safe"]
    end

    S2 -->|miss| S2b
    subgraph S2b["④ Streaming Layer"]
        SRC["StreamingResponseCache\nbuffered stream replay\nfor streaming LLMs"]
    end

    S2b -->|miss| S3
    subgraph S3["⑤ Retrieval Layer"]
        REC["RetrievalCache\nquery + retriever + top-k\nhash match"]
    end

    S3 -->|miss| S4
    subgraph S4["⑥ Embedding Layer"]
        EC["EmbeddingCache\nmodel + text hash match\nreturns np.ndarray"]
    end

    S4 -->|miss| S5
    subgraph S5["⑦ Context Layer"]
        CC["ContextCache\nsession_id + turn_index\nreturns message history"]
    end

    S5 -->|all miss| API["🤖 LLM / API Call\n+ PromptCacheLayer\n(provider cache_control)"]

    API -->|result| Store["Store in all\nrelevant layers\n+ CacheMetrics update"]
    Store --> R(["Response"])

    S0 -->|hit ⚡| R
    S1 -->|hit ⚡| R
    S2 -->|hit ⚡| R
    S2b -->|hit ⚡| R
    S3 -->|hit ⚡| R
    S4 -->|hit ⚡| R
    S5 -->|hit ⚡| R

    style S0 fill:#1a3a2a,color:#fff,stroke:#10b981
    style S1 fill:#4c1d95,color:#fff,stroke:#7c3aed
    style S2 fill:#1e3a5f,color:#fff,stroke:#3b82f6
    style S2b fill:#1e2a4a,color:#fff,stroke:#60a5fa
    style S3 fill:#14532d,color:#fff,stroke:#22c55e
    style S4 fill:#713f12,color:#fff,stroke:#f59e0b
    style S5 fill:#7f1d1d,color:#fff,stroke:#ef4444
```

---

### Backend Selection by Use Case

```mermaid
flowchart TD
    Start(["Which backend?"])

    Start --> Q1{"Multiple processes\nor services?"}
    Q1 -->|Yes| Q1b{"Also need\nfast local reads?"}
    Q1b -->|Yes| TIERED["TieredBackend\nL1=InMemory + L2=Redis\n[core]"]
    Q1b -->|No| REDIS["RedisBackend\n[redis]"]

    Q1 -->|No| Q2{"Need vector\nsimilarity?"}

    Q2 -->|Yes| Q3{"Need hybrid\nsearch (vector+BM25)?"}
    Q3 -->|Yes| WEAV["WeaviateBackend\n[vector-weaviate]"]
    Q3 -->|No| Q3b{"Production scale\n(10M+ vectors)?"}
    Q3b -->|Yes| QDRANT["QdrantBackend\n22ms p95 · [vector-qdrant]"]
    Q3b -->|No| Q3c{"Persist\nto disk?"}
    Q3c -->|Yes| CHROMA["ChromaBackend\n[vector-chroma]"]
    Q3c -->|No| FAISS["FAISSBackend\n[vector-faiss]"]

    Q2 -->|No| Q4{"Async framework\n(FastAPI / LangGraph)?"}
    Q4 -->|Yes| AMEM["AsyncInMemoryBackend\n[core]"]
    Q4 -->|No| Q5{"Survive\nrestarts?"}
    Q5 -->|Yes| DISK["DiskBackend\n[core]"]
    Q5 -->|No| MEM["InMemoryBackend\n[core]"]

    style REDIS fill:#dc2626,color:#fff
    style TIERED fill:#b45309,color:#fff
    style FAISS fill:#2563eb,color:#fff
    style CHROMA fill:#7c3aed,color:#fff
    style QDRANT fill:#0e7490,color:#fff
    style WEAV fill:#0f766e,color:#fff
    style DISK fill:#d97706,color:#fff
    style MEM fill:#059669,color:#fff
    style AMEM fill:#047857,color:#fff
```

---

## Installation

### Requirements

- Python ≥ 3.12
- Core dependencies: `diskcache`, `numpy` (installed automatically)

### pip (PyPI)

```bash
# Minimal — in-memory + disk backends
pip install omnicache-ai

# ── Framework adapters ──────────────────────────────────────────────
pip install 'omnicache-ai[openai]'          # OpenAI SDK adapter
pip install 'omnicache-ai[anthropic]'       # Anthropic SDK adapter
pip install 'omnicache-ai[google-adk]'      # Google ADK adapter
pip install openai-agents                   # OpenAI Agents SDK adapter
pip install 'omnicache-ai[llamaindex]'      # LlamaIndex LLM + QueryEngine adapters
pip install claude-code-sdk                 # Claude Agent SDK adapter
pip install 'omnicache-ai[langchain]'       # LangChain ≥ 0.2
pip install 'omnicache-ai[langgraph]'       # LangGraph ≥ 0.1 / 1.x
pip install 'omnicache-ai[autogen]'         # AutoGen legacy (pyautogen 0.2.x)
pip install 'autogen-agentchat>=0.4'        # AutoGen new API (separate package)
pip install 'omnicache-ai[crewai]'          # CrewAI ≥ 0.28 / 1.x
pip install 'omnicache-ai[agno]'            # Agno ≥ 0.1 / 2.x
pip install 'a2a-sdk>=0.3' omnicache-ai     # A2A SDK ≥ 0.2

# ── Storage backends ────────────────────────────────────────────────
pip install 'omnicache-ai[redis]'           # Redis
pip install 'omnicache-ai[vector-faiss]'    # FAISS vector search
pip install 'omnicache-ai[vector-chroma]'   # ChromaDB vector store
pip install 'omnicache-ai[vector-qdrant]'   # Qdrant (22ms p95, fastest)
pip install 'omnicache-ai[vector-weaviate]' # Weaviate hybrid search

# ── Observability ────────────────────────────────────────────────────
pip install 'omnicache-ai[observability]'   # Prometheus + OpenTelemetry exporters

# ── Common combos ───────────────────────────────────────────────────
pip install 'omnicache-ai[langchain,redis]'
pip install 'omnicache-ai[langgraph,vector-qdrant]'

# ── Everything ──────────────────────────────────────────────────────
pip install 'omnicache-ai[all]'
```

### uv

```bash
uv add omnicache-ai
uv add 'omnicache-ai[langchain,redis]'
uv add 'omnicache-ai[all]'
```

### conda

```bash
conda install -c conda-forge omnicache-ai
```

### From source

```bash
git clone https://github.com/ashishpatel26/omnicache-ai.git
cd omnicache-ai
uv sync --dev         # installs all dev + core deps
uv run pytest         # verify install
```

### Verify

```bash
python -c "import omnicache_ai; print(omnicache_ai.__version__)"
# 0.2.0
```

### Environment variable configuration

| Variable                       | Default                    | Values                      |
| ------------------------------ | -------------------------- | --------------------------- |
| `OMNICACHE_BACKEND`            | `memory`                   | `memory` · `disk` · `redis` |
| `OMNICACHE_REDIS_URL`          | `redis://localhost:6379/0` | Any Redis URL               |
| `OMNICACHE_DISK_PATH`          | `/tmp/omnicache`           | Any writable path           |
| `OMNICACHE_DEFAULT_TTL`        | `3600`                     | Seconds;`0` = no expiry     |
| `OMNICACHE_NAMESPACE`          | `omnicache`                | Key prefix string           |
| `OMNICACHE_SEMANTIC_THRESHOLD` | `0.95`                     | Float 0–1                   |
| `OMNICACHE_TTL_EMBEDDING`      | `86400`                    | Per-layer override          |
| `OMNICACHE_TTL_RETRIEVAL`      | `3600`                     | Per-layer override          |
| `OMNICACHE_TTL_CONTEXT`        | `1800`                     | Per-layer override          |
| `OMNICACHE_TTL_RESPONSE`       | `600`                      | Per-layer override          |

```bash
export OMNICACHE_BACKEND=redis
export OMNICACHE_REDIS_URL=redis://localhost:6379/0
export OMNICACHE_DEFAULT_TTL=3600
```

```python
from omnicache_ai import CacheManager, OmnicacheSettings

manager = CacheManager.from_settings(OmnicacheSettings.from_env())
```

---

## Quick Start

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(namespace="myapp"),
)

manager.set("my_key", {"result": 42}, ttl=60)
value = manager.get("my_key")  # {"result": 42}
```

### LangChain in 3 lines

```python
from langchain_core.globals import set_llm_cache
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter

set_llm_cache(LangChainCacheAdapter(CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())))
# Every ChatOpenAI / ChatAnthropic call is now cached automatically
```

---

## Cache Layers

### LLM Response Cache

Cache the string or dict output of any LLM call, keyed by model + messages + params.

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder, ResponseCache

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder(namespace="myapp"))
cache = ResponseCache(manager)

messages = [{"role": "user", "content": "What is 2+2?"}]

cache.set(messages, "4", model_id="gpt-4o")
answer = cache.get(messages, model_id="gpt-4o")  # "4"

# get_or_generate — calls generator only on cache miss
def call_llm(msgs):
    return openai_client.chat.completions.create(...).choices[0].message.content

answer = cache.get_or_generate(messages, call_llm, model_id="gpt-4o")
```

### Embedding Cache

```python
from omnicache_ai import EmbeddingCache

emb_cache = EmbeddingCache(manager)

vec = emb_cache.get_or_compute(
    text="Hello world",
    compute_fn=lambda t: embed_model.encode(t),
    model_id="text-embedding-3-small",
)
```

### Retrieval Cache

```python
from omnicache_ai import RetrievalCache

ret_cache = RetrievalCache(manager)

docs = ret_cache.get_or_retrieve(
    query="What is RAG?",
    retrieve_fn=lambda q: vectorstore.similarity_search(q, k=5),
    retriever_id="my-vectorstore",
    top_k=5,
)
```

### Context / Session Cache

```python
from omnicache_ai import ContextCache

ctx_cache = ContextCache(manager)

ctx_cache.set(session_id="user-123", turn_index=0, messages=[...])
history = ctx_cache.get(session_id="user-123", turn_index=0)

ctx_cache.invalidate_session("user-123")  # clear all turns for this session
```

### Semantic Cache

Returns a cached answer for semantically similar queries (cosine ≥ threshold). Requires `pip install 'omnicache-ai[vector-faiss]'`.

```python
from omnicache_ai import SemanticCache
from omnicache_ai.backends.memory_backend import InMemoryBackend
from omnicache_ai.backends.vector_backend import FAISSBackend

sem_cache = SemanticCache(
    exact_backend=InMemoryBackend(),
    vector_backend=FAISSBackend(dim=1536),
    embed_fn=lambda text: embed_model.encode(text),  # returns np.ndarray
    threshold=0.95,
)

sem_cache.set("What is the capital of France?", "Paris")

sem_cache.get("What is the capital of France?")       # "Paris" — exact
sem_cache.get("Which city is the capital of France?") # "Paris" — semantic hit
```

---

## Middleware (Decorator Pattern)

Wrap any sync/async LLM callable without changing its signature.

```python
from omnicache_ai import LLMMiddleware, CacheKeyBuilder, ResponseCache

middleware = LLMMiddleware(response_cache, key_builder, model_id="gpt-4o")

@middleware
def call_llm(messages: list[dict]) -> str:
    return openai_client.chat.completions.create(...).choices[0].message.content

wrapped = middleware(call_llm)  # or wrap an existing callable
```

```python
from omnicache_ai import AsyncLLMMiddleware

@AsyncLLMMiddleware(response_cache, key_builder, model_id="gpt-4o")
async def call_llm_async(messages):
    return await async_client.chat(messages)
```

Same pattern: `EmbeddingMiddleware`, `RetrieverMiddleware`

---

## Framework Adapters

### LangChain

```python
from langchain_core.globals import set_llm_cache
from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter

set_llm_cache(LangChainCacheAdapter(manager))

llm = ChatOpenAI(model="gpt-4o")
response = llm.invoke("What is 2+2?")  # cached on second call
```

### LangGraph

Compatible with langgraph ≥ 0.1 and ≥ 1.0 — adapter auto-detects the API version.

```python
from omnicache_ai.adapters.langgraph_adapter import LangGraphCacheAdapter

saver = LangGraphCacheAdapter(manager)
graph = StateGraph(MyState).compile(checkpointer=saver)

result = graph.invoke({"messages": [...]}, config={"configurable": {"thread_id": "t1"}})
```

### AutoGen

```python
# autogen-agentchat 0.4+ (new API)
from autogen_agentchat.agents import AssistantAgent
from omnicache_ai.adapters.autogen_adapter import AutoGenCacheAdapter

agent = AssistantAgent("assistant", model_client=...)
cached = AutoGenCacheAdapter(agent, manager)
result = await cached.arun("What is 2+2?")

# pyautogen 0.2.x (legacy)
from autogen import ConversableAgent
agent = ConversableAgent(name="assistant", llm_config={...})
cached = AutoGenCacheAdapter(agent, manager)
reply = cached.generate_reply(messages=[{"role": "user", "content": "Hi"}])
```

### CrewAI

```python
from crewai import Crew
from omnicache_ai.adapters.crewai_adapter import CrewAICacheAdapter

crew = Crew(agents=[...], tasks=[...])
cached_crew = CrewAICacheAdapter(crew, manager)

result = cached_crew.kickoff(inputs={"topic": "AI trends"})
result = await cached_crew.kickoff_async(inputs={"topic": "AI trends"})
```

### Agno

```python
from agno.agent import Agent
from omnicache_ai.adapters.agno_adapter import AgnoCacheAdapter

agent = Agent(model=..., tools=[...])
cached = AgnoCacheAdapter(agent, manager)

response = cached.run("Summarize the latest AI research")
response = await cached.arun("Summarize the latest AI research")
```

### Google ADK

```python
from google.adk.agents import Agent
from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

agent = Agent(name="research_agent", model="gemini-2.0-flash", instruction="...")
cached = GoogleADKCacheAdapter(agent, manager)

result = cached.run("Summarise the quarterly report")    # live call
result = cached.run("Summarise the quarterly report")    # instant from cache
result = await cached.arun("Async task")
```

### OpenAI Agents SDK

```python
from agents import Agent, Runner
from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

agent = Agent(name="assistant", instructions="Be concise", model="gpt-4o")
adapter = OpenAIAgentsCacheAdapter(manager)

result = adapter.run(agent, "What is RAG?")
result = await adapter.arun(agent, "What is RAG?")  # async
```

### LlamaIndex

```python
from llama_index.llms.openai import OpenAI
from omnicache_ai.adapters.llamaindex_adapter import (
    LlamaIndexLLMCacheAdapter,
    LlamaIndexQueryCacheAdapter,
)

# LLM cache
cached_llm = LlamaIndexLLMCacheAdapter(OpenAI(model="gpt-4o"), manager)
response = cached_llm.complete("What is vector search?")

# QueryEngine (RAG) cache
engine = index.as_query_engine()
cached_engine = LlamaIndexQueryCacheAdapter(engine, manager)
response = cached_engine.query("What are the key findings?")
```

### Claude Agent SDK

```python
from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

adapter = ClaudeAgentCacheAdapter(manager)

async for msg in adapter.query("Fix the import error in utils.py", options=options):
    print(msg)  # streams on first call, replays from cache on second
```

### OpenAI SDK

```python
import openai
from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

client = openai.OpenAI()
adapter = OpenAICacheAdapter(client, manager)

response = adapter.chat_create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
# Second call with identical args returns instantly from cache

# Async
client = openai.AsyncOpenAI()
adapter = OpenAICacheAdapter(client, manager)
response = await adapter.achat_create(model="gpt-4o", messages=[...])
```

### Anthropic SDK

```python
import anthropic
from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

client = anthropic.Anthropic()
adapter = AnthropicCacheAdapter(client, manager)

response = adapter.messages_create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)

# Async
client = anthropic.AsyncAnthropic()
adapter = AnthropicCacheAdapter(client, manager)
response = await adapter.amessages_create(model="claude-sonnet-4-6", ...)
```

### A2A (Agent-to-Agent)

```python
from omnicache_ai.adapters.a2a_adapter import A2ACacheAdapter

adapter = A2ACacheAdapter(manager, agent_id="planner")

# Explicit call
result = adapter.process(handler_fn, task_payload)
result = await adapter.aprocess(async_handler, task_payload)

# As a decorator
@adapter.wrap
def handle_task(payload: dict) -> dict:
    return downstream_agent.process(payload)
```

---

## v0.2.0 Features

### Cache Metrics

```python
manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())

manager.get("key")          # miss
manager.set("key", "val")
manager.get("key")          # hit

print(manager.metrics.snapshot())
# {'hits': 1, 'misses': 1, 'evictions': 0, 'sets': 1, 'hit_rate': 0.5, 'miss_rate': 0.5}
```

### Pluggable Serializer

```python
from omnicache_ai import JsonSerializer, ResponseCache

# Use JSON instead of pickle (safer for Redis with untrusted data)
cache = ResponseCache(manager, serializer=JsonSerializer())
```

### Stampede Protection

`ResponseCache.get_or_generate()` uses a per-key lock automatically — under concurrency, only one thread calls the LLM; others wait and read from cache.

### Tiered Backend (L1 + L2)

```python
from omnicache_ai import TieredBackend, InMemoryBackend
from omnicache_ai.backends.redis_backend import RedisBackend

backend = TieredBackend(
    l1=InMemoryBackend(max_size=1000),   # fast, local
    l2=RedisBackend(url="redis://..."),  # persistent, shared
    l1_ttl=300,                          # 5-min local copy
)
manager = CacheManager(backend=backend, key_builder=CacheKeyBuilder())
```

### Compression

```python
from omnicache_ai import GzipCompressor, CacheManager

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    compressor=GzipCompressor(level=6),  # compress all stored bytes
)
```

### Streaming Response Cache

```python
from omnicache_ai import StreamingResponseCache

stream_cache = StreamingResponseCache(manager)

def stream_fn(messages):
    return openai_client.chat.completions.create(
        model="gpt-4o", messages=messages, stream=True
    )

# First call: live stream + buffered to cache
# Second call: replays chunks from cache at full speed
for chunk in stream_cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Async Backend

```python
from omnicache_ai import AsyncInMemoryBackend

# Use in async frameworks — does not block the event loop
backend = AsyncInMemoryBackend(max_size=10_000)
value = await backend.get("key")
await backend.set("key", "value", ttl=60)
```

---

## Tag-Based Invalidation

```python
from omnicache_ai import InvalidationEngine, InMemoryBackend, CacheManager, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)

manager.set("key1", "v1", tags=["model:gpt-4o", "env:prod"])
manager.set("key2", "v2", tags=["model:gpt-4o"])

count = manager.invalidate("model:gpt-4o")  # removes both entries

# ResponseCache / ContextCache tag automatically
from omnicache_ai import ResponseCache, ContextCache
rc = ResponseCache(manager)
rc.invalidate_model("gpt-4o")           # remove all gpt-4o responses

ctx = ContextCache(manager)
ctx.invalidate_session("user-123")      # clear all session turns
```

---

## Backends

| Backend           | Extra             | Use case                               |
| ----------------- | ----------------- | -------------------------------------- |
| `InMemoryBackend` | —                 | Dev, testing, single-process           |
| `DiskBackend`     | —                 | Survives restarts, single-machine      |
| `RedisBackend`    | `[redis]`         | Shared cache across processes/services |
| `FAISSBackend`    | `[vector-faiss]`  | Semantic/vector similarity search      |
| `ChromaBackend`   | `[vector-chroma]` | Persistent vector store with metadata  |

```python
from omnicache_ai.backends.redis_backend import RedisBackend
from omnicache_ai.backends.disk_backend import DiskBackend

manager = CacheManager(backend=RedisBackend(url="redis://localhost:6379/0"), ...)
manager = CacheManager(backend=DiskBackend(path="/var/cache/omnicache"), ...)
```

---

## Custom Backend

Implement the `CacheBackend` Protocol — no inheritance required (structural typing):

```python
from omnicache_ai.backends.base import CacheBackend
from typing import Any

class MyBackend:
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...

assert isinstance(MyBackend(), CacheBackend)  # True
```

---

## Project Structure

```
omnicache_ai/
├── __init__.py                   # Public API surface (28 exports)
├── __main__.py                   # CLI: stats | flush | inspect <key>
├── config/
│   └── settings.py               # OmnicacheSettings dataclass + from_env()
├── backends/
│   ├── base.py                   # CacheBackend + VectorBackend Protocols
│   ├── async_base.py             # AsyncCacheBackend Protocol
│   ├── memory_backend.py         # InMemoryBackend (LRU, thread-safe, RLock)
│   ├── async_memory_backend.py   # AsyncInMemoryBackend (asyncio.Lock)
│   ├── disk_backend.py           # DiskBackend (diskcache, process-safe)
│   ├── redis_backend.py          # RedisBackend [optional: redis]
│   ├── tiered_backend.py         # TieredBackend (L1 memory + L2 any backend)
│   └── vector_backend.py         # FAISSBackend + ChromaBackend [optional]
├── core/
│   ├── key_builder.py            # namespace:type:sha256[:16] canonical keys
│   ├── metrics.py                # CacheMetrics (hits/misses/evictions/hit_rate)
│   ├── serializer.py             # Serializer protocol, PickleSerializer, JsonSerializer
│   ├── compressor.py             # Compressor protocol, GzipCompressor, NoopCompressor
│   ├── stampede.py               # StampedeShield (per-key threading.Lock)
│   ├── policies.py               # TTLPolicy, EvictionPolicy (wired into InMemoryBackend)
│   ├── invalidation.py           # Tag-based InvalidationEngine
│   └── cache_manager.py          # Central orchestrator + from_settings()
├── layers/
│   ├── embedding_cache.py        # np.ndarray ↔ bytes serialization
│   ├── retrieval_cache.py        # list[Document], pluggable serializer
│   ├── context_cache.py          # session_id + turn_index keyed
│   ├── response_cache.py         # model + messages + params keyed, stampede-safe
│   ├── semantic_cache.py         # exact → vector two-tier lookup
│   └── streaming_cache.py        # StreamingResponseCache (sync + async generators)
├── middleware/
│   ├── llm_middleware.py         # LLMMiddleware + AsyncLLMMiddleware
│   ├── embedding_middleware.py   # EmbeddingMiddleware
│   └── retriever_middleware.py   # RetrieverMiddleware
└── adapters/
    ├── openai_adapter.py         # OpenAICacheAdapter (chat.completions.create)
    ├── anthropic_adapter.py      # AnthropicCacheAdapter (messages.create)
    ├── langchain_adapter.py      # BaseCache (lookup/update/alookup/aupdate)
    ├── langgraph_adapter.py      # BaseCheckpointSaver (get_tuple/put/list + async)
    ├── autogen_adapter.py        # AssistantAgent 0.4+ + ConversableAgent 0.2.x
    ├── crewai_adapter.py         # Crew.kickoff() + kickoff_async()
    ├── agno_adapter.py           # Agent.run() + arun()
    └── a2a_adapter.py            # process() + aprocess() + @wrap
```

---

## Development

```bash
# Clone and install with dev deps
git clone https://github.com/ashishpatel26/omnicache-ai
cd omnicache-ai
uv sync --dev

# Install pre-commit hooks (runs automatically on every commit)
uv run pre-commit install

# Run all tests
uv run pytest

# With coverage report
uv run pytest --cov=omnicache_ai --cov-report=term-missing

# Lint + format + type check (via pre-commit)
uv run pre-commit run --all-files

# Run specific layer tests
uv run pytest tests/layers/ tests/core/ -v

# Run adapter tests (requires optional deps)
uv run pytest tests/adapters/ -v
```

---

## Contributing

We welcome contributions of all kinds — bug fixes, new backends, new adapters, documentation, and performance improvements.

| File | Purpose |
| ---- | ------- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Full dev setup, coding standards, how to add backends/adapters |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Contributor Covenant 2.1 — community standards |
| [.github/ISSUE_TEMPLATE/bug_report.yml](.github/ISSUE_TEMPLATE/bug_report.yml) | Structured bug report with version, backend, reproduction fields |
| [.github/ISSUE_TEMPLATE/feature_request.yml](.github/ISSUE_TEMPLATE/feature_request.yml) | Feature request with area dropdown, motivation, solution fields |
| [.github/pull_request_template.md](.github/pull_request_template.md) | PR checklist: type, changes, tests, breaking changes |

**Quick start for contributors:**

```bash
git clone https://github.com/ashishpatel26/omnicache-ai
cd omnicache-ai
uv sync --dev
uv run pre-commit install
uv run pytest  # all green before you start
```

Open an issue or [Discussion](https://github.com/ashishpatel26/omnicache-ai/discussions) before starting large changes.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ for the AI engineering community</sub>
</div>
