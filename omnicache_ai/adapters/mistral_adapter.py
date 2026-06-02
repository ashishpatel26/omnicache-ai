"""Mistral AI SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    from mistralai import Mistral as _Mistral  # type: ignore[import-untyped]

    _MISTRAL_AVAILABLE = True
except ImportError:
    _Mistral = None  # type: ignore[assignment]
    _MISTRAL_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class MistralCacheAdapter:
    """Wraps mistralai.Mistral chat completions with caching.

    Intercepts calls to ``client.chat.complete`` and returns cached
    responses for identical (model, messages, params) combinations.

    Sync usage::

        from mistralai import Mistral
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.mistral_adapter import MistralCacheAdapter

        client = Mistral(api_key="...")
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = MistralCacheAdapter(client, manager)

        response = adapter.chat_complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": "Hello"}],
        )

    Async usage::

        response = await adapter.achat_complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": "Hello"}],
        )

    Install with: pip install 'omnicache-ai[mistral]'
    """

    def __init__(self, client: Any, manager: "CacheManager") -> None:
        if not _MISTRAL_AVAILABLE:
            raise ImportError(
                "MistralCacheAdapter requires 'mistralai'. "
                "Install with: pip install 'omnicache-ai[mistral]'"
            )
        self._client = client
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, kwargs: dict[str, Any]) -> str:
        model = kwargs.get("model", "default")
        messages = kwargs.get("messages", [])
        params = {k: v for k, v in kwargs.items() if k not in ("model", "messages", "stream")}
        content = json.dumps({"messages": messages, "params": params}, sort_keys=True, default=str)
        return self._manager.key_builder.build("response", content, extra={"model": model})

    def chat_complete(self, **kwargs: Any) -> Any:
        """Cached synchronous chat completion."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = self._client.chat.complete(**kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{kwargs.get('model', 'default')}"],
        )
        return response

    async def achat_complete(self, **kwargs: Any) -> Any:
        """Cached async chat completion."""
        key = self._build_key(kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = await self._client.chat.complete_async(**kwargs)
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
