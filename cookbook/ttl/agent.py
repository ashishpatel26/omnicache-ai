from __future__ import annotations
from omnicache_ai import CacheKeyBuilder, CacheManager, InMemoryBackend, TTLPolicy

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    manager = CacheManager(
        backend=InMemoryBackend(),
        key_builder=CacheKeyBuilder(namespace="cookbook-ttl"),
        ttl_policy=TTLPolicy(default_ttl=60, per_type={"response": 10, "embed": 3600}),
    )
    t0 = time.perf_counter()
    manager.set("demo", "ok", cache_type="response")
    t1 = time.perf_counter()
    t2 = time.perf_counter()
    val = manager.get("demo")
    t3 = time.perf_counter()
    print(f"set : {t1 - t0:.6f}s")
    print(f"get : {t3 - t2:.6f}s  ({(t1 - t0) / (t3 - t2):.0f}x faster)")
    print("stored key with response ttl policy, value:", val)


if __name__ == "__main__":
    main()
