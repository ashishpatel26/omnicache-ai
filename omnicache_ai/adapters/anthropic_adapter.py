"""Anthropic SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    import anthropic as _anthropic

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _anthropic = None  # type: ignore[assignment]
    _ANTHROPIC_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class AnthropicCacheAdapter:
    """Wraps anthropic.Anthropic (or AsyncAnthropic) messages with caching.

    Intercepts calls to ``client.messages.create`` and returns cached responses
    for identical (model, messages, params) combinations.

    Sync usage::

        import anthropic
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.anthropic_adapter import AnthropicCacheAdapter

        client = anthropic.Anthropic()
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = AnthropicCacheAdapter(client, manager)

        response = adapter.messages_create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}],
        )

    Async usage::

        client = anthropic.AsyncAnthropic()
        adapter = AnthropicCacheAdapter(client, manager)
        response = await adapter.amessages_create(model="claude-sonnet-4-6", ...)

    Install with: pip install 'omnicache-ai[anthropic]'
    """

    def __init__(self, client: Any, manager: "CacheManager") -> None:
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError(
                "AnthropicCacheAdapter requires 'anthropic'. "
                "Install with: pip install 'omnicache-ai[anthropic]'"
            )
        self._client = client
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, kwargs: dict[str, Any]) -> str:
        model = kwargs.get("model", "default")
        messages = kwargs.get("messages", [])
        system = kwargs.get("system", "")
        params = {
            k: v for k, v in kwargs.items() if k not in ("model", "messages", "system", "stream")
        }
        content = json.dumps(
            {"messages": messages, "system": system, "params": params},
            sort_keys=True,
            default=str,
        )
        return self._manager.key_builder.build("response", content, extra={"model": model})

    def messages_create(self, **kwargs: Any) -> Any:
        """Cached synchronous messages.create."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = self._client.messages.create(**kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{kwargs.get('model', 'default')}"],
        )
        return response

    async def amessages_create(self, **kwargs: Any) -> Any:
        """Cached async messages.create."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = await self._client.messages.create(**kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{kwargs.get('model', 'default')}"],
        )
        return response

    def invalidate_model(self, model: str) -> int:
        """Invalidate all cached responses for a specific model."""
        return self._manager.invalidate(f"model:{model}")
