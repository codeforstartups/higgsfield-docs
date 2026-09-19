from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Literal, cast

ModelId = Literal[
    "higgsfield-ai/soul/standard",
    "kling-video/v2.5-turbo/pro/image-to-video",
    "kling-video/v2.5-turbo/pro/text-to-video",
    "kling-video/v2.5-turbo/standard/image-to-video",
    "minimax/hailuo-2.3/standard/image-to-video",
    "minimax/hailuo-2.3/standard/text-to-video",
]

SUPPORTED_MODELS: tuple[ModelId, ...] = (
    "higgsfield-ai/soul/standard",
    "kling-video/v2.5-turbo/pro/image-to-video",
    "kling-video/v2.5-turbo/pro/text-to-video",
    "kling-video/v2.5-turbo/standard/image-to-video",
    "minimax/hailuo-2.3/standard/image-to-video",
    "minimax/hailuo-2.3/standard/text-to-video",
)

Result = Mapping[str, Any]
Subscribe = Callable[..., Result]
SubscribeAsync = Callable[..., Awaitable[Result]]


def _official_subscribe() -> Subscribe:
    import higgsfield_client

    return cast(Subscribe, higgsfield_client.subscribe)


def _official_subscribe_async() -> SubscribeAsync:
    import higgsfield_client

    return cast(SubscribeAsync, higgsfield_client.subscribe_async)


def _validate_model(model: str) -> ModelId:
    if model not in SUPPORTED_MODELS:
        choices = ", ".join(SUPPORTED_MODELS)
        raise ValueError(f"Unsupported catalog model {model!r}. Choose one of: {choices}")
    return cast(ModelId, model)


def generate(
    model: ModelId,
    arguments: Mapping[str, Any],
    *,
    subscribe: Subscribe | None = None,
) -> Result:
    """Submit a generation and wait using the official synchronous SDK."""
    selected_model = _validate_model(model)
    runner = subscribe or _official_subscribe()
    return runner(selected_model, arguments=dict(arguments))


async def generate_async(
    model: ModelId,
    arguments: Mapping[str, Any],
    *,
    subscribe_async: SubscribeAsync | None = None,
) -> Result:
    """Submit a generation and wait using the official asynchronous SDK."""
    selected_model = _validate_model(model)
    runner = subscribe_async or _official_subscribe_async()
    return await runner(selected_model, arguments=dict(arguments))


def output_urls(result: Mapping[str, Any]) -> list[str]:
    """Collect image, video, and audio URLs from a completed SDK result."""
    urls: list[str] = []
    for collection_name in ("images", "audios"):
        for item in result.get(collection_name, []) or []:
            if isinstance(item, Mapping) and isinstance(item.get("url"), str):
                urls.append(item["url"])

    for item_name in ("video", "audio"):
        item = result.get(item_name)
        if isinstance(item, Mapping) and isinstance(item.get("url"), str):
            urls.append(item["url"])
    return urls
