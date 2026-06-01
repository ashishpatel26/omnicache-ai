FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY omnicache_ai/ omnicache_ai/

# Install package (no dev extras)
RUN uv sync --no-dev

# Default: show version and help
CMD ["uv", "run", "python", "-m", "omnicache_ai", "--help"]
