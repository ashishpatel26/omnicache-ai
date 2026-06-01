"""LLM response cache layer."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Callable

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER
from omnicache_ai.core.stampede import StampedeShield

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager
    from omnicache_ai.core.serializer import Serializer


def _hash_messages(messages: list[Any]) -> str:
    """Produce a short stable hash of a message list."""
    payload = json.dumps(messages, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class ResponseCache:
    """Cache layer for LLM responses.

    Only cache deterministic, non-personalised responses. Key discriminators
    include model ID, hashed messages, and hashed generation parameters.

    Args:
        manager: Underlying CacheManager instance.
        serializer: Serializer for encoding/decoding values (default: pickle).
    """

    def __init__(
        self,
        manager: "CacheManager",
        serializer: "Serializer | None" = None,
        stampede_shield: StampedeShield | None = None,
    ) -> None:
        self._manager = manager
        self._serializer = serializer or DEFAULT_SERIALIZER
        self._shield = stampede_shield or StampedeShield()

    def get(
        self,
        messages: list[Any],
        model_id: str = "default",
        params: dict[str, Any] | None = None,
    ) -> Any | None:
        """Return cached LLM response, or None on miss."""
        key = self._build_key(messages, model_id, params)
        raw = self._manager.get(key)
        return self._serializer.loads(raw) if raw is not None else None

    def set(
        self,
        messages: list[Any],
        response: Any,
        model_id: str = "default",
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Store an LLM response in the cache."""
        key = self._build_key(messages, model_id, params)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            ttl=ttl,
            cache_type="response",
            tags=tags or [f"model:{model_id}"],
        )

    def get_or_generate(
        self,
        messages: list[Any],
        generate_fn: Callable[[list[Any]], Any],
        model_id: str = "default",
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> Any:
        """Return cached response or call generate_fn under a per-key lock.

        The StampedeShield ensures that under concurrent requests for the
        same key, only one thread calls generate_fn; others wait and then
        read the result from cache.
        """
        key = self._build_key(messages, model_id, params)
        with self._shield.lock(key):
            cached = self.get(messages, model_id, params)
            if cached is not None:
                return cached
            response = generate_fn(messages)
            self.set(messages, response, model_id, params, ttl)
            return response

    def invalidate_model(self, model_id: str) -> int:
        """Invalidate all cached responses for a specific model."""
        return self._manager.invalidate(f"model:{model_id}")

    def _build_key(
        self,
        messages: list[Any],
        model_id: str,
        params: dict[str, Any] | None,
    ) -> str:
        messages_hash = _hash_messages(messages)
        params_hash = _hash_messages([params or {}])
        return self._manager.key_builder.build(
            "response",
            messages_hash,
            extra={"model": model_id, "params": params_hash},
        )
