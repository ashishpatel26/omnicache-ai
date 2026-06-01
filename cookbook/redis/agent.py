from __future__ import annotations
from omnicache_ai.backends.redis_backend import RedisBackend
from omnicache_ai import CacheKeyBuilder, CacheManager

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    manager = CacheManager(
        backend=RedisBackend(url="redis://localhost:6379/0", key_prefix="cookbook:"),
        key_builder=CacheKeyBuilder(namespace="cookbook-redis"),
    )
    t0 = time.perf_counter()
    manager.set("redis_demo", {"status": "ok"}, ttl=120)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    val = manager.get("redis_demo")
    t3 = time.perf_counter()
    print(f"set : {t1 - t0:.6f}s")
    print(f"get : {t3 - t2:.6f}s  ({(t1 - t0) / (t3 - t2):.0f}x faster)")
    print("redis value:", val)


if __name__ == "__main__":
    main()
