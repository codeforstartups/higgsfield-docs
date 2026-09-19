from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from agent import file_data_from_bytes, get_agent, thread_config

thread_files: dict[str, dict[str, Any]] = {}
app = FastAPI(title="Campaign workspace")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    company_url: str | None = None


def _safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not cleaned.lower().endswith(".pdf"):
        cleaned += ".pdf"
    return cleaned or "upload.pdf"


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
            elif hasattr(block, "text"):
                parts.append(str(getattr(block, "text")))
        return "".join(parts)
    return str(content or "")


def _assets_from_tool_content(content: str) -> list[str]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    urls = payload.get("urls")
    if isinstance(urls, list):
        return [u for u in urls if isinstance(u, str)]
    return []


@app.get("/health")
def health() -> dict[str, str]:
    openai = "set" if os.getenv("OPENAI_API_KEY") else "missing"
    hf = "set" if (os.getenv("HF_KEY") or os.getenv("HF_API_KEY_ID")) else "missing"
    return {"status": "ok", "openai": openai, "higgsfield": hf}


@app.post("/upload")
async def upload(thread_id: str = Form(...), file: UploadFile = File(...)) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > 8_000_000:
        raise HTTPException(status_code=400, detail="PDF must be under 8MB")

    path = f"/uploads/{_safe_filename(file.filename)}"
    thread_files.setdefault(thread_id, {})[path] = file_data_from_bytes(data)
    return {"path": path, "thread_id": thread_id}


@app.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    user_text = body.message.strip()
    if body.company_url:
        user_text = (
            f"{user_text}\n\nCompany website to research: {body.company_url.strip()}"
        )

    async def events() -> AsyncIterator[str]:
        collected_assets: list[str] = []
        final_text = ""
        payload: dict[str, Any] = {
            "messages": [{"role": "user", "content": user_text}],
        }
        files = thread_files.get(body.thread_id)
        if files:
            payload["files"] = files
        try:
            async for mode, chunk in get_agent().astream(
                payload,
                thread_config(body.thread_id),
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    message, metadata = chunk
                    msg_type = getattr(message, "type", "")
                    if msg_type == "tool":
                        tool_name = getattr(message, "name", None)
                        collected_assets.extend(
                            _assets_from_tool_content(
                                _message_text(getattr(message, "content", ""))
                            )
                        )
                        if tool_name:
                            yield f"data: {json.dumps({'type': 'tool', 'name': tool_name})}\n\n"
                        continue
                    if metadata.get("langgraph_node") in {"tools"}:
                        continue
                    delta = _message_text(getattr(message, "content", ""))
                    if delta:
                        final_text += delta
                        yield f"data: {json.dumps({'type': 'token', 'text': delta})}\n\n"
                elif mode == "updates" and isinstance(chunk, dict):
                    for node_update in chunk.values():
                        if not isinstance(node_update, dict):
                            continue
                        for msg in node_update.get("messages") or []:
                            if getattr(msg, "type", None) != "tool":
                                continue
                            collected_assets.extend(
                                _assets_from_tool_content(
                                    _message_text(getattr(msg, "content", ""))
                                )
                            )
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
            return

        unique_assets = list(dict.fromkeys(collected_assets))
        yield f"data: {json.dumps({'type': 'done', 'message': final_text, 'assets': unique_assets})}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
