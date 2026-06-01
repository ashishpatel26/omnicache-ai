"""LangGraph incident triage agent using local Ollama + omnicache-ai.

Run:
    python cookbook/langgraph/agent.py
"""

from __future__ import annotations
from omnicache_ai.adapters.langgraph_adapter import LangGraphCacheAdapter
from omnicache_ai.adapters.langchain_adapter import LangChainCacheAdapter
from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend
from langgraph.graph.message import add_messages
from langgraph.graph import END, StateGraph
from langchain_ollama import ChatOllama
from langchain_core.globals import set_llm_cache

import sys
import time
from pathlib import Path
from typing import Annotated, Any
from typing_extensions import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MODEL = "gemma3:4b"


class IncidentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    severity: str
    action_plan: str


class SafeLangGraphCacheAdapter(LangGraphCacheAdapter):
    """Sanitize non-pickleable runtime fields before persisting checkpoints."""

    @staticmethod
    def _sanitize(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None), bytes)):
            return value
        if isinstance(value, dict):
            return {
                str(k): SafeLangGraphCacheAdapter._sanitize(v)
                for k, v in value.items()
                if k != "stream_writer"
            }
        if isinstance(value, (list, tuple, set)):
            return [SafeLangGraphCacheAdapter._sanitize(v) for v in value]
        try:
            import pickle

            pickle.dumps(value)
            return value
        except Exception:
            return repr(value)

    def put(  # type: ignore[override]
        self,
        config: dict[str, Any],
        checkpoint: Any,
        metadata: Any,
        new_versions: Any = None,
    ) -> dict[str, Any]:
        import pickle
        import time as _time

        thread_id, ns, cid = self._config_parts(config)
        if not cid:
            cid = str(_time.monotonic_ns())

        safe_checkpoint = self._sanitize(checkpoint)
        safe_metadata = self._sanitize(metadata)
        safe_versions = self._sanitize(new_versions)
        safe_parent_config = self._sanitize(config)

        key = self._key(thread_id, ns, cid)
        self._manager.set(
            key,
            pickle.dumps(
                {
                    "checkpoint": safe_checkpoint,
                    "metadata": safe_metadata,
                    "parent_config": safe_parent_config,
                    "pending_writes": None,
                    "new_versions": safe_versions,
                }
            ),
            tags=[f"thread:{thread_id}"],
        )

        index_raw = self._manager.get(self._thread_list_key(thread_id))
        index: list[str] = pickle.loads(index_raw) if index_raw else []  # noqa: S301
        if cid not in index:
            index.append(cid)
        self._manager.set(self._thread_list_key(thread_id), pickle.dumps(index))

        return {
            **config,
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": cid,
                "thread_id": thread_id,
                "checkpoint_ns": ns,
            },
        }


def build_graph(llm: ChatOllama) -> StateGraph:
    def _extract_last_user_text(messages: list) -> str:
        if not messages:
            return "No incident text provided"
        last = messages[-1]
        if isinstance(last, tuple) and len(last) >= 2:
            return str(last[1])
        if isinstance(last, dict):
            return str(last.get("content", "No incident text provided"))
        return str(getattr(last, "content", str(last)))

    def classify_severity(state: IncidentState) -> IncidentState:
        messages = state.get("messages", [])
        prompt = [
            (
                "system",
                "Classify incident severity as LOW, MEDIUM, HIGH, or CRITICAL. "
                "Return only one word.",
            ),
            *messages,
        ]
        severity = llm.invoke(prompt).content.strip().upper()
        return {"severity": severity}

    def generate_action_plan(state: IncidentState) -> IncidentState:
        messages = state.get("messages", [])
        incident_report = _extract_last_user_text(messages)
        prompt = [
            (
                "system",
                "You are a senior SRE. Create a concise response plan with: "
                "Immediate containment, diagnostics, stakeholder comms, and follow-up.",
            ),
            (
                "human",
                f"Incident severity: {state.get('severity', 'UNKNOWN')}\n"
                f"Incident report: {incident_report}",
            ),
        ]
        plan = llm.invoke(prompt).content
        return {"action_plan": plan, "messages": [("assistant", plan)]}

    graph = StateGraph(IncidentState)
    graph.add_node("classify_severity", classify_severity)
    graph.add_node("generate_action_plan", generate_action_plan)
    graph.set_entry_point("classify_severity")
    graph.add_edge("classify_severity", "generate_action_plan")
    graph.add_edge("generate_action_plan", END)
    return graph


def main() -> None:
    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="cookbook-langgraph"),
    )

    # Cache all LangChain-compatible LLM calls.
    set_llm_cache(LangChainCacheAdapter(manager))

    llm = ChatOllama(model=MODEL, temperature=0)
    checkpointer = SafeLangGraphCacheAdapter(manager)
    app = build_graph(llm).compile(checkpointer=checkpointer)

    thread = {"configurable": {"thread_id": "incident-2026-03-22-001"}}
    incident_text = (
        "Payment API p95 latency jumped from 300ms to 8s after deployment. "
        "5xx error rate is now 18% in ap-south region and rising."
    )

    t0 = time.perf_counter()
    result_1 = app.invoke(
        {
            "messages": [("user", incident_text)],
            "severity": "",
            "action_plan": "",
        },
        config=thread,
    )
    t1 = time.perf_counter()
    print("=== First Run (LLM call expected) ===")
    print("Severity:", result_1["severity"])
    print("Plan:\n", result_1["action_plan"])
    print(f"Time: {t1 - t0:.3f}s")

    t2 = time.perf_counter()
    result_2 = app.invoke(
        {
            "messages": [("user", incident_text)],
            "severity": "",
            "action_plan": "",
        },
        config=thread,
    )
    t3 = time.perf_counter()
    print("\n=== Second Run (cache/checkpoint expected) ===")
    print("Severity:", result_2["severity"])
    print("Plan:\n", result_2["action_plan"])
    print(f"Time: {t3 - t2:.3f}s  ({(t1 - t0) / (t3 - t2):.0f}x faster)")


if __name__ == "__main__":
    main()
