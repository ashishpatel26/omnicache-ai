"""Google Gemini SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    import google.generativeai as _genai  # type: ignore[import-untyped]

    _GEMINI_AVAILABLE = True
except ImportError:
    _genai = None  # type: ignore[assignment]
    _GEMINI_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class GeminiCacheAdapter:
    """Wraps Google Gemini GenerativeModel with response caching.

    Intercepts calls to ``model.generate_content`` and returns cached
    responses for identical (model name + contents + params) combinations.

    Sync usage::

        import google.generativeai as genai
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.gemini_adapter import GeminiCacheAdapter

        genai.configure(api_key="...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = GeminiCacheAdapter(model, manager)

        response = adapter.generate_content("What is the capital of France?")

    Async usage::

        response = await adapter.agenerate_content("What is the capital of France?")

    Install with: pip install 'omnicache-ai[gemini]'
    """

    def __init__(self, model: Any, manager: "CacheManager") -> None:
        if not _GEMINI_AVAILABLE:
            raise ImportError(
                "GeminiCacheAdapter requires 'google-generativeai'. "
                "Install with: pip install 'omnicache-ai[gemini]'"
            )
        self._model = model
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER
        self._model_name = getattr(model, "model_name", "gemini")

    def _build_key(self, contents: Any, kwargs: dict[str, Any]) -> str:
        content_str = json.dumps(
            contents if isinstance(contents, (list, dict)) else str(contents),
            sort_keys=True,
            default=str,
        )
        params = {k: str(v) for k, v in kwargs.items() if k != "stream"}
        return self._manager.key_builder.build(
            "response",
            content_str,
            extra={"model": self._model_name, **params},
        )

    def generate_content(self, contents: Any, **kwargs: Any) -> Any:
        """Cached synchronous generate_content."""
        key = self._build_key(contents, kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = self._model.generate_content(contents, **kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{self._model_name}"],
        )
        return response

    async def agenerate_content(self, contents: Any, **kwargs: Any) -> Any:
        """Cached async generate_content."""
        key = self._build_key(contents, kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        response = await self._model.generate_content_async(contents, **kwargs)
        self._manager.set(
            key,
            self._serializer.dumps(response),
            cache_type="response",
            tags=[f"model:{self._model_name}"],
        )
        return response

    def invalidate_model(self) -> int:
        """Invalidate all cached responses for this model."""
        return self._manager.invalidate(f"model:{self._model_name}")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)
