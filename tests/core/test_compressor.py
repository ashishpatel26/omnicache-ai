"""Tests for GzipCompressor and NoopCompressor."""

from __future__ import annotations


from omnicache_ai.core.compressor import GzipCompressor, NoopCompressor


class TestNoopCompressor:
    def setup_method(self):
        self.c = NoopCompressor()

    def test_compress_returns_same_bytes(self):
        data = b"hello world"
        assert self.c.compress(data) == data

    def test_decompress_returns_same_bytes(self):
        data = b"hello world"
        assert self.c.decompress(data) == data

    def test_roundtrip(self):
        data = b"\x00\xff\xab" * 100
        assert self.c.decompress(self.c.compress(data)) == data


class TestGzipCompressor:
    def setup_method(self):
        self.c = GzipCompressor(level=6)

    def test_compress_changes_data(self):
        data = b"hello world " * 100
        compressed = self.c.compress(data)
        assert compressed != data

    def test_roundtrip(self):
        data = b"hello world " * 100
        assert self.c.decompress(self.c.compress(data)) == data

    def test_compress_reduces_size_for_repetitive_data(self):
        data = b"repeat " * 1000
        compressed = self.c.compress(data)
        assert len(compressed) < len(data)

    def test_level_0_no_compression(self):
        c = GzipCompressor(level=0)
        data = b"hello world " * 100
        assert c.decompress(c.compress(data)) == data

    def test_level_9_best_compression(self):
        c9 = GzipCompressor(level=9)
        c1 = GzipCompressor(level=1)
        data = b"repeating pattern " * 500
        # level 9 should compress at least as well as level 1
        assert len(c9.compress(data)) <= len(c1.compress(data))

    def test_empty_bytes_roundtrip(self):
        assert self.c.decompress(self.c.compress(b"")) == b""
