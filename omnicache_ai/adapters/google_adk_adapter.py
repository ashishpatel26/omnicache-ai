"""Google Agent Development Kit (ADK) cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    from google.adk.agents import Agent as _ADKAgent  # type: ignore[import-untyped]

    _ADK_AVAILABLE = True
except ImportError:
    _ADKAgent = None  # type: ignore[assignment,misc]
    _ADK_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class GoogleADKCacheAdapter:
    """Wraps a Google ADK Agent with response caching.

    Intercepts calls to ``agent.run()`` / ``agent.run_async()`` and returns
    cached responses for identical (agent name + task input) combinations.

    Usage::

        from google.adk.agents import Agent
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.google_adk_adapter import GoogleADKCacheAdapter

        agent = Agent(name="my_agent", model="gemini-2.0-flash", ...)
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        cached = GoogleADKCacheAdapter(agent, manager)

        response = cached.run("Summarise the quarterly report")
        response = await cached.arun("Summarise the quarterly report")

    Install with: pip install 'omnicache-ai[google-adk]'
    """

    def __init__(self, agent: Any, manager: "CacheManager") -> None:
        if not _ADK_AVAILABLE:
            raise ImportError(
                "GoogleADKCacheAdapter requires 'google-adk'. "
                "Install with: pip install 'omnicache-ai[google-adk]'"
            )
        self._agent = agent
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, task: Any, **kwargs: Any) -> str:
        agent_name = getattr(self._agent, "name", "adk_agent")
        content = json.dumps(
            {"task": str(task), "kwargs": {k: str(v) for k, v in kwargs.items()}},
            sort_keys=True,
        )
        return self._manager.key_builder.build("response", content, extra={"agent": agent_name})

    def run(self, task: Any, **kwargs: Any) -> Any:
        """Cached synchronous agent run."""
        key = self._build_key(task, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        result = self._agent.run(task, **kwargs)
        if result is not None:
            self._manager.set(
                key,
                self._serializer.dumps(result),
                cache_type="response",
                tags=[f"agent:{getattr(self._agent, 'name', 'adk_agent')}"],
            )
        return result

    async def arun(self, task: Any, **kwargs: Any) -> Any:
        """Cached async agent run."""
        key = self._build_key(task, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        if hasattr(self._agent, "run_async"):
            result = await self._agent.run_async(task, **kwargs)
        else:
            result = self._agent.run(task, **kwargs)
        if result is not None:
            self._manager.set(
                key,
                self._serializer.dumps(result),
                cache_type="response",
                tags=[f"agent:{getattr(self._agent, 'name', 'adk_agent')}"],
            )
        return result

    def invalidate_agent(self) -> int:
        """Invalidate all cached responses for this agent."""
        agent_name = getattr(self._agent, "name", "adk_agent")
        return self._manager.invalidate(f"agent:{agent_name}")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)
