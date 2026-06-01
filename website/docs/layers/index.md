---
title: "Cache Layers"
---

# Cache Layers

OmniCache-AI ships eight purpose-built cache layers. Each targets a distinct stage of the AI pipeline with optimized serialization and a consistent `get` / `set` / `get_or_*` interface.

---

## At a Glance

| Layer | Class | What it caches | Key |
|---|---|---|---|
| [Response](response.md) | `ResponseCache` | LLM completions | model + messages + params |
| [Streaming](streaming.md) | `StreamingResponseCache` | Streaming LLM chunks (buffered) | model + messages + params |
| [Embedding](embedding.md) | `EmbeddingCache` | `np.ndarray` vectors | text + model |
| [Retrieval](retrieval.md) | `RetrievalCache` | Document lists | query + retriever + top_k |
| [Context](context.md) | `ContextCache` | Conversation history | session ID + turn index |
| [Semantic](semantic.md) | `SemanticCache` | Any value by meaning (exact + cosine) | exact key or vector similarity |
| [Adaptive Semantic](adaptive-semantic.md) | `AdaptiveSemanticCache` | Semantic cache with auto-tuning threshold | same as SemanticCache |
| [Prompt Cache](prompt-cache.md) | `PromptCacheLayer` | Provider cache_control injection + savings | — (wraps API calls) |

---

## Pipeline Diagram

```mermaid
flowchart TD
    Q(["Incoming Query"]) --> ASC{"AdaptiveSemanticCache\n(auto-tuning threshold)"}
    ASC -->|hit| R(["Cached Response"])
    ASC -->|miss| SC{"SemanticCache\n(exact + vector)"}
    SC -->|hit| R
    SC -->|miss| RC{"ResponseCache\n(model + messages + params)"}
    RC -->|hit| R
    RC -->|miss| SRC{"StreamingResponseCache\n(buffered chunks)"}
    SRC -->|hit| R
    SRC -->|miss| RET{"RetrievalCache\n(query + retriever + top_k)"}
    RET -->|hit| R
    RET -->|miss| EC{"EmbeddingCache\n(text + model)"}
    EC -->|hit| R
    EC -->|miss| CC{"ContextCache\n(session + turn)"}
    CC -->|hit| R
    CC -->|miss| API["🤖 Live API Call\n+ PromptCacheLayer\n(cache_control injection)"]
    API --> STORE["Store in applicable layers"]
    STORE --> R

    style ASC fill:#1a3a2a,color:#fff
    style SC fill:#4c1d95,color:#fff
    style RC fill:#1e3a5f,color:#fff
    style SRC fill:#1e2a4a,color:#fff
    style RET fill:#14532d,color:#fff
    style EC fill:#713f12,color:#fff
    style CC fill:#7f1d1d,color:#fff
```

---

## Shared Design Principles

1. **Constructor takes a `CacheManager`** — except `SemanticCache`/`AdaptiveSemanticCache` which wire their own backends.
2. **`get(...)` returns `None` on miss** — never raises.
3. **`set(...)` accepts optional `ttl`** — falls back to `TTLPolicy` when omitted.
4. **`get_or_*` convenience methods** — compute + cache in one call.
5. **Pluggable serializer** — all layers accept `serializer=` param.

---

## Next Steps

- [ResponseCache](response.md) — cache LLM completions
- [StreamingResponseCache](streaming.md) — cache streaming LLM output
- [SemanticCache](semantic.md) — meaning-aware caching
- [AdaptiveSemanticCache](adaptive-semantic.md) — auto-tuning threshold
- [PromptCacheLayer](prompt-cache.md) — provider prompt cache integration
- [EmbeddingCache](embedding.md) — cache dense vectors
- [RetrievalCache](retrieval.md) — cache retriever results
- [ContextCache](context.md) — cache conversation history
