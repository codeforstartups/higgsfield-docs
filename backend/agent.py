from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver

from tools import fetch_website, generate_asset

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
if not os.getenv("HF_KEY"):
    key_id = os.getenv("HF_API_KEY_ID")
    secret = os.getenv("HF_API_KEY_SECRET")
    if key_id and secret:
        os.environ["HF_KEY"] = f"{key_id}:{secret}"

SYSTEM_PROMPT = """You are a marketing-agency researcher and creative partner.

Workflow:
1. Research first. If the user gives a company website, call fetch_website.
   Follow a few important same-domain pages (about, product, brand) when useful.
2. If PDFs exist under /uploads/, use ls and read_file to extract brand facts.
3. Write a concise brand brief to /brand-brief.md covering: company, audience,
   tone, visual style, proof points, and campaign angles.
4. Answer in chat with the brief highlights. Do not generate media until the
   user asks for images or video.
5. When generating, call generate_asset with a catalog model and a JSON
   arguments object. Prefer higgsfield-ai/soul/standard for stills. Use Kling
   or MiniMax only for video. Ground prompts in the brief.

Catalog models:
- higgsfield-ai/soul/standard
- kling-video/v2.5-turbo/pro/image-to-video
- kling-video/v2.5-turbo/pro/text-to-video
- kling-video/v2.5-turbo/standard/image-to-video
- minimax/hailuo-2.3/standard/image-to-video
- minimax/hailuo-2.3/standard/text-to-video
"""

checkpointer = MemorySaver()
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set in the project .env")
        _agent = create_deep_agent(
            model="openai:gpt-4.1",
            system_prompt=SYSTEM_PROMPT,
            tools=[fetch_website, generate_asset],
            checkpointer=checkpointer,
        )
    return _agent


def file_data_from_bytes(content: bytes) -> dict[str, Any]:
    return create_file_data(
        base64.b64encode(content).decode("ascii"),
        encoding="base64",
    )


def thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}
