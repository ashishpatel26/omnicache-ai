"""Per-request cache configuration overrides."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RequestConfig:
    """Override global cache settings for a single request.

    Pass to any cache layer ``get`` / ``set`` / ``get_or_generate`` call
    to override the global TTL, semantic threshold, or to skip the cache
    entirely for this request.

    Usage::

        from omnicache_ai.core.request_config import RequestConfig
        from omnicache_ai import ResponseCache

        cache = ResponseCache(manager)
        cfg = RequestConfig(ttl=30, skip_cache=True)  # bypass for this call

        # Or use a lower threshold for a specific query
        cfg = RequestConfig(semantic_threshold=0.80, ttl=120)

    Args:
        ttl: Override TTL in seconds for this request. None = use policy default.
        semantic_threshold: Override cosine similarity threshold for semantic
            cache lookup. None = use global threshold.
        skip_cache: If True, bypass cache entirely (no read, no write).
        tags: Additional invalidation tags to attach to this cache entry.
        namespace_prefix: Optional additional key prefix for this request
            (e.g. for per-request tenant isolation).
    """

    ttl: int | None = None
    semantic_threshold: float | None = None
    skip_cache: bool = False
    tags: list[str] = field(default_factory=list)
    namespace_prefix: str | None = None
