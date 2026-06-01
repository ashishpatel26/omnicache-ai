"""OpenAI Agents SDK cache adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.cache_manager import CacheManager

try:
    from agents import Runner as _Runner  # type: ignore[import-untyped]

    _OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    _Runner = None  # type: ignore[assignment,misc]
    _OPENAI_AGENTS_AVAILABLE = False

from omnicache_ai.core.serializer import DEFAULT_SERIALIZER


class OpenAIAgentsCacheAdapter:
    """Wraps OpenAI Agents SDK Runner with response caching.

    Intercepts ``Runner.run()`` / ``Runner.run_async()`` and returns cached
    results for identical (agent + input) combinations.

    Usage::

        from agents import Agent, Runner
        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.adapters.openai_agents_adapter import OpenAIAgentsCacheAdapter

        agent = Agent(name="assistant", instructions="You are a helpful assistant")
        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        adapter = OpenAIAgentsCacheAdapter(manager)

        result = adapter.run(agent, "What is 2+2?")
        result = await adapter.arun(agent, "What is 2+2?")

    Install with: pip install openai-agents
    """

    def __init__(self, manager: "CacheManager") -> None:
        if not _OPENAI_AGENTS_AVAILABLE:
            raise ImportError(
                "OpenAIAgentsCacheAdapter requires 'openai-agents'. "
                "Install with: pip install openai-agents"
            )
        self._manager = manager
        self._serializer = DEFAULT_SERIALIZER

    def _build_key(self, agent: Any, input_text: str, **kwargs: Any) -> str:
        agent_name = getattr(agent, "name", "openai_agent")
        model = getattr(agent, "model", "default")
        content = json.dumps(
            {"input": input_text, "kwargs": {k: str(v) for k, v in kwargs.items()}},
            sort_keys=True,
        )
        return self._manager.key_builder.build(
            "response", content, extra={"agent": agent_name, "model": model}
        )

    def run(self, agent: Any, input_text: str, **kwargs: Any) -> Any:
        """Cached synchronous Runner.run()."""
        key = self._build_key(agent, input_text, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        result = _Runner.run_sync(agent, input_text, **kwargs)
        if result is not None:
            agent_name = getattr(agent, "name", "openai_agent")
            self._manager.set(
                key,
                self._serializer.dumps(result),
                cache_type="response",
                tags=[f"agent:{agent_name}"],
            )
        return result

    async def arun(self, agent: Any, input_text: str, **kwargs: Any) -> Any:
        """Cached async Runner.run()."""
        key = self._build_key(agent, input_text, **kwargs)
        raw = self._manager.get(key)
        if raw is not None:
            return self._serializer.loads(raw)
        result = await _Runner.run(agent, input_text, **kwargs)
        if result is not None:
            agent_name = getattr(agent, "name", "openai_agent")
            self._manager.set(
                key,
                self._serializer.dumps(result),
                cache_type="response",
                tags=[f"agent:{agent_name}"],
            )
        return result

    def invalidate_agent(self, agent: Any) -> int:
        """Invalidate all cached responses for a specific agent."""
        agent_name = getattr(agent, "name", "openai_agent")
        return self._manager.invalidate(f"agent:{agent_name}")
