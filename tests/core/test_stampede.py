"""Tests for StampedeShield."""

from __future__ import annotations

import threading
import time

import pytest

from omnicache_ai.core.stampede import StampedeShield


def test_lock_context_manager_yields_true() -> None:
    shield = StampedeShield()
    with shield.lock("key") as first:
        assert first is True


def test_different_keys_dont_block_each_other() -> None:
    shield = StampedeShield()

    results = []

    def acquire(key: str) -> None:
        with shield.lock(key):
            results.append(key)

    t1 = threading.Thread(target=acquire, args=("key-1",))
    t2 = threading.Thread(target=acquire, args=("key-2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert set(results) == {"key-1", "key-2"}


def test_same_key_serializes_access() -> None:
    shield = StampedeShield()
    order = []

    def task(name: str) -> None:
        with shield.lock("shared-key"):
            order.append(f"{name}-enter")
            time.sleep(0.01)
            order.append(f"{name}-exit")

    t1 = threading.Thread(target=task, args=("t1",))
    t2 = threading.Thread(target=task, args=("t2",))
    t1.start()
    time.sleep(0.001)  # ensure t1 acquires first
    t2.start()
    t1.join()
    t2.join()

    # Both threads completed and their critical sections didn't interleave
    assert len(order) == 4
    assert order[0] == "t1-enter"
    assert order[1] == "t1-exit"


def test_timeout_raises_timeout_error() -> None:
    shield = StampedeShield(timeout=0.05)

    acquired = threading.Event()
    released = threading.Event()

    def hold_lock() -> None:
        with shield.lock("key"):
            acquired.set()
            released.wait(timeout=2.0)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    acquired.wait()

    with pytest.raises(TimeoutError, match="key"):
        with shield.lock("key"):
            pass

    released.set()
    holder.join()


def test_lock_cleanup_after_release() -> None:
    shield = StampedeShield()

    with shield.lock("key"):
        pass

    # After release, lock is removed from internal dict
    assert "key" not in shield._locks


def test_reuse_same_key_after_release() -> None:
    shield = StampedeShield()

    with shield.lock("key") as first1:
        assert first1 is True

    with shield.lock("key") as first2:
        assert first2 is True
