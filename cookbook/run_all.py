#!/usr/bin/env python3
"""Run all cookbook examples that work without optional extras.

Usage:
    uv run python cookbook/run_all.py          # run all baseline examples
    uv run python cookbook/run_all.py --full   # include framework examples (needs Ollama)
    uv run python cookbook/run_all.py --all    # include optional-dep examples (redis, etc.)
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field


@dataclass
class Example:
    module: str
    label: str
    requires: list[str] = field(default_factory=list)
    tier: str = "base"  # base | framework | optional


EXAMPLES = [
    # ── Tier 1: no external deps (always run) ──────────────────────────────
    Example("cookbook.core.agent", "Core: ResponseCache + EmbeddingCache", tier="base"),
    Example("cookbook.ttl.agent", "TTL: per-type retention policy", tier="base"),
    Example("cookbook.invalidation.agent", "Invalidation: tag-based bulk eviction", tier="base"),
    # ── Tier 2: framework adapters (need Ollama + gemma3:4b) ───────────────
    Example(
        "cookbook.langchain.agent",
        "LangChain: support assistant chain",
        requires=["langchain_ollama"],
        tier="framework",
    ),
    Example(
        "cookbook.langgraph.agent",
        "LangGraph: incident triage graph",
        requires=["langgraph"],
        tier="framework",
    ),
    Example(
        "cookbook.autogen.agent",
        "AutoGen: async assistant",
        requires=["autogen_agentchat"],
        tier="framework",
    ),
    Example(
        "cookbook.crewai.agent",
        "CrewAI: release planning crew",
        requires=["crewai", "litellm"],
        tier="framework",
    ),
    Example(
        "cookbook.agno.agent", "Agno: deployment risk analyst", requires=["agno"], tier="framework"
    ),
    Example(
        "cookbook.a2a.agent",
        "A2A: planner-executor-reviewer",
        requires=["langchain_ollama"],
        tier="framework",
    ),
    Example(
        "cookbook.multi_framework.agent",
        "Multi-Framework: LangChain + A2A",
        requires=["langchain_ollama"],
        tier="framework",
    ),
    # ── Tier 3: optional backends (need extra packages) ────────────────────
    Example(
        "cookbook.semantic_cache.agent",
        "Semantic Cache: FAISS + Ollama embed",
        requires=["faiss", "langchain_ollama"],
        tier="optional",
    ),
    Example("cookbook.redis.agent", "Redis: shared backend", requires=["redis"], tier="optional"),
]


def _check_imports(requires: list[str]) -> str | None:
    """Return missing package name or None if all present."""
    for pkg in requires:
        try:
            __import__(pkg)
        except ImportError:
            return pkg
    return None


def run_example(ex: Example) -> tuple[bool, str]:
    missing = _check_imports(ex.requires)
    if missing:
        return False, f"SKIP  (missing: {missing})"

    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", ex.module],
        capture_output=True,
        text=True,
        timeout=600,
    )
    elapsed = time.monotonic() - start

    if result.returncode == 0:
        return True, f"OK    ({elapsed:.1f}s)"
    else:
        lines = (result.stderr or result.stdout or "").strip().splitlines()
        last = lines[-1] if lines else "unknown error"
        return False, f"FAIL  ({elapsed:.1f}s) — {last}"


def main() -> None:
    args = sys.argv[1:]
    run_framework = "--full" in args or "--all" in args
    run_optional = "--all" in args

    tiers = {"base"}
    if run_framework:
        tiers.add("framework")
    if run_optional:
        tiers.add("optional")

    selected = [e for e in EXAMPLES if e.tier in tiers]

    print(f"\nomnicache-ai cookbook -- running {len(selected)} examples\n{'-' * 60}")

    passed = failed = skipped = 0
    for ex in selected:
        print(f"  {ex.label:<52}", end="", flush=True)
        ok, msg = run_example(ex)
        print(msg)
        if "SKIP" in msg:
            skipped += 1
        elif ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'-' * 60}")
    print(f"  passed={passed}  failed={failed}  skipped={skipped}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
