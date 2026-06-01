"""Provider-level prompt cache layer — surfaces Anthropic/OpenAI prefix caching."""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.metrics import CacheMetrics

# Anthropic pricing: cached input tokens cost 10% of normal price
_ANTHROPIC_CACHE_DISCOUNT = 0.90
# OpenAI prompt cache: 50% discount on cached tokens
_OPENAI_CACHE_DISCOUNT = 0.50

# Rough cost per 1M input tokens (USD) — used for savings estimation
_COST_PER_1M = {
    "claude-opus-4": 15.0,
    "claude-sonnet-4-6": 3.0,
    "claude-haiku-4-5": 0.80,
    "gpt-4o": 5.0,
    "gpt-4o-mini": 0.15,
    "o1": 15.0,
}


class PromptCacheLayer:
    """Injects provider-level cache_control markers and tracks savings.

    Anthropic supports explicit cache_control breakpoints — long system prompts
    and repeated context blocks are cached server-side at 90% discount.
    OpenAI caches automatically for prompts ≥ 1024 tokens (50% discount).

    This layer:
    - Injects ``cache_control: {"type": "ephemeral"}`` on Anthropic system prompts
      when the prompt exceeds ``min_tokens_to_cache`` characters
    - Tracks ``provider_cache_hits``, ``estimated_tokens_saved``, and
      ``estimated_cost_saved_usd`` in the supplied ``CacheMetrics`` instance
    - Works with both sync and async Anthropic/OpenAI clients

    Usage::

        import anthropic
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder, CacheMetrics
        from omnicache_ai.layers.prompt_cache import PromptCacheLayer

        client = anthropic.Anthropic()
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        layer = PromptCacheLayer(metrics=manager.metrics)

        response = layer.anthropic_create(
            client,
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are an expert Python engineer...",  # auto-cached if long
            messages=[{"role": "user", "content": "Fix the auth bug"}],
        )

    Args:
        metrics: CacheMetrics instance to record provider cache hits/savings.
        min_chars_to_cache: System prompt character threshold for cache injection (default: 1024).
    """

    def __init__(
        self,
        metrics: "CacheMetrics | None" = None,
        min_chars_to_cache: int = 1024,
    ) -> None:
        self._metrics = metrics
        self._min_chars = min_chars_to_cache
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------

    def _inject_anthropic_cache(self, system: str | list[Any] | None) -> str | list[Any] | None:
        """Wrap a plain-string system prompt with cache_control if long enough."""
        if system is None:
            return None
        if isinstance(system, str) and len(system) >= self._min_chars:
            return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        return system

    def _record_anthropic_savings(self, response: Any, model: str) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        if cache_read <= 0:
            return
        cost_per_token = _COST_PER_1M.get(model, 3.0) / 1_000_000
        saved_usd = cache_read * cost_per_token * _ANTHROPIC_CACHE_DISCOUNT
        if self._metrics is not None:
            with self._lock:
                self._metrics.provider_cache_hits += 1
                self._metrics.estimated_tokens_saved += cache_read
                self._metrics.estimated_cost_saved_usd += saved_usd

    def anthropic_create(self, client: Any, **kwargs: Any) -> Any:
        """Sync Anthropic messages.create with auto cache_control injection."""
        kwargs["system"] = self._inject_anthropic_cache(kwargs.get("system"))
        response = client.messages.create(**kwargs)
        self._record_anthropic_savings(response, kwargs.get("model", ""))
        return response

    async def anthropic_acreate(self, client: Any, **kwargs: Any) -> Any:
        """Async Anthropic messages.create with auto cache_control injection."""
        kwargs["system"] = self._inject_anthropic_cache(kwargs.get("system"))
        response = await client.messages.create(**kwargs)
        self._record_anthropic_savings(response, kwargs.get("model", ""))
        return response

    # ------------------------------------------------------------------
    # OpenAI (automatic — just track savings from usage object)
    # ------------------------------------------------------------------

    def _record_openai_savings(self, response: Any, model: str) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
        cache_hit = getattr(prompt_tokens_details, "cached_tokens", 0) or 0
        if cache_hit <= 0:
            return
        cost_per_token = _COST_PER_1M.get(model, 5.0) / 1_000_000
        saved_usd = cache_hit * cost_per_token * _OPENAI_CACHE_DISCOUNT
        if self._metrics is not None:
            with self._lock:
                self._metrics.provider_cache_hits += 1
                self._metrics.estimated_tokens_saved += cache_hit
                self._metrics.estimated_cost_saved_usd += saved_usd

    def openai_create(self, client: Any, **kwargs: Any) -> Any:
        """Sync OpenAI chat.completions.create with savings tracking."""
        response = client.chat.completions.create(**kwargs)
        self._record_openai_savings(response, kwargs.get("model", ""))
        return response

    async def openai_acreate(self, client: Any, **kwargs: Any) -> Any:
        """Async OpenAI chat.completions.create with savings tracking."""
        response = await client.chat.completions.create(**kwargs)
        self._record_openai_savings(response, kwargs.get("model", ""))
        return response
