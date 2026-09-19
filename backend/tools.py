from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx
from langchain.tools import tool

from higgsfield_companion import SUPPORTED_MODELS, generate_async, output_urls

MAX_PAGE_CHARS = 24_000
MAX_BYTES = 1_000_000


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        joined = " ".join(self._chunks)
        return re.sub(r"[ \t]+", " ", re.sub(r"\n+", "\n", joined)).strip()


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


@tool
def fetch_website(url: str) -> str:
    """Fetch a public company web page and return readable text.

    Use this to research a brand from its website. Call again for important
    same-domain pages (about, products, pricing) discovered in the first page.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "Invalid URL. Provide an http or https address."

    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as client:
            response = client.get(
                url,
                headers={"User-Agent": "marketing-agency-research-agent/1.0"},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Failed to fetch {url}: {exc}"

    content_type = response.headers.get("content-type", "")
    body = response.content[:MAX_BYTES]
    if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
        return (
            "This URL points to a PDF. Ask the user to upload it in the workspace "
            "so it can be read with the filesystem tools."
        )

    text = body.decode(response.encoding or "utf-8", errors="replace")
    if "html" in content_type.lower() or "<html" in text[:500].lower():
        text = _html_to_text(text)
    if len(text) > MAX_PAGE_CHARS:
        text = text[:MAX_PAGE_CHARS] + "\n...[truncated]"
    return f"URL: {response.url}\n\n{text or '(no readable text)'}"


@tool
async def generate_asset(model: str, arguments_json: str) -> str:
    """Generate an image or video with Higgsfield after researching the brand.

    `model` must be one of the catalog ids. `arguments_json` is a JSON object
    with at least `prompt`. Image-to-video models also need `image_url`.
    Only call this when the user wants creative assets, not during research.
    """
    if model not in SUPPORTED_MODELS:
        choices = ", ".join(SUPPORTED_MODELS)
        return f"Unsupported model {model!r}. Choose one of: {choices}"
    try:
        arguments: dict[str, Any] = json.loads(arguments_json)
    except json.JSONDecodeError as exc:
        return f"arguments_json must be valid JSON: {exc}"
    if not isinstance(arguments, dict):
        return "arguments_json must be a JSON object."

    try:
        result = await generate_async(model, arguments)
    except Exception as exc:  # noqa: BLE001 - surface SDK/API errors to the agent
        return f"Generation failed: {exc}"

    urls = output_urls(result)
    payload = {
        "status": result.get("status"),
        "request_id": result.get("request_id"),
        "urls": urls,
        "raw": {k: result[k] for k in ("error", "images", "video") if k in result},
    }
    return json.dumps(payload)
