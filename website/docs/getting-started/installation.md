---
title: "Installation"
---

# Installation

## Requirements

- **Python** >= 3.12
- **Core dependencies**: `diskcache`, `numpy` (installed automatically)

---

## Install from PyPI

```bash
# Core (in-memory + disk backends)
pip install omnicache-ai

# With framework adapters
pip install 'omnicache-ai[langchain]'
pip install 'omnicache-ai[langgraph]'
pip install 'omnicache-ai[autogen]'
pip install 'omnicache-ai[crewai]'
pip install 'omnicache-ai[agno]'

# With storage backends
pip install 'omnicache-ai[redis]'
pip install 'omnicache-ai[vector-faiss]'
pip install 'omnicache-ai[vector-chroma]'

# Everything
pip install 'omnicache-ai[all]'
```

### uv

```bash
uv add omnicache-ai
uv add 'omnicache-ai[langchain,redis]'
uv add 'omnicache-ai[all]'
```

---

## From Source

```bash
git clone https://github.com/ashishpatel26/omnicache-ai.git
cd omnicache-ai
uv sync --dev
uv run pytest  # verify install
```

---

## Verify Installation

```bash
python -c "import omnicache_ai; print(omnicache_ai.__version__)"
# 0.2.0
```

---

## Optional Dependencies

| Extra | Package | What it enables |
|---|---|---|
| `redis` | `redis>=5.0` | Redis-backed distributed cache |
| `vector-faiss` | `faiss-cpu>=1.7` | FAISS vector similarity search |
| `vector-chroma` | `chromadb>=0.4` | ChromaDB persistent vector store |
| `langchain` | `langchain-core>=0.2` | LangChain `BaseCache` adapter |
| `langgraph` | `langgraph>=0.1` | LangGraph checkpoint adapter |
| `autogen` | `pyautogen>=0.2` | AutoGen 0.2.x adapter |
| `crewai` | `crewai>=0.28` | CrewAI kickoff adapter |
| `agno` | `agno>=0.1` | Agno agent adapter |
| `openai` | `openai>=1.0` | OpenAI SDK adapter |
| `anthropic` | `anthropic>=0.25` | Anthropic SDK adapter |

> **AutoGen 0.4+**: install `autogen-agentchat>=0.4` separately — it ships as its own package.

---

## Docker

```bash
docker build -t omnicache-ai .
docker run --rm omnicache-ai
```
