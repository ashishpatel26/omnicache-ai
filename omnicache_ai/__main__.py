"""CLI entry point for omnicache-ai."""

from __future__ import annotations

import argparse
import json
import sys


def _build_manager() -> object:
    """Build a CacheManager from environment settings."""
    from omnicache_ai import CacheManager, OmnicacheSettings

    return CacheManager.from_settings(OmnicacheSettings.from_env())


def cmd_stats(_args: argparse.Namespace) -> None:
    manager = _build_manager()
    snapshot = manager.metrics.snapshot()  # type: ignore[attr-defined]
    print(json.dumps(snapshot, indent=2))


def cmd_flush(_args: argparse.Namespace) -> None:
    manager = _build_manager()
    manager.clear()  # type: ignore[attr-defined]
    print("Cache flushed.")


def cmd_inspect(args: argparse.Namespace) -> None:
    manager = _build_manager()
    exists = manager.exists(args.key)  # type: ignore[attr-defined]
    if not exists:
        print(f"Key not found: {args.key}", file=sys.stderr)
        sys.exit(1)
    raw = manager.get(args.key)  # type: ignore[attr-defined]
    info = {
        "key": args.key,
        "exists": True,
        "value_type": type(raw).__name__,
        "value_size_bytes": len(raw) if isinstance(raw, (bytes, str)) else "n/a",
    }
    print(json.dumps(info, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="omnicache",
        description="omnicache-ai — unified caching layer for AI/agent frameworks",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="Show cache hit/miss/eviction metrics")
    sub.add_parser("flush", help="Clear all cache entries")
    inspect_p = sub.add_parser("inspect", help="Inspect a cache key")
    inspect_p.add_argument("key", help="Cache key to inspect")

    args = parser.parse_args()

    if args.command == "stats":
        cmd_stats(args)
    elif args.command == "flush":
        cmd_flush(args)
    elif args.command == "inspect":
        cmd_inspect(args)


if __name__ == "__main__":
    main()
