---
title: "Deployment"
---

# Deployment

How to run omnicache-ai in production — Docker, Docker Compose, CI/CD, and a production checklist.

---

## Docker

A `Dockerfile` is included in the repo root. It uses a slim Python 3.12 image with `uv`.

### Build and run

```bash
docker build -t omnicache-ai .

# Show CLI help
docker run --rm omnicache-ai

# Stats (reads OMNICACHE_* env vars)
docker run --rm \
  -e OMNICACHE_BACKEND=memory \
  omnicache-ai uv run python -m omnicache_ai stats
```

### With Redis backend

```bash
docker run --rm \
  -e OMNICACHE_BACKEND=redis \
  -e OMNICACHE_REDIS_URL=redis://host.docker.internal:6379/0 \
  omnicache-ai uv run python -m omnicache_ai stats
```

---

## Docker Compose (Redis + your app)

```yaml
# docker-compose.yml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  app:
    build: .
    environment:
      OMNICACHE_BACKEND: redis
      OMNICACHE_REDIS_URL: redis://redis:6379/0
      OMNICACHE_NAMESPACE: myapp
      OMNICACHE_DEFAULT_TTL: "3600"
      OMNICACHE_TTL_RESPONSE: "600"
      OMNICACHE_TTL_EMBEDDING: "86400"
    depends_on:
      - redis
```

```bash
docker compose up -d
```

---

## GitHub Actions CI

The repo ships with CI/CD workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push/PR to `main` | Tests on 6 matrix legs (3 OS × Python 3.12/3.13), pre-commit |
| `publish.yml` | GitHub Release published | Build → TestPyPI → PyPI (OIDC) |
| `release.yml` | `git push tag v*` | Build wheel, GitHub Release, PyPI via `PYPI_TOKEN` |

No changes needed — CI runs automatically on every push.

---

## Environment Variables

All settings are driven by `OMNICACHE_*` environment variables. See [Settings](../core/settings.md) for the full list.

```bash
# Minimal production config
OMNICACHE_BACKEND=redis
OMNICACHE_REDIS_URL=redis://your-redis:6379/0
OMNICACHE_NAMESPACE=myapp-prod
OMNICACHE_DEFAULT_TTL=3600
```

Load in Python:

```python
from omnicache_ai import CacheManager, OmnicacheSettings

manager = CacheManager.from_settings(OmnicacheSettings.from_env())
```

---

## Production Checklist

### Backend

- [ ] Use `RedisBackend` or `TieredBackend` (not `InMemoryBackend`) — survives restarts, shared across workers
- [ ] Set `maxmemory` and `maxmemory-policy allkeys-lru` in Redis config
- [ ] For high read volume: `TieredBackend(l1=InMemoryBackend(), l2=RedisBackend(), l1_ttl=300)`

### Serialization & Compression

- [ ] Use `JsonSerializer` if Redis is shared across services (safer than pickle)
- [ ] Enable `GzipCompressor(level=6)` for large LLM responses stored in Redis

### TTLs

- [ ] Set per-layer TTLs appropriate to your data freshness requirements:
  - `OMNICACHE_TTL_RESPONSE=600` (10 min — LLM responses)
  - `OMNICACHE_TTL_EMBEDDING=86400` (24 h — embeddings rarely change)
  - `OMNICACHE_TTL_RETRIEVAL=3600` (1 h)
  - `OMNICACHE_TTL_CONTEXT=1800` (30 min — session data)

### Observability

- [ ] Export metrics to Prometheus or OTEL — see [Observability](../core/observability.md)
- [ ] Monitor `hit_rate` — target ≥ 0.3 in production
- [ ] Alert on `evictions` spike — means cache is too small or TTLs too long

### Security

- [ ] Scope `PYPI_TOKEN` to the specific package
- [ ] Use `JsonSerializer` if the Redis instance is accessible by untrusted clients
- [ ] Rotate API keys; never commit `.env` files

### Cache Warming

- [ ] Run `CacheWarmer.warm_from_file("hot_queries.csv", ...)` on startup for known high-traffic queries — see [CacheWarmer](../core/warmer.md)
