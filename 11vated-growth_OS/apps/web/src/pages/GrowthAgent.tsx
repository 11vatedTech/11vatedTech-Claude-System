import { useEffect, useRef, useState } from "react";
import { api } from "../api";

interface AgentReply {
  intent: string;
  reply: string;
  product_id: string | null;
  campaign_id: string | null;
  needs_clarification: boolean;
  actions: { action: string; [k: string]: unknown }[];
}

interface Msg {
  role: "user" | "agent";
  text: string;
  intent?: string;
  productId?: string | null;
  campaignId?: string | null;
}

export function GrowthAgent() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<{ products: { id: string; name: string }[] }>("/products")
      .then((r) => {
        if (r.products.length === 0) {
          setMessages([
            {
              role: "agent",
              text: "**Ready for first product intake.** Describe what you built — e.g. “I built a platform that turns short stories into cinematic full-screen experiences. Add it as a product and help me understand how we can sell it.”",
            },
          ]);
        } else {
          setMessages([
            {
              role: "agent",
              text: `You have ${r.products.length} product(s) in the Canon. Tell me what you want to do: “Market this”, “Change the pricing”, “Who should buy this?”, or describe something new.`,
            },
          ]);
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await api<AgentReply>("/agent/message", {
        method: "POST",
        body: JSON.stringify({ message: text }),
      });
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: r.reply,
          intent: r.intent,
          productId: r.product_id,
          campaignId: r.campaign_id,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "agent", text: `Error: ${e instanceof Error ? e.message : "failed"}` },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const chip = (label: string) => (
    <button
      key={label}
      className="ghost"
      style={{ marginRight: 6, fontSize: 12 }}
      onClick={() => setInput(label)}
    >
      {label}
    </button>
  );

  return (
    <div className="page">
      <h1>Growth Agent</h1>
      <p className="muted">
        Natural-language commercial command, driven by local AI. Software
        governs; the model reasons. Unknown stays unknown.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="card" style={{ minHeight: 320, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "4px 8px" }}>
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                margin: "10px 0",
                textAlign: m.role === "user" ? "right" : "left",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  maxWidth: "85%",
                  padding: "8px 12px",
                  borderRadius: 10,
                  whiteSpace: "pre-wrap",
                  background: m.role === "user" ? "#1e3a8a" : "#111",
                  color: "#fff",
                  border: m.role === "agent" ? "1px solid #333" : "none",
                }}
              >
                {m.text}
                {m.productId && (
                  <div style={{ fontSize: 11, opacity: 0.7, marginTop: 6 }}>
                    → product {m.productId.slice(0, 8)}
                    {m.campaignId ? ` · campaign ${m.campaignId.slice(0, 8)}` : ""}
                  </div>
                )}
              </span>
            </div>
          ))}
          {busy && <div className="muted" style={{ padding: 8 }}>Thinking…</div>}
          <div ref={bottomRef} />
        </div>

        <div style={{ display: "flex", gap: 8, borderTop: "1px solid #222", paddingTop: 10 }}>
          <input
            style={{ flex: 1 }}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Tell GrowthOS what you built, or what to do next…"
          />
          <button className="primary" onClick={send} disabled={busy}>
            Send
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        {chip("Market this")}
        {chip("Who should buy this?")}
        {chip("Change the pricing")}
        {chip("Find partners")}
        {chip("What is the biggest weakness?")}
        {chip("Could we license this?")}
      </div>
    </div>
  );
}
