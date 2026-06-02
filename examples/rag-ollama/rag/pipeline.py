"""Full RAG pipeline: retrieve → generate, all three cache layers active.

Flow:
  query
    → EmbeddingCache.get(query)       [Layer 1 — skip OpenRouter embed API]
    → FAISS search
    → RetrievalCache.get(query)       [Layer 2 — skip FAISS search]
    → ResponseCache.get(messages)     [Layer 3 — skip OpenRouter LLM]
    → answer
"""

from __future__ import annotations

import time

from rich.console import Console
from rich.table import Table

from .cache import build_cache_manager, build_layers
from .embedder import CachedEmbedder
from .generator import CachedGenerator
from .indexer import DocumentIndex

console = Console()


class RAGPipeline:
    def __init__(
        self,
        llm_model: str | None = None,
        embed_model: str | None = None,
        top_k: int = 4,
    ) -> None:
        self._top_k = top_k
        manager = build_cache_manager()
        emb_cache, ret_cache, resp_cache = build_layers(manager)
        self._manager = manager

        kwargs_embed = {"model": embed_model} if embed_model else {}
        kwargs_llm = {"model": llm_model} if llm_model else {}

        self._embedder = CachedEmbedder(emb_cache, **kwargs_embed)
        self._index = DocumentIndex(self._embedder, ret_cache)
        self._generator = CachedGenerator(resp_cache, **kwargs_llm)

    # ------------------------------------------------------------------

    def ingest_file(self, path: str) -> int:
        with open(path) as f:
            text = f.read()
        return self._index.ingest([text])

    def ingest_texts(self, texts: list[str]) -> int:
        return self._index.ingest(texts)

    def is_indexed(self) -> bool:
        return not self._index.is_empty()

    # ------------------------------------------------------------------

    def query(self, question: str) -> str:
        console.rule(f"[bold]Query:[/bold] {question}")
        t0 = time.perf_counter()

        docs = self._index.retrieve(question, top_k=self._top_k)
        if not docs:
            return "No documents indexed. Run `python main.py ingest` first."

        context = "\n\n---\n\n".join(docs)
        answer, was_cached = self._generator.generate(context, question)

        elapsed = time.perf_counter() - t0
        tag = "[green]CACHED[/green]" if was_cached else "[yellow]LIVE[/yellow]"
        console.print(f"\n  Total: {elapsed:.3f}s  {tag}\n")
        return answer

    # ------------------------------------------------------------------

    def print_stats(self) -> None:
        snap = self._manager.metrics.snapshot()
        table = Table(title="OmniCache-AI — Cache Stats")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold white")
        table.add_row("Hits", str(snap["hits"]))
        table.add_row("Misses", str(snap["misses"]))
        table.add_row("Hit rate", f"{snap['hit_rate']:.1%}")
        table.add_row("Total writes", str(snap["sets"]))
        console.print(table)
