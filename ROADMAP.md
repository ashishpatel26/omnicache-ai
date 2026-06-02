# Roadmap

## v0.3.0 — Current (released 2026-05)

- 8 cache layers: ResponseCache, EmbeddingCache, RetrievalCache, ContextCache, SemanticCache, AdaptiveSemanticCache, StreamingResponseCache, PromptCacheLayer
- 9 backends: InMemory (sync + async), Disk, Redis, TieredBackend, FAISS, ChromaDB, Qdrant, Weaviate
- 13 framework adapters: OpenAI SDK, Anthropic SDK, LangChain, LangGraph, AutoGen, CrewAI, Agno, A2A, LlamaIndex, Google ADK, OpenAI Agents, Claude Agent SDK
- Prometheus + OpenTelemetry observability
- 76% test coverage, 272 tests, 70% coverage gate enforced on CI

## v0.4.0 — In Progress (target: 2026-07)

### New Backends
- [ ] **Pinecone** vector backend (`vector-pinecone` extra)
- [ ] **MongoDB Atlas Vector Search** backend

### New Adapters
- [ ] **Mistral AI** adapter (`mistral-adapter` extra)
- [ ] **Gemini SDK** adapter (`gemini` extra)
- [ ] **Vertex AI** adapter (enterprise Google Cloud)

### New Layer
- [ ] **PersistentSemanticCache** — FAISS index serialized to disk, survives process restarts

### Config
- [ ] `OMNICACHE_MAX_TOKENS_PER_ENTRY` — skip caching oversized responses
- [ ] `OMNICACHE_CACHE_ON_ERROR` — configurable error response caching

### Quality
- [ ] Benchmark suite (`benchmarks/`) with latency numbers for docs
- [ ] `docs/migration-from-gptcache.md` — drop-in replacement guide

## v1.0.0 — Target: 2026-Q4

- Stable public API (no breaking changes after 1.0)
- 90%+ test coverage
- Full async backend support (all backends have native async variants)
- Distributed cache warming
- CLI: `omnicache inspect`, `omnicache analyze` (cost savings estimation)
- Production deployment guide (Kubernetes sidecar, Docker Compose)

## Requested / Under Consideration

- Cassandra backend
- DynamoDB backend
- Azure CosmosDB backend
- Embedding model auto-detection (skip EmbeddingCache key if model unchanged)
- LangSmith tracing integration
- Cache hit/miss webhooks

## Contributing

Want to add a backend or adapter? See [CONTRIBUTING.md](CONTRIBUTING.md) for the backend template and adapter template. Issues tagged [`backend-request`](https://github.com/ashishpatel26/omnicache-ai/labels/backend-request) and [`adapter-request`](https://github.com/ashishpatel26/omnicache-ai/labels/adapter-request) welcome PRs.
