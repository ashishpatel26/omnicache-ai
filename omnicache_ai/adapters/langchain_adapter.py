"""LangChain cache adapter."""

from __future__ import annotations

import hashlib
import pickle
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    from langchain_core.caches import BaseCache

    _LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseCache = object  # type: ignore[assignment,misc]
    _LANGCHAIN_AVAILABLE = False


class LangChainCacheAdapter(BaseCache):  # type: ignore[misc]
    """Implements langchain_core.caches.BaseCache using omnicache_ai.

    Register globally::

        from langchain_core.globals import set_llm_cache
        from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter

        set_llm_cache(LangChainCacheAdapter(cache_manager))

    Install with: pip install 'omnicache-ai[langchain]'
    """

    def __init__(self, cache_manager: "CacheManager") -> None:
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChainCacheAdapter requires 'langchain-core'. "
                "Install with: pip install 'omnicache-ai[langchain]'"
            )
        self._manager = cache_manager

    def _make_key(self, prompt: str, llm_string: str) -> str:
        digest = hashlib.sha256(f"{llm_string}:{prompt}".encode()).hexdigest()[:16]
        return f"{self._manager.key_builder._namespace}:lc:{digest}"

    def lookup(self, prompt: str, llm_string: str) -> list[Any] | None:
        key = self._make_key(prompt, llm_string)
        raw = self._manager.get(key)
        if raw is None:
            return None
        return cast(list[Any], pickle.loads(raw))  # noqa: S301

    def update(self, prompt: str, llm_string: str, return_val: list[Any]) -> None:
        key = self._make_key(prompt, llm_string)
        self._manager.set(key, pickle.dumps(return_val), cache_type="response")

    def clear(self, **kwargs: Any) -> None:
        self._manager.clear()

    async def alookup(self, prompt: str, llm_string: str) -> list[Any] | None:
        return self.lookup(prompt, llm_string)

    async def aupdate(self, prompt: str, llm_string: str, return_val: list[Any]) -> None:
        self.update(prompt, llm_string, return_val)
