"""Cache warming — bulk-populate cache from queries or CSV files."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from omnicache_ai.layers.response_cache import ResponseCache


class CacheWarmer:
    """Bulk-populate the response cache from historical query logs or CSV files.

    Useful for warming a cold cache on startup using known high-traffic queries,
    reducing the number of live LLM calls in production.

    Usage::

        from omnicache_ai import ResponseCache, CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.core.warmer import CacheWarmer

        cache = ResponseCache(manager)
        warmer = CacheWarmer(cache)

        def generate(messages):
            return openai_client.chat.completions.create(
                model="gpt-4o", messages=messages
            )

        # From a list of known queries
        warmer.warm_from_queries(
            queries=["What is RAG?", "Explain semantic caching"],
            generate_fn=generate,
            model_id="gpt-4o",
        )

        # From a CSV file (column: "query")
        warmer.warm_from_file("hot_queries.csv", generate_fn=generate, model_id="gpt-4o")

    Args:
        cache: ResponseCache instance to populate.
    """

    def __init__(self, cache: "ResponseCache") -> None:
        self._cache = cache

    def warm_from_queries(
        self,
        queries: list[str],
        generate_fn: Callable[[list[Any]], Any],
        model_id: str = "default",
        ttl: int | None = None,
        skip_existing: bool = True,
    ) -> dict[str, str]:
        """Warm the cache by running generate_fn for each query.

        Args:
            queries: List of query strings to warm.
            generate_fn: Callable that accepts a messages list and returns a response.
            model_id: Model identifier for cache keying.
            ttl: TTL in seconds for cached entries. None = policy default.
            skip_existing: Skip queries already in cache (default: True).

        Returns:
            Dict mapping query → 'hit' (skipped) or 'warmed' (newly cached).
        """
        results: dict[str, str] = {}
        for query in queries:
            messages = [{"role": "user", "content": query}]
            if skip_existing and self._cache.get(messages, model_id=model_id) is not None:
                results[query] = "hit"
                continue
            response = generate_fn(messages)
            self._cache.set(messages, response, model_id=model_id, ttl=ttl)
            results[query] = "warmed"
        return results

    async def awarm_from_queries(
        self,
        queries: list[str],
        generate_fn: Callable[[list[Any]], Any],
        model_id: str = "default",
        ttl: int | None = None,
        skip_existing: bool = True,
    ) -> dict[str, str]:
        """Async variant of warm_from_queries."""
        import asyncio

        results: dict[str, str] = {}
        for query in queries:
            messages = [{"role": "user", "content": query}]
            if skip_existing and self._cache.get(messages, model_id=model_id) is not None:
                results[query] = "hit"
                continue
            if asyncio.iscoroutinefunction(generate_fn):
                response = await generate_fn(messages)
            else:
                response = generate_fn(messages)
            self._cache.set(messages, response, model_id=model_id, ttl=ttl)
            results[query] = "warmed"
        return results

    def warm_from_file(
        self,
        path: str,
        generate_fn: Callable[[list[Any]], Any],
        model_id: str = "default",
        ttl: int | None = None,
        query_column: str = "query",
        skip_existing: bool = True,
    ) -> dict[str, str]:
        """Warm the cache from a CSV file.

        The CSV must have a column named ``query_column`` (default: 'query').
        Each row's query is warmed individually.

        Args:
            path: Path to the CSV file.
            generate_fn: Callable that accepts a messages list and returns a response.
            model_id: Model identifier for cache keying.
            ttl: TTL in seconds. None = policy default.
            query_column: Name of the CSV column containing queries.
            skip_existing: Skip queries already cached (default: True).

        Returns:
            Dict mapping query → 'hit' or 'warmed'.
        """
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            queries = [row[query_column] for row in reader if query_column in row]
        return self.warm_from_queries(queries, generate_fn, model_id, ttl, skip_existing)
