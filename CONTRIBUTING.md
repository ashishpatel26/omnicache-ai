# Contributing to omnicache-ai

Thank you for your interest in contributing. This document covers everything you need to get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Adding a New Backend](#adding-a-new-backend)
- [Adding a New Adapter](#adding-a-new-adapter)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

---

## Ways to Contribute

- **Bug reports** — open an issue using the Bug Report template
- **Feature requests** — open an issue using the Feature Request template
- **Documentation** — fix typos, improve examples, add recipes
- **Bug fixes** — pick an issue labeled `good first issue` or `bug`
- **New backends** — add support for Qdrant, Weaviate, Pinecone, etc.
- **New adapters** — add support for new AI frameworks
- **Performance** — profiling, benchmarks, optimization PRs

---

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Clone and install

```bash
git clone https://github.com/ashishpatel26/omnicache-ai.git
cd omnicache-ai

# Install all dev dependencies
uv sync --dev

# Install pre-commit hooks (runs on every commit automatically)
uv run pre-commit install

# Verify everything works
uv run pytest
```

---

## Making Changes

1. **Fork** the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   # or
   git checkout -b fix/my-bug
   ```

2. **Make your changes** following the coding standards below.

3. **Add tests** — PRs without tests for new functionality will not be merged.

4. **Run the full check suite** before pushing:
   ```bash
   uv run pre-commit run --all-files   # lint + format + mypy
   uv run pytest --cov=omnicache_ai    # tests + coverage
   ```

5. **Commit** with a clear message (conventional commits preferred):
   ```
   feat: add QdrantBackend vector store
   fix: FAISSBackend.delete() now removes vector from index
   docs: add Redis cookbook example
   test: add async backend coverage
   ```

6. **Push and open a PR** against `main`.

---

## Pull Request Process

- Fill out the PR template completely
- Link the issue your PR resolves (e.g. `Closes #42`)
- Keep PRs focused — one feature or fix per PR
- All CI checks must pass before merge
- At least one maintainer review required
- Squash-merge preferred for feature branches

---

## Coding Standards

### Style

- **Formatter**: `ruff format` (line length 100)
- **Linter**: `ruff check`
- **Type checker**: `mypy` in strict mode scoped to `omnicache_ai/`
- All enforced automatically via pre-commit

### Rules

- All public functions/classes must have type annotations
- No `Any` without justification
- No `# type: ignore` without a comment explaining why
- No `pickle` without `# noqa: S301` (acknowledged security trade-off)
- No comments explaining *what* the code does — only *why* (hidden constraints, workarounds)
- No dead code, no backwards-compat shims unless explicitly required

### Protocols over inheritance

New backends and serializers implement the structural `Protocol` interfaces — no inheritance from base classes required.

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=omnicache_ai --cov-report=term-missing

# Run a specific test file
uv run pytest tests/layers/test_response_cache.py -v

# Run a specific test by name
uv run pytest -k "test_cache_hit" -v
```

### Test conventions

- Tests live in `tests/` mirroring the `omnicache_ai/` structure
- Use fixtures from `tests/conftest.py` (`backend`, `cache_manager`, `mock_embed`)
- `asyncio_mode = "auto"` — async tests need no decorator
- Mock external services (Redis, FAISS) — do not require running infrastructure for unit tests
- Integration tests for optional backends go in `tests/backends/test_<name>_backend.py`

---

## Adding a New Backend

1. Create `omnicache_ai/backends/<name>_backend.py`
2. Implement `CacheBackend` protocol (or `VectorBackend` for vector stores):
   ```python
   class MyBackend:
       def get(self, key: str) -> Any | None: ...
       def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
       def delete(self, key: str) -> None: ...
       def exists(self, key: str) -> bool: ...
       def clear(self) -> None: ...
       def close(self) -> None: ...
   ```
3. Guard optional imports with `try/except ImportError`
4. Add the extra to `pyproject.toml` under `[project.optional-dependencies]`
5. Add tests in `tests/backends/test_<name>_backend.py`
6. Document in `website/docs/backends/<name>.md`

---

## Adding a New Adapter

1. Create `omnicache_ai/adapters/<framework>_adapter.py`
2. Guard framework import with `try/except ImportError` and a `_AVAILABLE` flag
3. Raise `ImportError` with install instructions in `__init__` if framework missing
4. Add the extra to `pyproject.toml`
5. Add tests in `tests/adapters/test_<framework>_adapter.py`
6. Document in `website/docs/adapters/<framework>.md`

---

## Questions?

Open a [Discussion](https://github.com/ashishpatel26/omnicache-ai/discussions) or reach out at **ashishpatel.ce.2011@gmail.com**.
