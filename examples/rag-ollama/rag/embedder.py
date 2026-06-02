"""Cached Ollama embeddings via OmniCache-AI EmbeddingCache.

Uses local Ollama server (http://localhost:11434) — no API key needed.
Model: embeddinggemma:300m (set OLLAMA_EMBED_MODEL in .env to override).

EmbeddingCache.set signature: set(text, vector, model_id)
EmbeddingCache.get signature: get(text, model_id) -> ndarray | None
"""

from __future__ import annotations

import os
import time

import numpy as np
import requests
from dotenv import load_dotenv
from rich.console import Console

from omnicache_ai.layers.embedding_cache import EmbeddingCache

load_dotenv()
console = Console()

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma:300m")


def _ollama_embed(text: str, model: str) -> np.ndarray:
    resp = requests.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=120,  # first call loads model into memory — can be slow
    )
    resp.raise_for_status()
    vec = np.array(resp.json()["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


class CachedEmbedder:
    """Embed text via Ollama, caching in EmbeddingCache."""

    def __init__(self, cache: EmbeddingCache, model: str = EMBED_MODEL) -> None:
        self._cache = cache
        self._model = model
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            raise RuntimeError("Call embed() at least once to detect dim.")
        return self._dim

    def embed(self, text: str, *, silent: bool = False) -> np.ndarray:
        # get(text, model_id)
        cached = self._cache.get(text, self._model)
        if cached is not None:
            if self._dim is None:
                self._dim = cached.shape[0]
            if not silent:
                snippet = (text[:60] + "...") if len(text) > 60 else text
                console.print(f"  [green]EMBED HIT[/green]  '{snippet}'")
            return cached

        t0 = time.perf_counter()
        vec = _ollama_embed(text, self._model)
        elapsed = time.perf_counter() - t0

        if self._dim is None:
            self._dim = vec.shape[0]

        # set(text, vector, model_id)
        self._cache.set(text, vec, self._model)

        if not silent:
            snippet = (text[:60] + "...") if len(text) > 60 else text
            console.print(
                f"  [yellow]EMBED MISS[/yellow] '{snippet}' -> {elapsed:.3f}s dim={self._dim}"
            )
        return vec

    def embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        cached_map: dict[str, np.ndarray | None] = {
            t: self._cache.get(t, self._model) for t in texts
        }
        misses = [t for t, v in cached_map.items() if v is None]

        if misses:
            t0 = time.perf_counter()
            vecs = [_ollama_embed(t, self._model) for t in misses]
            elapsed = time.perf_counter() - t0
            console.print(
                f"  [yellow]EMBED MISS[/yellow] batch {len(misses)} texts -> {elapsed:.3f}s"
            )
            for t, vec in zip(misses, vecs):
                if self._dim is None:
                    self._dim = vec.shape[0]
                self._cache.set(t, vec, self._model)
                cached_map[t] = vec

        return [cached_map[t] for t in texts]  # type: ignore[return-value]
