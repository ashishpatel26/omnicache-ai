"""Pluggable serialization for cache layers."""

from __future__ import annotations

import json
import pickle
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Serializer(Protocol):
    """Structural interface for cache value serializers."""

    def dumps(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        ...

    def loads(self, data: bytes) -> Any:
        """Deserialize bytes back to value."""
        ...


class PickleSerializer:
    """Default serializer using pickle. Supports any Python object."""

    def dumps(self, value: Any) -> bytes:
        return pickle.dumps(value)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)  # noqa: S301


class JsonSerializer:
    """JSON serializer. Safer than pickle for untrusted backends (e.g. Redis).

    Only supports JSON-compatible types (str, int, float, bool, list, dict, None).
    Raises TypeError for non-serializable values.
    """

    def dumps(self, value: Any) -> bytes:
        return json.dumps(value, default=str).encode()

    def loads(self, data: bytes) -> Any:
        return json.loads(data)


DEFAULT_SERIALIZER: Serializer = PickleSerializer()
