---
title: "Compressor"
---

# Compressor

Optional value compression wired into `CacheManager`. Compresses bytes before writing to the backend and decompresses on read. Reduces memory and disk usage for large LLM responses.

## Built-in Compressors

| Class | Algorithm | Use when |
|---|---|---|
| `NoopCompressor` | None (passthrough) | Default — no overhead |
| `GzipCompressor` | gzip (Python stdlib) | Large text responses, embedding payloads |

---

## Usage

### Default (no compression)

```python
from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
)  # NoopCompressor by default
```

### Gzip compression

```python
from omnicache_ai import GzipCompressor, CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    compressor=GzipCompressor(level=6),  # 0=fastest, 9=best compression
)
```

Compression applies automatically on `manager.set()` for `bytes` values and decompresses on `manager.get()`. Non-bytes values (e.g. dicts stored directly) are passed through unchanged.

### With Redis backend (reduces network transfer)

```python
from omnicache_ai.backends.redis_backend import RedisBackend

manager = CacheManager(
    backend=RedisBackend(url="redis://localhost:6379/0"),
    key_builder=CacheKeyBuilder(),
    compressor=GzipCompressor(level=6),
)
```

---

## Custom Compressor

Implement the `Compressor` protocol — two methods required:

```python
from omnicache_ai import Compressor

class Lz4Compressor:
    def compress(self, data: bytes) -> bytes:
        import lz4.frame
        return lz4.frame.compress(data)

    def decompress(self, data: bytes) -> bytes:
        import lz4.frame
        return lz4.frame.decompress(data)

manager = CacheManager(
    backend=InMemoryBackend(),
    key_builder=CacheKeyBuilder(),
    compressor=Lz4Compressor(),
)
```

LZ4 is ~4× faster than gzip with similar compression ratios for LLM text — good for high-throughput production deployments.

---

## When to Use Compression

| Scenario | Recommendation |
|---|---|
| Short LLM responses (&lt;1KB) | `NoopCompressor` — overhead exceeds savings |
| Long LLM responses (&gt;4KB) | `GzipCompressor(level=6)` |
| Redis backend (reduces network bytes) | `GzipCompressor` |
| Disk backend (reduces storage) | `GzipCompressor` |
| Latency-critical hot path | `NoopCompressor` or LZ4 |

---

## API Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `level` (GzipCompressor) | `int` | `6` | Compression level 0–9. 0=no compression, 9=max |

`Compressor` is `@runtime_checkable` — verify with `isinstance(obj, Compressor)`.
