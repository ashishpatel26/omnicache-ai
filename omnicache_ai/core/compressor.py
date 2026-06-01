"""Optional compression layer for cache values."""

from __future__ import annotations

import gzip
from typing import Protocol, runtime_checkable


@runtime_checkable
class Compressor(Protocol):
    """Structural interface for value compressors."""

    def compress(self, data: bytes) -> bytes:
        """Compress bytes."""
        ...

    def decompress(self, data: bytes) -> bytes:
        """Decompress bytes."""
        ...


class NoopCompressor:
    """Pass-through compressor (no compression). Default."""

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, data: bytes) -> bytes:
        return data


class GzipCompressor:
    """Gzip compressor. Best for large text responses (LLM outputs, docs).

    Args:
        level: Compression level 0-9. 6 is the default (balanced speed/ratio).
    """

    def __init__(self, level: int = 6) -> None:
        self._level = level

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self._level)

    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)


DEFAULT_COMPRESSOR: Compressor = NoopCompressor()
