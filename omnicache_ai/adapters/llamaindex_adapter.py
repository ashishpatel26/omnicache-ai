"""LlamaIndex cache adapter — LLM + QueryEngine caching."""

from __future__ import annotations

import hashlib
import json
import pickle
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    from llama_index.core.llms import LLM as _LlamaLLM  # type: ignore[import-untyped]
    from llama_index.core.llms import (  # type: ignore[import-untyped]
        ChatMessage,
        ChatResponse,
        CompletionResponse,
        LLMMetadata,
    )

    _LLAMAINDEX_AVAILABLE = True
except ImportError:
    _LlamaLLM = object  # type: ignore[assignment,misc]
    ChatMessage = None  # type: ignore[assignment]
    ChatResponse = None  # type: ignore[assignment]
    CompletionResponse = None  # type: ignore[assignment]
    LLMMetadata = None  # type: ignore[assignment]
    _LLAMAINDEX_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


class LlamaIndexLLMCacheAdapter(_LlamaLLM):  # type: ignore[misc]
    """LlamaIndex LLM adapter that caches chat and completion responses.

    Drop-in replacement for any LlamaIndex LLM. Wraps the underlying model
    and returns cached responses for identical inputs.

    Usage::

        from llama_index.llms.openai import OpenAI
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexLLMCacheAdapter

        llm = OpenAI(model="gpt-4o")
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        cached_llm = LlamaIndexLLMCacheAdapter(llm, manager)

        # Use cached_llm anywhere a LlamaIndex LLM is accepted
        response = cached_llm.complete("What is 2+2?")

    Install with: pip install 'omnicache-ai[llamaindex]'
    """

    def __init__(self, llm: Any, manager: "CacheManager") -> None:
        if not _LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndexLLMCacheAdapter requires 'llama-index-core'. "
                "Install with: pip install 'omnicache-ai[llamaindex]'"
            )
        self._llm = llm
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    @property
    def metadata(self) -> Any:
        return self._llm.metadata

    def _key_complete(self, prompt: str, **kwargs: Any) -> str:
        return self._manager.key_builder.build(
            "response",
            _hash({"prompt": prompt, "kwargs": kwargs}),
            extra={"model": getattr(self._llm, "model", "default"), "type": "complete"},
        )

    def _key_chat(self, messages: list[Any], **kwargs: Any) -> str:
        msgs = [str(m) for m in messages]
        return self._manager.key_builder.build(
            "response",
            _hash({"messages": msgs, "kwargs": kwargs}),
            extra={"model": getattr(self._llm, "model", "default"), "type": "chat"},
        )

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        key = self._key_complete(prompt, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, self._serializer.loads(raw))
        result = self._llm.complete(prompt, **kwargs)
        self._manager.set(key, self._serializer.dumps(result), cache_type="response")
        return result

    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        key = self._key_complete(prompt, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, self._serializer.loads(raw))
        result = await self._llm.acomplete(prompt, **kwargs)
        self._manager.set(key, self._serializer.dumps(result), cache_type="response")
        return result

    def chat(self, messages: list[Any], **kwargs: Any) -> Any:
        key = self._key_chat(messages, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, self._serializer.loads(raw))
        result = self._llm.chat(messages, **kwargs)
        self._manager.set(key, self._serializer.dumps(result), cache_type="response")
        return result

    async def achat(self, messages: list[Any], **kwargs: Any) -> Any:
        key = self._key_chat(messages, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, self._serializer.loads(raw))
        result = await self._llm.achat(messages, **kwargs)
        self._manager.set(key, self._serializer.dumps(result), cache_type="response")
        return result

    def stream_complete(self, prompt: str, **kwargs: Any) -> Any:
        return self._llm.stream_complete(prompt, **kwargs)

    def stream_chat(self, messages: list[Any], **kwargs: Any) -> Any:
        return self._llm.stream_chat(messages, **kwargs)

    async def astream_complete(self, prompt: str, **kwargs: Any) -> Any:
        async for chunk in self._llm.astream_complete(prompt, **kwargs):
            yield chunk

    async def astream_chat(self, messages: list[Any], **kwargs: Any) -> Any:
        async for chunk in self._llm.astream_chat(messages, **kwargs):
            yield chunk


class LlamaIndexQueryCacheAdapter:
    """Caches LlamaIndex QueryEngine responses.

    Usage::

        from llama_index.core import VectorStoreIndex
        from omnicache_ai.adapters.llamaindex_adapter import LlamaIndexQueryCacheAdapter

        index = VectorStoreIndex.from_documents(docs)
        engine = index.as_query_engine()
        cached_engine = LlamaIndexQueryCacheAdapter(engine, manager)

        response = cached_engine.query("What is RAG?")
    """

    def __init__(self, query_engine: Any, manager: "CacheManager") -> None:
        if not _LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndexQueryCacheAdapter requires 'llama-index-core'. "
                "Install with: pip install 'omnicache-ai[llamaindex]'"
            )
        self._engine = query_engine
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, query: str) -> str:
        return self._manager.key_builder.build("retrieval", query)

    def query(self, query: str, **kwargs: Any) -> Any:
        key = self._build_key(query)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, pickle.loads(raw))  # noqa: S301
        result = self._engine.query(query, **kwargs)
        self._manager.set(key, pickle.dumps(result), cache_type="retrieval")
        return result

    async def aquery(self, query: str, **kwargs: Any) -> Any:
        key = self._build_key(query)
        raw = self._manager.get(key)
        if raw is not None:
            return cast(Any, pickle.loads(raw))  # noqa: S301
        result = await self._engine.aquery(query, **kwargs)
        self._manager.set(key, pickle.dumps(result), cache_type="retrieval")
        return result
