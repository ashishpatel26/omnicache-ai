"""Tests for AsyncInMemoryBackend."""

from __future__ import annotations

import pytest

from omnicache_ai.backends.async_memory_backend import AsyncInMemoryBackend


@pytest.fixture
def backend() -> AsyncInMemoryBackend:
    return AsyncInMemoryBackend(max_size=100)


async def test_get_miss(backend: AsyncInMemoryBackend) -> None:
    assert await backend.get("nonexistent") is None


async def test_set_and_get_roundtrip(backend: AsyncInMemoryBackend) -> None:
    await backend.set("key", b"value")
    result = await backend.get("key")
    assert result == b"value"


async def test_overwrite_key(backend: AsyncInMemoryBackend) -> None:
    await backend.set("key", b"v1")
    await backend.set("key", b"v2")
    assert await backend.get("key") == b"v2"


async def test_delete_existing_key(backend: AsyncInMemoryBackend) -> None:
    await backend.set("key", b"value")
    await backend.delete("key")
    assert await backend.get("key") is None


async def test_delete_nonexistent_key_does_not_raise(backend: AsyncInMemoryBackend) -> None:
    await backend.delete("nonexistent")


async def test_exists_true_after_set(backend: AsyncInMemoryBackend) -> None:
    await backend.set("key", b"value")
    assert await backend.exists("key") is True


async def test_exists_false_before_set(backend: AsyncInMemoryBackend) -> None:
    assert await backend.exists("key") is False


async def test_exists_false_after_delete(backend: AsyncInMemoryBackend) -> None:
    await backend.set("key", b"value")
    await backend.delete("key")
    assert await backend.exists("key") is False


async def test_clear_removes_all_entries(backend: AsyncInMemoryBackend) -> None:
    await backend.set("a", b"1")
    await backend.set("b", b"2")
    await backend.clear()

    assert await backend.get("a") is None
    assert await backend.get("b") is None


async def test_close_does_not_raise(backend: AsyncInMemoryBackend) -> None:
    await backend.close()


async def test_multiple_sequential_operations() -> None:
    backend = AsyncInMemoryBackend(max_size=100)

    for i in range(20):
        await backend.set(f"key-{i}", f"value-{i}".encode())

    for i in range(20):
        result = await backend.get(f"key-{i}")
        assert result == f"value-{i}".encode()
