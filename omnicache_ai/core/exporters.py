"""Observability exporters for CacheMetrics — Prometheus and OpenTelemetry."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omnicache_ai.core.metrics import CacheMetrics

try:
    from prometheus_client import (  # type: ignore[import-untyped]
        Counter,
        Gauge,
        start_http_server,
    )

    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import metrics as _otel_metrics  # type: ignore[import-untyped]
    from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[import-untyped]
    from opentelemetry.sdk.metrics.export import (  # type: ignore[import-untyped]
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


class PrometheusExporter:
    """Exposes CacheMetrics as a Prometheus /metrics HTTP endpoint.

    Usage::

        from omnicache_ai import CacheManager, InMemoryBackend, CacheKeyBuilder
        from omnicache_ai.core.exporters import PrometheusExporter

        manager = CacheManager(backend=InMemoryBackend(), key_builder=CacheKeyBuilder())
        exporter = PrometheusExporter(manager.metrics, port=9090)
        exporter.start()  # non-blocking — scrape at localhost:9090/metrics

    Install with: pip install 'omnicache-ai[observability]'

    Args:
        metrics: CacheMetrics instance to export.
        port: HTTP port for the Prometheus scrape endpoint (default: 9090).
        namespace: Metric name prefix (default: 'omnicache').
    """

    def __init__(
        self,
        metrics: "CacheMetrics",
        port: int = 9090,
        namespace: str = "omnicache",
    ) -> None:
        if not _PROMETHEUS_AVAILABLE:
            raise ImportError(
                "PrometheusExporter requires 'prometheus-client'. "
                "Install with: pip install 'omnicache-ai[observability]'"
            )
        self._metrics = metrics
        self._port = port
        self._ns = namespace
        self._running = False
        self._thread: threading.Thread | None = None

        self._hits = Counter(f"{namespace}_cache_hits_total", "Total cache hits")
        self._misses = Counter(f"{namespace}_cache_misses_total", "Total cache misses")
        self._evictions = Counter(f"{namespace}_cache_evictions_total", "Total LRU evictions")
        self._sets = Counter(f"{namespace}_cache_sets_total", "Total cache writes")
        self._hit_rate = Gauge(f"{namespace}_cache_hit_rate", "Cache hit rate (0-1)")
        self._provider_hits = Counter(
            f"{namespace}_provider_cache_hits_total", "Provider-level prompt cache hits"
        )
        self._tokens_saved = Counter(
            f"{namespace}_tokens_saved_total", "Estimated tokens saved via provider caching"
        )
        self._cost_saved = Gauge(
            f"{namespace}_cost_saved_usd", "Estimated USD saved via provider caching"
        )

    def _sync_loop(self, interval: float = 5.0) -> None:
        import time
        from typing import cast

        prev: dict[str, int] = {}
        while self._running:
            raw_snap = self._metrics.snapshot()
            snap: dict[str, Any] = raw_snap  # type: ignore[assignment]

            def _delta(key: str) -> int:
                return int(cast(int, snap[key])) - prev.get(key, 0)

            self._hits.inc(_delta("hits"))
            self._misses.inc(_delta("misses"))
            self._evictions.inc(_delta("evictions"))
            self._sets.inc(_delta("sets"))
            self._provider_hits.inc(_delta("provider_cache_hits"))
            self._tokens_saved.inc(_delta("estimated_tokens_saved"))
            self._hit_rate.set(float(cast(float, snap["hit_rate"])))
            self._cost_saved.set(float(cast(float, snap["estimated_cost_saved_usd"])))
            prev = {
                k: int(cast(int, snap[k]))
                for k in (
                    "hits",
                    "misses",
                    "evictions",
                    "sets",
                    "provider_cache_hits",
                    "estimated_tokens_saved",
                )
            }
            time.sleep(interval)

    def start(self, sync_interval: float = 5.0) -> None:
        """Start the Prometheus HTTP server and metric sync loop (non-blocking)."""
        start_http_server(self._port)
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, args=(sync_interval,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the metric sync loop."""
        self._running = False


class OpenTelemetryExporter:
    """Pushes CacheMetrics to an OpenTelemetry collector.

    Usage::

        from omnicache_ai.core.exporters import OpenTelemetryExporter

        exporter = OpenTelemetryExporter(
            metrics=manager.metrics,
            endpoint="http://otel-collector:4317",
        )
        exporter.start()

    Install with: pip install 'omnicache-ai[observability]'

    Args:
        metrics: CacheMetrics instance to export.
        endpoint: OTLP gRPC endpoint (default: localhost:4317).
        export_interval_ms: How often to push metrics in milliseconds (default: 10000).
    """

    def __init__(
        self,
        metrics: "CacheMetrics",
        endpoint: str = "http://localhost:4317",
        export_interval_ms: int = 10_000,
    ) -> None:
        if not _OTEL_AVAILABLE:
            raise ImportError(
                "OpenTelemetryExporter requires 'opentelemetry-sdk'. "
                "Install with: pip install 'omnicache-ai[observability]'"
            )
        self._metrics = metrics
        self._endpoint = endpoint
        self._interval_ms = export_interval_ms

    def start(self) -> None:
        """Configure OTEL meter provider and register observable gauges."""
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (  # type: ignore[import-untyped]
                OTLPMetricExporter,
            )

            exporter = OTLPMetricExporter(endpoint=self._endpoint)
        except ImportError:
            exporter = ConsoleMetricExporter()

        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=self._interval_ms)
        provider = MeterProvider(metric_readers=[reader])
        _otel_metrics.set_meter_provider(provider)
        meter = provider.get_meter("omnicache_ai")

        snap_ref = {"snap": self._metrics.snapshot()}

        def _refresh(_: Any) -> None:
            snap_ref["snap"] = self._metrics.snapshot()

        meter.create_observable_gauge(
            "omnicache.hit_rate",
            callbacks=[
                lambda obs: [_otel_metrics.Observation(float(snap_ref["snap"]["hit_rate"]))]
            ],
            description="Cache hit rate (0-1)",
        )
        meter.create_observable_gauge(
            "omnicache.hits",
            callbacks=[lambda obs: [_otel_metrics.Observation(int(snap_ref["snap"]["hits"]))]],
        )
        meter.create_observable_gauge(
            "omnicache.misses",
            callbacks=[lambda obs: [_otel_metrics.Observation(int(snap_ref["snap"]["misses"]))]],
        )
        meter.create_observable_gauge(
            "omnicache.cost_saved_usd",
            callbacks=[
                lambda obs: [
                    _otel_metrics.Observation(float(snap_ref["snap"]["estimated_cost_saved_usd"]))
                ]
            ],
        )
