"""OpenAI SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    import openai as _openai

    _OPENAI_AVAILABLE = True
except ImportError:
    _openai = None  # type: ignore[assignment]
    _OPENAI_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class OpenAICacheAdapter:
    """Wraps openai.OpenAI (or AsyncOpenAI) chat completions with caching.

    Intercepts calls to ``client.chat.completions.create`` and returns cached
    responses for identical (model, messages, params) combinations.

    Sync usage::

        import openai
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.openai_adapter import OpenAICacheAdapter

        client = openai.OpenAI()
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = OpenAICacheAdapter(client, manager)

        response = adapter.chat_create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )

    Async usage::

        client = openai.AsyncOpenAI()
        adapter = OpenAICacheAdapter(client, manager)
        response = await adapter.achat_create(model="gpt-4o", messages=[...])

    Install with: pip install 'omnicache-ai[openai]'
    """

    def __init__(self, client: Any, manager: "CacheManager") -> None:
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAICacheAdapter requires 'openai'. "
                "Install with: pip install 'omnicache-ai[openai]'"
            )
        self._client = client
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, kwargs: dict[str, Any]) -> str:
        model = kwargs.get("model", "default")
        messages = kwargs.get("messages", [])
        # Strip non-deterministic params from key
        params = {k: v for k, v in kwargs.items() if k not in ("model", "messages", "stream")}
        content = json.dumps({"messages": messages, "params": params}, sort_keys=True, default=str)
        return self._manager.key_builder.build("response", content, extra={"model": model})

    def chat_create(self, **kwargs: Any) -> Any:
        """Cached synchronous chat completion."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = self._client.chat.completions.create(**kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{kwargs.get('model', 'default')}"],
        )
        return response

    async def achat_create(self, **kwargs: Any) -> Any:
        """Cached async chat completion."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = await self._client.chat.completions.create(**kwargs)
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
