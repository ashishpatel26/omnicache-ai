---
title: "Serializer"
---

# Serializer

Pluggable value encoding/decoding for all cache layers. Default is `PickleSerializer`. Switch to `JsonSerializer` for Redis backends where untrusted data may be at rest.

## Built-in Serializers

| Class | Format | Supports | Use when |
|---|---|---|---|
| `PickleSerializer` | Python pickle | Any Python object | Default — most flexible |
| `JsonSerializer` | JSON (UTF-8 bytes) | `str`, `int`, `float`, `bool`, `list`, `dict`, `None` | Redis + security-conscious deployments |

---

## Usage

### Default (pickle)

```python
from omnicache_ai import ResponseCache, CacheManager, InMemoryBackend, CacheKeyBuilder

manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
cache = ResponseCache(manager)  # uses PickleSerializer by default
```

### JSON serializer (safer for Redis)

```python
from omnicache_ai import JsonSerializer, ResponseCache

cache = ResponseCache(manager, serializer=JsonSerializer())
```

### Custom serializer

Implement the `Serializer` protocol — two methods required:

```python
from omnicache_ai import Serializer
import msgpack

class MsgpackSerializer:
    def dumps(self, value) -> bytes:
        return msgpack.packb(value)

    def loads(self, data: bytes):
        return msgpack.unpackb(data)

# Use with any layer
cache = ResponseCache(manager, serializer=MsgpackSerializer())
```

---

## Serializer Protocol

```python
from omnicache_ai import Serializer
from typing import Any

class Serializer(Protocol):
    def dumps(self, value: Any) -> bytes: ...
    def loads(self, data: bytes) -> Any: ...
```

`Serializer` is `@runtime_checkable` — verify with `isinstance(my_ser, Serializer)`.

---

## Security Note

`PickleSerializer` deserializes arbitrary Python objects. For Redis backends shared across services or exposed to untrusted input, use `JsonSerializer` to limit the attack surface. JSON is also more interoperable if you need to inspect cache values from other languages.
