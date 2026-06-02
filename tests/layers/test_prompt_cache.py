"""Tests for PromptCacheLayer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from omnicache_ai.core.metrics import CacheMetrics
from omnicache_ai.layers.prompt_cache import PromptCacheLayer


@pytest.fixture
def metrics() -> CacheMetrics:
    return CacheMetrics()


@pytest.fixture
def layer(metrics: CacheMetrics) -> PromptCacheLayer:
    return PromptCacheLayer(metrics=metrics, min_chars_to_cache=100)


def _make_anthropic_response(cache_read_tokens: int = 0) -> MagicMock:
    usage = MagicMock()
    usage.cache_read_input_tokens = cache_read_tokens
    resp = MagicMock()
    resp.usage = usage
    return resp


def _make_openai_response(cached_tokens: int = 0) -> MagicMock:
    details = MagicMock()
    details.cached_tokens = cached_tokens
    usage = MagicMock()
    usage.prompt_tokens_details = details
    resp = MagicMock()
    resp.usage = usage
    return resp


# --- Cache control injection ---


def test_short_system_prompt_not_injected(layer: PromptCacheLayer) -> None:
    result = layer._inject_anthropic_cache("Short prompt")
    assert result == "Short prompt"


def test_long_system_prompt_injected(layer: PromptCacheLayer) -> None:
    long_prompt = "x" * 200
    result = layer._inject_anthropic_cache(long_prompt)
    assert isinstance(result, list)
    assert result[0]["cache_control"] == {"type": "ephemeral"}
    assert result[0]["text"] == long_prompt


def test_list_system_prompt_not_modified(layer: PromptCacheLayer) -> None:
    existing = [{"type": "text", "text": "already a list"}]
    result = layer._inject_anthropic_cache(existing)
    assert result == existing


def test_none_system_prompt_returns_none(layer: PromptCacheLayer) -> None:
    result = layer._inject_anthropic_cache(None)
    assert result is None


# --- anthropic_create ---


def test_anthropic_create_calls_client(layer: PromptCacheLayer) -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_anthropic_response()

    layer.anthropic_create(client, model="claude-sonnet-4-6", max_tokens=100, messages=[])

    client.messages.create.assert_called_once()


def test_anthropic_create_injects_cache_control_for_long_prompt(layer: PromptCacheLayer) -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_anthropic_response()
    long_system = "x" * 200

    layer.anthropic_create(
        client,
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[],
        system=long_system,
    )

    call_kwargs = client.messages.create.call_args[1]
    assert isinstance(call_kwargs["system"], list)
    assert call_kwargs["system"][0]["cache_control"]["type"] == "ephemeral"


def test_anthropic_create_records_savings_on_cache_read(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_anthropic_response(cache_read_tokens=1000)

    layer.anthropic_create(client, model="claude-sonnet-4-6", max_tokens=100, messages=[])

    assert metrics.provider_cache_hits == 1
    assert metrics.estimated_tokens_saved == 1000
    assert metrics.estimated_cost_saved_usd > 0


def test_anthropic_create_no_savings_on_cache_miss(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.messages.create.return_value = _make_anthropic_response(cache_read_tokens=0)

    layer.anthropic_create(client, model="claude-sonnet-4-6", max_tokens=100, messages=[])

    assert metrics.provider_cache_hits == 0
    assert metrics.estimated_cost_saved_usd == 0


async def test_anthropic_acreate_records_savings(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_anthropic_response(cache_read_tokens=500))

    await layer.anthropic_acreate(client, model="claude-sonnet-4-6", max_tokens=100, messages=[])

    assert metrics.provider_cache_hits == 1


# --- openai_create ---


def test_openai_create_calls_client(layer: PromptCacheLayer) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _make_openai_response()

    layer.openai_create(client, model="gpt-4o", messages=[])

    client.chat.completions.create.assert_called_once()


def test_openai_create_records_savings_on_cache_hit(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _make_openai_response(cached_tokens=2000)

    layer.openai_create(client, model="gpt-4o", messages=[])

    assert metrics.provider_cache_hits == 1
    assert metrics.estimated_tokens_saved == 2000
    assert metrics.estimated_cost_saved_usd > 0


def test_openai_create_no_savings_on_cache_miss(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _make_openai_response(cached_tokens=0)

    layer.openai_create(client, model="gpt-4o", messages=[])

    assert metrics.provider_cache_hits == 0


async def test_openai_acreate_records_savings(
    layer: PromptCacheLayer, metrics: CacheMetrics
) -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=_make_openai_response(cached_tokens=1500)
    )

    await layer.openai_acreate(client, model="gpt-4o", messages=[])

    assert metrics.provider_cache_hits == 1


def test_layer_works_without_metrics() -> None:
    layer = PromptCacheLayer(metrics=None, min_chars_to_cache=10)
    client = MagicMock()
    client.messages.create.return_value = _make_anthropic_response(cache_read_tokens=500)

    # Should not raise even without metrics
    layer.anthropic_create(client, model="claude-sonnet-4-6", max_tokens=100, messages=[])
