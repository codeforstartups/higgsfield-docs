import asyncio

import pytest

from higgsfield_companion import generate, generate_async, output_urls


def test_generate_delegates_to_official_shape() -> None:
    calls = []

    def fake_subscribe(model, *, arguments):
        calls.append((model, arguments))
        return {"status": "completed", "images": [{"url": "https://cdn.test/a.jpg"}]}

    result = generate(
        "higgsfield-ai/soul/standard",
        {"prompt": "Test"},
        subscribe=fake_subscribe,
    )

    assert calls == [("higgsfield-ai/soul/standard", {"prompt": "Test"})]
    assert output_urls(result) == ["https://cdn.test/a.jpg"]


def test_generate_rejects_unknown_model() -> None:
    with pytest.raises(ValueError, match="Unsupported catalog model"):
        generate("unknown/model", {"prompt": "Test"}, subscribe=lambda *_a, **_k: {})


def test_generate_async_delegates() -> None:
    async def fake_subscribe(model, *, arguments):
        return {"status": "completed", "video": {"url": f"https://cdn.test/{model}.mp4"}}

    result = asyncio.run(
        generate_async(
            "minimax/hailuo-2.3/standard/text-to-video",
            {"prompt": "Test"},
            subscribe_async=fake_subscribe,
        )
    )

    assert output_urls(result) == [
        "https://cdn.test/minimax/hailuo-2.3/standard/text-to-video.mp4"
    ]
