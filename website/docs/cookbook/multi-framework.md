---
title: "Multi-Framework Pipeline"
---

# Multi-Framework Pipeline

A complete example that wires **LangChain** LLM caching, **LangGraph** state persistence,
**Agno** agent caching, and **A2A** inter-agent caching into a single shared `CacheManager`.

```bash
pip install 'omnicache-ai[all]'
```

---

## Pipeline overview

```
User query
  -> LangChain (cached LLM call) -> outline
  -> LangGraph (stateful graph, checkpointed) -> structured plan
  -> Agno agent (cached) -> detailed write-up
  -> A2A reviewer (cached) -> final review
```

Every step shares one `CacheManager` backed by a disk cache with per-layer TTLs.
On the second run with the same input, every step is served from cache.

---

## Full example

```python
"""
Pipeline:
  User query
    -> LangChain (cached LLM call) -> outline
    -> LangGraph (stateful graph, checkpointed) -> structured plan
    -> Agno agent (cached) -> detailed write-up
    -> A2A reviewer (cached) -> final review
"""
import asyncio
import numpy as np

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.globals import set_llm_cache
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from agno.agent import Agent as AgnoAgent
from agno.models.openai import OpenAIChat
from typing import Annotated, TypedDict

from omnicache_ai import (
    CacheManager, DiskBackend, CacheKeyBuilder,
    InvalidationEngine, InMemoryBackend,
    TTLPolicy, EmbeddingCache,
)
from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter
from omnicache_ai.adapters.langgraph_adapter import LangGraphCacheAdapter
from omnicache_ai.adapters.agno_adapter import AgnoCacheAdapter
from omnicache_ai.adapters.a2a_adapter import A2ACacheAdapter

# ── Shared cache manager ───────────────────────────────────────────────────
manager = CacheManager(
    backend=DiskBackend(directory="/var/cache/pipeline"),
    key_builder=CacheKeyBuilder(namespace="pipeline"),
    ttl_policy=TTLPolicy(
        default_ttl=3600,
        per_type={"embed": 86400, "response": 600},
    ),
    invalidation_engine=InvalidationEngine(InMemoryBackend()),
)

# ── 1. LangChain — cache all LLM calls globally ────────────────────────────
set_llm_cache(LangChainCacheAdapter(manager))
llm = ChatOpenAI(model="gpt-4o-mini")

# ── 2. LangGraph — stateful agent graph ───────────────────────────────────
class State(TypedDict):
    messages: Annotated[list, add_messages]
    plan: str

def outline_node(state: State) -> State:
    resp = llm.invoke([
        {"role": "system", "content": "Create a numbered outline (max 5 points)."},
        *state["messages"],
    ])
    return {"plan": resp.content}

builder = StateGraph(State)
builder.add_node("outline", outline_node)
builder.set_entry_point("outline")
builder.add_edge("outline", END)

checkpointer = LangGraphCacheAdapter(manager)
graph = builder.compile(checkpointer=checkpointer)

# ── 3. Agno — cached writer agent ─────────────────────────────────────────
writer_agent = AgnoAgent(
    model=OpenAIChat(id="gpt-4o-mini"),
    description="Expand an outline into prose.",
)
cached_writer = AgnoCacheAdapter(writer_agent, manager)

# ── 4. A2A — cached reviewer ───────────────────────────────────────────────
reviewer_adapter = A2ACacheAdapter(manager, agent_id="reviewer")

async def review_fn(payload: dict) -> dict:
    resp = llm.invoke([
        {"role": "system", "content": "Review and improve the text. Return the improved version."},
        {"role": "user",   "content": payload["text"]},
    ])
    return {"reviewed": resp.content}

# ── 5. Embeddings cache ────────────────────────────────────────────────────
embedder = OpenAIEmbeddings(model="text-embedding-3-small")
emb_cache = EmbeddingCache(manager)

# ── Pipeline ───────────────────────────────────────────────────────────────
async def run_pipeline(query: str) -> str:
    config = {"configurable": {"thread_id": f"pipeline-{hash(query)}"}}

    # Step 1: LangGraph outline (checkpointed)
    state = graph.invoke(
        {"messages": [("user", query)], "plan": ""},
        config=config,
    )
    outline = state["plan"]
    print("Outline:\n", outline)

    # Step 2: Agno writer (cached)
    write_result = await cached_writer.arun(
        f"Expand this outline into a short article:\n{outline}"
    )
    article = write_result.content
    print("\nDraft:\n", article[:300], "...")

    # Step 3: A2A reviewer (cached)
    reviewed = await reviewer_adapter.aprocess(review_fn, {"text": article})
    print("\nReviewed:\n", reviewed["reviewed"][:300], "...")

    # Step 4: Embed the final article (cached)
    vec = emb_cache.get_or_compute(
        text=reviewed["reviewed"],
        compute_fn=lambda t: np.array(embedder.embed_query(t), dtype=np.float32),
        model_id="text-embedding-3-small",
    )
    print(f"\nEmbedding shape: {vec.shape}")

    return reviewed["reviewed"]

if __name__ == "__main__":
    result = asyncio.run(run_pipeline("Write about the impact of caching on AI systems."))
    # Run again — every step served from cache
    result2 = asyncio.run(run_pipeline("Write about the impact of caching on AI systems."))
    assert result == result2
    print("\nAll steps cached correctly!")
```

:::tip
In production, replace `InMemoryBackend()` for the `InvalidationEngine` tag store
with a `RedisBackend` so that tag metadata is shared across workers.
:::
