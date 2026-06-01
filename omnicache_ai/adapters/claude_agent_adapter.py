"""Claude Agent SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    import claude_code_sdk as _sdk  # type: ignore[import-untyped]

    _CLAUDE_SDK_AVAILABLE = True
except ImportError:
    _sdk = None  # type: ignore[assignment]
    _CLAUDE_SDK_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class ClaudeAgentCacheAdapter:
    """Wraps Claude Agent SDK runs with response caching.

    Caches results of ``claude_code_sdk.query()`` calls — the main entry
    point for Claude Code agent interactions. Ranked #2 production agent
    framework in 2026 (Alice Labs benchmark).

    Usage::

        import claude_code_sdk
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.claude_agent_adapter import ClaudeAgentCacheAdapter

        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = ClaudeAgentCacheAdapter(manager)

        messages = []
        async for msg in adapter.query("Fix the bug in app.py", options=options):
            messages.append(msg)

    Install with: pip install claude-code-sdk
    """

    def __init__(self, manager: "CacheManager") -> None:
        if not _CLAUDE_SDK_AVAILABLE:
            raise ImportError(
                "ClaudeAgentCacheAdapter requires 'claude-code-sdk'. "
                "Install with: pip install claude-code-sdk"
            )
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, prompt: str, options: Any = None) -> str:
        options_repr = (
            json.dumps(getattr(options, "__dict__", str(options)), sort_keys=True, default=str)
            if options
            else ""
        )
        return self._manager.key_builder.build(
            "response",
            prompt,
            extra={"options": options_repr[:64], "framework": "claude-agent-sdk"},
        )

    async def query(
        self,
        prompt: str,
        options: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Cached async generator wrapping claude_code_sdk.query().

        On cache hit: replays stored messages.
        On miss: collects all messages, stores, then yields.
        """
        key = self._build_key(prompt, options)
        raw = self._manager.get(key)
        if raw is not None:
            stored: list[Any] = self._serializer.loads(raw)
            for msg in stored:
                yield msg
            return

        collected: list[Any] = []
        query_kwargs: dict[str, Any] = {"prompt": prompt}
        if options is not None:
            query_kwargs["options"] = options
        query_kwargs.update(kwargs)

        async for message in _sdk.query(**query_kwargs):
            collected.append(message)
            yield message

        if collected:
            self._manager.set(
                key,
                self._serializer.dumps(collected),
                cache_type="response",
                tags=["framework:claude-agent-sdk"],
            )

    def invalidate_all(self) -> int:
        """Invalidate all cached Claude agent responses."""
        return self._manager.invalidate("framework:claude-agent-sdk")
