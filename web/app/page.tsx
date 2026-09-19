"use client";

import { FormEvent, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

type ChatItem = {
  id: string;
  role: "user" | "assistant" | "tool";
  text: string;
};

function newThreadId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `thread-${Date.now()}`;
}

function isVideo(url: string) {
  return /\.(mp4|webm|mov)(\?|$)/i.test(url);
}

export default function Page() {
  const [threadId] = useState(newThreadId);
  const [companyUrl, setCompanyUrl] = useState("");
  const [message, setMessage] = useState(
    "Research this company and write a campaign brief.",
  );
  const [items, setItems] = useState<ChatItem[]>([]);
  const [assets, setAssets] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [uploadNote, setUploadNote] = useState("");

  const canSend = useMemo(() => message.trim().length > 0 && !busy, [message, busy]);

  async function uploadPdf(file: File) {
    const body = new FormData();
    body.append("thread_id", threadId);
    body.append("file", file);
    const response = await fetch(`${API}/upload`, { method: "POST", body });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const payload = (await response.json()) as { path: string };
    setUploadNote(`Attached ${payload.path}`);
    setItems((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "tool",
        text: `PDF stored at ${payload.path}. Ask the agent to read it.`,
      },
    ]);
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!canSend) return;
    const text = message.trim();
    setMessage("");
    setBusy(true);
    const assistantId = crypto.randomUUID();
    setItems((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", text },
      { id: assistantId, role: "assistant", text: "" },
    ]);

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          message: text,
          company_url: companyUrl || null,
        }),
      });
      if (!response.ok || !response.body) {
        throw new Error(await response.text());
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.split("\n").find((row) => row.startsWith("data: "));
          if (!line) continue;
          const eventPayload = JSON.parse(line.slice(6)) as {
            type: string;
            text?: string;
            name?: string;
            message?: string;
            assets?: string[];
            detail?: string;
          };
          if (eventPayload.type === "token" && eventPayload.text) {
            setItems((prev) =>
              prev.map((item) =>
                item.id === assistantId
                  ? { ...item, text: item.text + eventPayload.text }
                  : item,
              ),
            );
          } else if (eventPayload.type === "tool" && eventPayload.name) {
            setItems((prev) => [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: "tool",
                text: `Using ${eventPayload.name}`,
              },
            ]);
          } else if (eventPayload.type === "done") {
            if (eventPayload.assets?.length) {
              setAssets((prev) => [...prev, ...eventPayload.assets!]);
            }
            if (eventPayload.message) {
              setItems((prev) =>
                prev.map((item) =>
                  item.id === assistantId && !item.text
                    ? { ...item, text: eventPayload.message ?? "" }
                    : item,
                ),
              );
            }
          } else if (eventPayload.type === "error") {
            throw new Error(eventPayload.detail || "Agent error");
          }
        }
      }
    } catch (error) {
      setItems((prev) =>
        prev.map((item) =>
          item.id === assistantId
            ? {
                ...item,
                text: item.text || `Could not reach the agent: ${String(error)}`,
              }
            : item,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <h1>Campaign workspace</h1>
        <p>
          Paste a company site, attach PDFs, then chat with the research agent.
          Assets stay on the server until you ask it to generate.
        </p>
      </header>

      <section className="brief">
        <label>
          Company website
          <input
            type="url"
            placeholder="https://example.com"
            value={companyUrl}
            onChange={(event) => setCompanyUrl(event.target.value)}
          />
        </label>
        <div className="actions">
          <label>
            PDF
            <input
              type="file"
              accept="application/pdf"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  void uploadPdf(file).catch((err) =>
                    setUploadNote(String(err)),
                  );
                }
              }}
            />
          </label>
        </div>
        {uploadNote ? <p className="empty">{uploadNote}</p> : null}
      </section>

      <section className="workspace">
        <div className="card">
          <h2>Agent</h2>
          <div className="messages">
            {items.length === 0 ? (
              <p className="empty">No messages yet. Send a brief to start research.</p>
            ) : (
              items.map((item) => (
                <div key={item.id} className={`bubble ${item.role}`}>
                  {item.text || (busy ? "…" : "")}
                </div>
              ))
            )}
          </div>
          <form className="composer" onSubmit={send}>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask for a brief, then request a hero image or video."
            />
            <button type="submit" disabled={!canSend}>
              {busy ? "Working" : "Send"}
            </button>
          </form>
        </div>
        <aside className="card">
          <h2>Assets</h2>
          <div className="assets">
            {assets.length === 0 ? (
              <p className="empty">Generated images and video will land here.</p>
            ) : (
              assets.map((url) =>
                isVideo(url) ? (
                  <video key={url} src={url} controls />
                ) : (
                  <img key={url} src={url} alt="Generated asset" />
                ),
              )
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
