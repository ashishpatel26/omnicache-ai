"""Cached OpenRouter LLM generation via OmniCache-AI ResponseCache.

ResponseCache signatures:
  get(messages, model_id) -> Any | None
  set(messages, response, model_id) -> None
"""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

from omnicache_ai.layers.response_cache import ResponseCache

load_dotenv()
console = Console()

LLM_MODEL = os.getenv("OPENROUTER_LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

_SYSTEM = (
    "You are a helpful assistant. Answer using ONLY the provided context. "
    "If context doesn't contain the answer, say 'I don't have enough information.' "
    "Be concise and factual."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client  # noqa: PLW0603
    if _client is None:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")
        _client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
    return _client


class CachedGenerator:
    """Generate answers via OpenRouter, caching in ResponseCache."""

    def __init__(self, cache: ResponseCache, model: str = LLM_MODEL) -> None:
        self._cache = cache
        self._model = model

    def generate(self, context: str, question: str) -> tuple[str, bool]:
        """Return (answer, was_cached)."""
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        # get(messages, model_id)
        cached = self._cache.get(messages, self._model)
        if cached is not None:
            console.print(f"  [green]RESPONSE HIT[/green]  '{question[:70]}'")
            return str(cached), True

        t0 = time.perf_counter()
        resp = _get_client().chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
        )
        answer = resp.choices[0].message.content or ""
        elapsed = time.perf_counter() - t0

        # set(messages, response, model_id)
        self._cache.set(messages, answer, self._model)
        console.print(f"  [yellow]RESPONSE MISS[/yellow] '{question[:70]}' -> {elapsed:.2f}s")
        return answer, False
