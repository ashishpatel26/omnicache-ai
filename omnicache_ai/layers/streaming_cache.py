"""Streaming response cache — buffers streamed LLM output and caches the full result."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Generator, Iterator

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER
from omnicache_ai.layers.response_cache import _hash_messages

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager
    from omnicache_ai.core.serializer import Serializer


class StreamingResponseCache:
    """Cache layer for streaming LLM responses.

    On a cache hit, replays the previously buffered chunks as a generator so
    callers get a consistent streaming interface regardless of cache state.

    On a cache miss, transparently buffers the stream, stores the full
    response, and yields each chunk to the caller in real time.

    Sync usage::

        cache = StreamingResponseCache(manager)

        def stream_fn(messages):
            return openai_client.chat.completions.create(
                model="gpt-4o", messages=messages, stream=True
            )

        for chunk in cache.get_or_stream(messages, stream_fn, model_id="gpt-4o"):
            print(chunk.choices[0].delta.content or "", end="", flush=True)

    Async usage::

        async for chunk in cache.aget_or_stream(messages, async_stream_fn, model_id="gpt-4o"):
            print(chunk.choices[0].delta.content or "", end="", flush=True)

    Args:
        manager: Underlying CacheManager instance.
        serializer: Serializer for encoding/decoding buffered chunks (default: pickle).
        chunk_joiner: Optional callable that merges buffered chunks into a single
                      stored value. Defaults to storing the list of chunks as-is.
    """

    def __init__(
        self,
        manager: "CacheManager",
        serializer: "Serializer | None" = None,
        chunk_joiner: Callable[[list[Any]], Any] | None = None,
    ) -> None:
        self._manager = manager
        self._serializer = serializer or DEFAULT_SERIALIZER
        self._chunk_joiner = chunk_joiner

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
            extra={"model": model_id, "params": params_hash, "streaming": True},
        )

    def _store(self, key: str, chunks: list[Any], ttl: int | None, tags: list[str]) -> None:
        stored = self._chunk_joiner(chunks) if self._chunk_joiner else chunks
        self._manager.set(
            key,
            self._serializer.dumps(stored),
            ttl=ttl,
            cache_type="response",
            tags=tags,
        )

    def get_or_stream(
        self,
        messages: list[Any],
        stream_fn: Callable[[list[Any]], Iterator[Any]],
        model_id: str = "default",
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> Generator[Any, None, None]:
        """Yield cached chunks or buffer a live stream, then cache and yield.

        Args:
            messages: Conversation messages (used for cache key).
            stream_fn: Callable that returns an iterator of stream chunks.
            model_id: Model identifier used as a key discriminator.
            params: Additional generation parameters for the key.
            ttl: Cache TTL in seconds. Falls back to TTLPolicy default.
            tags: Invalidation tags. Defaults to ``['model:<model_id>']``.
        """
        key = self._build_key(messages, model_id, params)
        raw = self._manager.get(key)
        if raw is not None:
            stored = self._serializer.loads(raw)
            cached_chunks: list[Any] = stored if isinstance(stored, list) else [stored]
            yield from cached_chunks
            return

        live_chunks: list[Any] = []
        for chunk in stream_fn(messages):
            live_chunks.append(chunk)
            yield chunk

        self._store(key, live_chunks, ttl, tags or [f"model:{model_id}"])

    async def aget_or_stream(
        self,
        messages: list[Any],
        stream_fn: Callable[[list[Any]], AsyncGenerator[Any, None]],
        model_id: str = "default",
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> AsyncGenerator[Any, None]:
        """Async variant — yields cached chunks or buffers a live async stream."""
        key = self._build_key(messages, model_id, params)
        raw = self._manager.get(key)
        if raw is not None:
            stored = self._serializer.loads(raw)
            cached_chunks: list[Any] = stored if isinstance(stored, list) else [stored]
            for chunk in cached_chunks:
                yield chunk
            return

        live_chunks: list[Any] = []
        async for chunk in stream_fn(messages):
            live_chunks.append(chunk)
            yield chunk

        self._store(key, live_chunks, ttl, tags or [f"model:{model_id}"])
