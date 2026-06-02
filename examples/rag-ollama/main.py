"""RAG with OpenRouter + OmniCache-AI.

Usage:
    python main.py ingest                  index data/docs.txt
    python main.py query "What is RAG?"   ask a question
    python main.py demo                    run 5 queries (2 repeats show cache hits)
    python main.py stats                   print cache metrics
"""

from __future__ import annotations

import sys
import time

# Windows cp1252 can't encode many Unicode chars returned by LLMs.
# Reconfigure stdout/stderr to UTF-8 so any answer text prints safely.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from rag.pipeline import RAGPipeline

console = Console()
DOCS_PATH = Path(__file__).parent / "data" / "docs.txt"


def cmd_ingest(rag: RAGPipeline) -> None:
    if not DOCS_PATH.exists():
        console.print(f"[red]Not found: {DOCS_PATH}[/red]")
        sys.exit(1)
    n = rag.ingest_file(str(DOCS_PATH))
    console.print(Panel(f"[green]Ingested {n} chunks[/green]"))


def cmd_query(rag: RAGPipeline, question: str) -> None:
    if not rag.is_indexed():
        console.print("[red]No docs indexed. Run: python main.py ingest[/red]")
        sys.exit(1)
    answer = rag.query(question)
    console.print(Panel(answer, title="[bold cyan]Answer[/bold cyan]", border_style="cyan"))


def cmd_demo(rag: RAGPipeline) -> None:
    if not rag.is_indexed():
        console.print("[yellow]Auto-ingesting...[/yellow]")
        cmd_ingest(rag)

    questions = [
        "What is retrieval-augmented generation?",
        "How does vector similarity search work?",
        "What are the benefits of caching in AI pipelines?",
        "What is retrieval-augmented generation?",  # repeat → cache hit
        "How does vector similarity search work?",  # repeat → cache hit
    ]

    console.print(
        Panel(
            "[bold]5 queries — last 2 are repeats to demonstrate cache hits[/bold]",
            border_style="blue",
        )
    )

    timings: list[tuple[str, float]] = []
    for q in questions:
        t0 = time.perf_counter()
        answer = rag.query(q)
        elapsed = time.perf_counter() - t0
        timings.append((q, elapsed))
        console.print(
            Panel(
                answer[:400] + ("..." if len(answer) > 400 else ""),
                title="Answer",
                border_style="dim",
            )
        )

    console.rule("[bold]Timing summary[/bold]")
    for q, t in timings:
        tag = "[green]CACHED[/green]" if t < 0.2 else "[yellow]LIVE  [/yellow]"
        console.print(f"  {tag}  {t:.3f}s  {q[:65]}")

    rag.print_stats()


def main() -> None:
    args = sys.argv[1:]
    if not args:
        console.print(__doc__)
        sys.exit(0)

    rag = RAGPipeline()
    cmd = args[0]

    if cmd == "ingest":
        cmd_ingest(rag)
    elif cmd == "query":
        if len(args) < 2:
            console.print('[red]Usage: python main.py query "question"[/red]')
            sys.exit(1)
        cmd_query(rag, " ".join(args[1:]))
    elif cmd == "demo":
        cmd_demo(rag)
    elif cmd == "stats":
        rag.print_stats()
    else:
        console.print(f"[red]Unknown: {cmd}[/red]")
        console.print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
